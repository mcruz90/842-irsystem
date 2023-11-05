import subprocess
import tarfile
import re
import multiprocessing

# Reads and parses query.text file and returns a dictionary of queries
def parse_queries():
    tar_file = tarfile.open('cacm.tar', 'r')
    file_name = 'query.text'

    # Check if the file exists in the archive and processes each line
    if file_name in tar_file.getnames():
        file_contents = tar_file.extractfile(file_name).read().decode('utf-8')
        lines = file_contents.splitlines()

        # Initialize an empty dictionary to store the content
        content_dict = {}
        current_key = None 
        is_reading_content = False  

        # Iterate through each line in file
        for i, line in enumerate(lines):
            if line.startswith('.I'):
                # Get the key from the '.I' line
                current_key = int(line.split()[1])
                content_dict[current_key] = '' 
                is_reading_content = False
            elif line.startswith('.W'):
                # Start appending the lines to the value in the key-value pair
                if current_key is not None:
                    is_reading_content = True
                    # Extract text in the line after '.W'
                    content_dict[current_key] += line.lstrip('.W').strip()
            elif is_reading_content:
                if line.startswith('.A') or line.startswith('.N'):
                    # Stop reading content once in '.A' or '.N' sections
                    is_reading_content = False
                else:
                    # Append the lines to the value associated with the current key
                    content_dict[current_key] += ' ' + line.strip()
        
    tar_file.close()
    return content_dict

def parse_qrel():
    tar_file = tarfile.open('cacm.tar', 'r')
    file_name = 'qrels.text'

    # Check if the file exists in the archive
    if file_name in tar_file.getnames():
        file_contents = tar_file.extractfile(file_name).read().decode('utf-8')
        
    # Create a dictionary to store relevant documents
    relevant_docs = {}

    # Parse the content line by line
    for line in file_contents.split('\n'):
        if line.strip():
            parts = line.split()
            query_id, doc_id = parts[0], int(parts[1]) 
            if query_id in relevant_docs:
                relevant_docs[query_id].append(doc_id)
            else:
                relevant_docs[query_id] = [doc_id]

    tar_file.close()
    return relevant_docs

def get_query(idx, queries_dict):
    return queries_dict[idx]

def query_search(query):
    result = subprocess.run(['C:/Users/maycr/anaconda3/python.exe', 'search.py', query], stdout=subprocess.PIPE, text=True)
    return result

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

def average_precision(query_id, relevant_docs, retrieved_docs):
    retrieved = retrieved_docs.get(query_id, [])
    return calculate_precision_at_k(retrieved, relevant_docs)

def mean_average_precision(ground_truth, retrieved_docs):
    total_ap = 0.0
    num_queries = len(ground_truth)

    for query_id, relevant_docs in ground_truth.items():
        total_ap += average_precision(query_id, relevant_docs, retrieved_docs)

    return total_ap / num_queries

def r_precision(query_id, relevant_docs, retrieved_docs):
    retrieved = retrieved_docs.get(query_id, [])
    num_relevant = len(relevant_docs)
    num_relevant_found = 0

    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant_docs:
            num_relevant_found += 1

    return num_relevant_found / num_relevant

def calculate_r_precision(ground_truth, retrieved_docs):
    r_precision_values = []

    for query_id, relevant_docs in ground_truth.items():
        r_precision_values.append(r_precision(query_id, relevant_docs, retrieved_docs))

    return r_precision_values

# Function to extract and process document IDs and scores
def extract_doc_scores(output):
    matches = re.findall(r'(\d+): ([\d.]+)', output)
    doc_scores = {doc_id: float(score) for doc_id, score in matches}

    return doc_scores

def get_ir_results(queries, results):
    ir_results = {}

    # Extract and process the document IDs and scores from each result
    for result, (query, query_id) in zip(results, queries.items()):
        doc_scores = extract_doc_scores(result.stdout)
        ir_results[query_id] = doc_scores

    return ir_results

def get_retrieved_docs(ir_results):
    retrieved_docs = {}
    for i, (key, value) in enumerate(ir_results.items()):
        if i < 1:  # Specify the number of elements per group
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

    queries = parse_queries()

    print("Running evaluations...")

    # Using multiprocessing pool to decrease processing time
    # Uses 4 less than total CPU available to prevent using too many 
    pool = multiprocessing.Pool(processes=(multiprocessing.cpu_count()-4)) 
    results = pool.map(query_search, queries.values())
    pool.close()

    ###### Evaluations ####### 

    # Retrieved Docs
    ir_results = get_ir_results(queries, results)
    retrieved_docs = get_retrieved_docs(ir_results)
    
    # Relevant Docs
    extracted_qrel = parse_qrel()
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

if __name__ == "__main__":

    main()