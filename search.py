from nltk.stem import PorterStemmer
import sys
import math
import numpy as np
import re
import json
import tarfile

def load_raw_docs_file(tar_input):
    target_extension = '.all'
    documents = {}
    current_doc_id = None
    current_doc_content = []
    skip_content = False

    for member in tar_input.getmembers():
        if member.isfile() and member.name.endswith(target_extension):
            with tar_input.extractfile(member) as file:
                # Read and decode the file in larger chunks to lower # of calls made
                chunk_size = 1024
                decoded_chunk = ""

                for chunk in iter(lambda: file.read(chunk_size), b''):
                    decoded_chunk += chunk.decode('utf-8')
                    lines = decoded_chunk.split('\n')
                    decoded_chunk = lines.pop()

                    for line in lines:
                        # Get the first two chars of the line to check the section labels
                        section_label = line[:2]

                        if section_label == ".I":
                            if current_doc_id is not None:
                                documents[current_doc_id] = '\n'.join(current_doc_content)
                            current_doc_id = line.split()[-1]
                            current_doc_content = []
                            skip_content = False
                        elif section_label in {".N", ".X"}:
                            skip_content = True
                        elif not skip_content:
                            current_doc_content.append(line)

                if decoded_chunk:
                    lines = decoded_chunk.split('\n')
                    for line in lines:
                        section_label = line[:2]
                        if section_label == ".I":
                            if current_doc_id is not None:
                                documents[current_doc_id] = '\n'.join(current_doc_content)
                            current_doc_id = line.split()[-1]
                            current_doc_content = []
                            skip_content = False
                        elif section_label in {".N", ".X"}:
                            skip_content = True
                        elif not skip_content:
                            current_doc_content.append(line)

    if current_doc_id is not None:
        documents[current_doc_id] = '\n'.join(current_doc_content)

    return documents


# Confirms if user-provided term exists in the input terms_dict.json file
def term_found(user_input, terms_data):    
    if user_input in terms_data:
        return True
    else:
        return False
    
# Retrieves the index in postings using the user_term as the key
def get_doc_ids(term_exists, user_input, terms_data):
    if term_exists:
        return list(terms_data.keys()).index(user_input)
    
# Called when a search term is found in the documents; returns the postings of that term
def search_postings(term_index, postings_data):    
    return postings_data[term_index]

# Returns list of retrieved docs that have that them
def retrieve_docs(term, postings, raw_docs):
    results = []

    for doc_id, content in postings.items():
        positions = content['positions']
        term_frequency = content['term frequency']
        doc_content = raw_docs[doc_id]

        # Initialize variables that store the document title, author, and its terms
        title = None
        author = None

        # Split doc_content into lines
        lines = doc_content.split('\n')

        # Set initial flag for the 'A' (i.e. Authors) section in text
        in_a_section = False

        # Get the first position that the term occurs in from the list of positions in the term positions dictionary
        term_position = positions

        # Iterate through the lines to extract only the title and the author's name 
        for i, line in enumerate(lines):
            # Check the first two characters of the line for section labels
            section_label = line[:2]

            if section_label == '.T':
                # The title is on the next line
                title = lines[i + 1]
                for char in reversed(title):
                    if not char.isspace():
                        title = title[:title.index(char) + 1]
                        break
                in_a_section = False
            elif section_label == '.A':
                in_a_section = True
                # The Author's name is on the next line
                author = lines[i + 1]
                for char in reversed(author):
                    if not char.isspace():
                        author = author[:author.index(char) + 1]
                        break

        result = {
            'Term': term,
            'Document ID': doc_id,
            'Title': title,
            'Author': author,
            'Positions': positions,
            'Term Frequency': term_frequency
        }

        results.append(result)

    return results



def term_stemming(query_term, isStemming):

    with open('stopwords.txt', 'r') as stopword_file:
                stop_words = set(stopword_file.read().splitlines())

    pattern = "[^0-9a-zA-Z\s]+"
    tokened_query = query_term.lower().split()

    alphanum_terms = [re.sub(pattern, "", c).strip() for c in tokened_query]
    
    if isStemming == 'Yes':
        stemmer = PorterStemmer()
        alphanum_terms = [stemmer.stem(word) for word in alphanum_terms if word not in stop_words and word != ""]
    
    if len(alphanum_terms) == 0:
        return ""
    else:
        return alphanum_terms[0]

def get_df(term_exists, user_input, terms_data):
    if term_exists:
        return terms_data.get(user_input)

def main():

        if len(sys.argv) != 3:
            print(f"No input query received!\nUsage: search.py <query> (in double quotes) <Yes/No> ")
            
        else:
            terms_file = 'terms_dict.json'
            postings_file = 'postings_dict.json'

            with open(terms_file, 'r') as terms_file:
                terms_data = json.load(terms_file)

            with open(postings_file, 'r') as postings_file:
                postings_data = json.load(postings_file)

            with tarfile.open('cacm.tar', 'r') as tar:
                docs_tar_file = load_raw_docs_file(tar)
                
            user_string = sys.argv[1]
            user_stemming = sys.argv[2]
            user_query = user_string.split()
            
            doc_data = []
            
            query_terms = []
            
            N = 3204
            term_df = None
            term_idf = None
            
            for char in user_query:
                processed_term = term_stemming(char, user_stemming)
                term_exists = term_found(processed_term, terms_data)
                    
                if term_exists:
                    
                    query_terms.append(processed_term)
                    idx = get_doc_ids(term_exists, processed_term, terms_data)
                    postings_results = search_postings(str(idx), postings_data)
                    docs = retrieve_docs(processed_term, postings_results, docs_tar_file)
                    
                    term_df = get_df(term_exists, processed_term, terms_data)
                    term_idf = math.log((N/term_df),10)

                    for doc in docs:  
                        doc_data.append({doc['Document ID']: [doc['Term'], doc['Term Frequency']*term_idf]})
            
            combined_data = {}

            for item in doc_data:

                # Get the single key-value pair
                key, values = item.popitem()  

                if key in combined_data:
                    # Append the values to the existing key
                    combined_data[key].append(values)
                else:
                    # Create a new entry in the combined_data dictionary
                    combined_data[key] = [values]

            # Convert the combined_data dictionary back to a list of dictionaries
            combined_data_list = [{k: v} for k, v in combined_data.items()]
            
            # Only get unique terms from user entered query
            unique_terms = sorted(set(query_terms))
                
            # Initialize a vector of zeros for each document
            vector_length = len(unique_terms)
            zero_vector = [0.0] * vector_length

            # Create a dictionary to store the document vectors
            document_vectors = {}
            
            for item in combined_data_list:
                for key, value in item.items():
                    document_vector = zero_vector.copy()
                    for subitem in value:
                        term, weight = subitem
                        index = unique_terms.index(term)
                        document_vector[index] = weight
                    document_vectors[key] = document_vector
                    
            # Create a query vector
            sorted_query = sorted(query_terms)
            
            # Initialize a dictionary to store string counts
            query_counts = {}

            # Iterate through the list and count occurrences
            for string in sorted_query:
                if string in query_counts:
                    # If the string is already in the dictionary, increment its count
                    query_counts[string] += 1
                else:
                    # If the string is not in the dictionary, add it with a count of 1
                    query_counts[string] = 1
                    
            query_vector_raw = query_counts.values()
            query_vector = [x*term_idf for x in query_vector_raw]
            query_q = math.sqrt(sum(i**2 for i in query_vector))
            
            # Cosine similarity for query and document
            sim_qd = {}

            # Term Weight threshold
            weight_threshold = 2.75

            # Initialize a dictionary to store matching documents
            threshold_documents = {}

            for doc_id, vector in (document_vectors.items()):
                matching = False

                for weight in vector:
                    if weight > weight_threshold:
                        matching = True
                        break 

                if matching:
                    threshold_documents[doc_id] = vector

            threshold_documents = dict(sorted(threshold_documents.items(), key=lambda item: (item[1]), reverse=True))

            # Calculate the dot product of the query vector with each document vector
            for doc_id, doc_vector in threshold_documents.items():

                # Calculate the cosine similarity
                cos_sim = sum(q * d for q, d in zip(query_vector, doc_vector))/(query_q*math.sqrt(sum(i**2 for i in doc_vector)))

                # Store the result in the dot_products dictionary
                sim_qd[doc_id] = cos_sim
                
            sorted_sim_qd = dict(sorted(sim_qd.items(), key=lambda item: item[1], reverse=True))
            
            topk_docs = {k: v for k, v in list(sorted_sim_qd.items())[:20]}

            for id, score in topk_docs.items():
                print(f"{id}: {score}")

            output_json = json.dumps(topk_docs)
            
            tar.close()

if __name__ == "__main__":
    main()