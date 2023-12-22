import subprocess
import tarfile
import re
import multiprocessing
import sys
from functools import partial

# Reads and parses query.text file and returns a dictionary of queries
def parse_queries(tar_file):
    file_name = 'query.text'

    if file_name in tar_file.getnames():
        file_contents = tar_file.extractfile(file_name).read().decode('utf-8')
        lines = file_contents.splitlines()

        content_dict = {}
        current_key = None 
        is_reading_content = False  

        for i, line in enumerate(lines):
            if line.startswith('.I'):
                current_key = int(line.split()[1])
                content_dict[current_key] = '' 
                is_reading_content = False
            elif line.startswith('.W'):
                if current_key is not None:
                    is_reading_content = True
                    content_dict[current_key] += line.lstrip('.W').strip()
            elif is_reading_content:
                if line.startswith('.A') or line.startswith('.N'):
                    is_reading_content = False
                else:
                    content_dict[current_key] += ' ' + line.strip()
        
    return content_dict

# Reads and parses query.text file and returns a dictionary of queries
def parse_qrel(tar_file):
    file_name = 'qrels.text'

    if file_name in tar_file.getnames():
        file_contents = tar_file.extractfile(file_name).read().decode('utf-8')
    
    relevant_docs = {}

    for line in file_contents.split('\n'):
        if line.strip():
            parts = line.split()
            query_id, doc_id = parts[0], int(parts[1]) 
            if query_id in relevant_docs:
                relevant_docs[query_id].append(doc_id)
            else:
                relevant_docs[query_id] = [doc_id]

    return relevant_docs

# Return query string
def get_query(idx, queries_dict):
    return queries_dict[idx]

# Run search.py and return top-k results for that query
def query_search(query, user_stemming):
    result = subprocess.run(['C:/Users/maycr/anaconda3/python.exe', 'search.py', query, user_stemming], stdout=subprocess.PIPE, text=True)
    return result

# return the precision@k
def calculate_precision_at_k(retrieved, relevant_docs):
    precision_at_k = []
    num_relevant_found = 0

    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant_docs:
            num_relevant_found += 1
            precision_at_k.append(num_relevant_found / (i + 1))

    if not precision_at_k:
        return 0.0
    return sum(precision_at_k) / len(relevant_docs)

# Returns that average precision of a query, comparing relevant docs vs retrieved docs
def average_precision(query_id, relevant_docs, retrieved_docs):
    retrieved = retrieved_docs.get(query_id, [])
    return calculate_precision_at_k(retrieved, relevant_docs)

# Return MAP for the whole I-R system
def mean_average_precision(relevant_docs, retrieved_docs):
    total_ap = 0.0
    num_queries = len(relevant_docs)

    for query_id, relevant_doc in relevant_docs.items():
        total_ap += average_precision(query_id, relevant_doc, retrieved_docs)

    return total_ap / num_queries

# Returns R-Precision Value of a query against the retrieved docs and relevant docs
def r_precision(query_id, relevant_docs, retrieved_docs):
    retrieved = retrieved_docs.get(query_id, [])
    num_relevant = len(relevant_docs)
    num_relevant_found = 0

    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant_docs:
            num_relevant_found += 1

    return num_relevant_found / num_relevant

def calculate_r_precision(relevant_docs, retrieved_docs):
    r_precision_values = []

    for query_id, relevant_doc in relevant_docs.items():
        r_precision_values.append(r_precision(query_id, relevant_doc, retrieved_docs))

    return r_precision_values

# Function to extract and process document IDs and scores
def extract_doc_scores(output):
    matches = re.findall(r'(\d+): ([\d.]+)', output)
    doc_scores = {doc_id: float(score) for doc_id, score in matches}

    return doc_scores

# Return dict of scores run on the IR system for each query
def get_ir_results(queries, results):
    ir_results = {}

    # Extract and process the document IDs and scores from each result
    for result, (_, query_id) in zip(results, queries.items()):
        doc_scores = extract_doc_scores(result.stdout)
        ir_results[query_id] = doc_scores

    return ir_results

# Returns key-value pairs of doc_id-scores
def get_retrieved_docs(ir_results):
    retrieved_docs = {}
    for i, (key, value) in enumerate(ir_results.items()):
        if i < 1: 
            group = 1
        else:
            group = (i // 1) + 1
        retrieved_docs[group] = value

    polished_retrieved = {}
    for qid, results in retrieved_docs.items():
        polished_retrieved[qid] = [int(key) for key in results.keys()]

    return polished_retrieved

def get_relevant_doc_ids(extracted_qrels):

    relevant_docs = {int(query_id): docs for query_id, docs in extracted_qrels.items()}

    return relevant_docs

def main():

    user_stemming = sys.argv[1]
    with tarfile.open('cacm.tar', 'r') as tar:
        queries = parse_queries(tar)
        extracted_qrel = parse_qrel(tar)

    print("Running evaluations...")

    # Using multiprocessing pool to decrease processing time
    # Uses 4 less than total CPU available to prevent using too many 
    pool = multiprocessing.Pool(processes=(multiprocessing.cpu_count() - 4))
    partial_query_search = partial(query_search, user_stemming=user_stemming)
    results = pool.map(partial_query_search, queries.values())
    pool.close()

    ###### Evaluations ####### 

    # Retrieved Docs
    ir_results = get_ir_results(queries, results)
    retrieved_docs = get_retrieved_docs(ir_results)
    
    # Relevant Docs
    relevant_doc_ids = get_relevant_doc_ids(extracted_qrel)

    # Calculate MAP, R-Precision, and R-Precision values
    map_score = mean_average_precision(relevant_doc_ids, retrieved_docs)
    r_precision_values = calculate_r_precision(relevant_doc_ids, retrieved_docs)

    # Print the results
    print("Mean Average Precision (MAP):", map_score)

    relevant_docs_keys = []
    for key, _ in relevant_doc_ids.items():
        relevant_docs_keys.append(key)

    print("R-Precision values:")
    for qid, rp_value in zip(relevant_docs_keys, r_precision_values):
        print(f"Query {qid}, R-Precision: {rp_value}")

    tar.close()

if __name__ == "__main__":
    main()