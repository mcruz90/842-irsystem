import tarfile
from nltk.stem import PorterStemmer
from collections import defaultdict
import json
import os
import sys
import re
import math

def load_raw_docs_file(input_collection):    
    # Open the .tar file
    tar = tarfile.open(input_collection, 'r')

    # Specifying file extension .all in tar file, which has all the documents
    target_extension = '.all'

    # Initialize documents dictionary and loop counter variables for the current doc ID and its content
    documents = {}
    current_doc_id = None
    current_doc_content = []

    # Loop through the .tar file to look for the CACM.all file and put each document in it into a dict data structure
    for member in tar.getmembers():
        if member.isfile() and member.name.endswith(target_extension):
            with tar.extractfile(member) as file:
                    
                    # Using skip flags to indicate extraction only from sections .I, .T, .W, .B and .A
                    # flags: False means don't skip; True means skip that section
                    skip_content = False

                    for line in file:
                        line = line.decode('utf-8').strip()
                        if line.startswith(".I"):
                            if current_doc_id is not None:
                                documents[current_doc_id] = '\n'.join(current_doc_content)
                                current_doc_content = []
                            # Store the content of the previous document
                            current_doc_id = line.split()[-1]
                            skip_content = False 
                        elif line.startswith(".N"):
                            # Don't want text in .N section
                            skip_content = True  
                        elif line.startswith(".X"):
                            # Don't want text in .X section
                            skip_content = True
                        elif not skip_content:

                            # Add the line to the current document content if not skipping
                            current_doc_content.append(line)

    # Store the very last document that was not part of the loop
    if current_doc_id is not None:
        documents[current_doc_id] = '\n'.join(current_doc_content)

    # Close the .tar file
    tar.close()

    return documents

# If document_stemming == True, open stopwords file and use PorterStemmer
# Else, don't do stemming, just convert to lowercase and split by space and return all terms
def preprocess_and_inverted_index(documents, document_stemming):

    # Initialize an empty in-memory inverted index with the term, the doc ids, positions and term frequency
    inverted_index = defaultdict(dict)

    # Iterate through each document in the input dict of documents and process each term
    for doc_id, content in documents.items():

        # Tokenize the document by turning each term to lowercase and split by whitespace
        pattern = "[^0-9a-zA-Z\s]+"
        terms = content.lower().split()

        alphanum_terms = [re.sub(pattern, "", c).strip() for c in terms]

        # Only execute if user wants stemming
        if document_stemming:
            stemmer = PorterStemmer()

            # Load stop words from the provided text file into a set
            with open('stopwords.txt', 'r') as stopword_file:
                stop_words = set(stopword_file.read().splitlines())

            alphanum_terms = [stemmer.stem(word) for word in alphanum_terms if word not in stop_words and word != ""]

        total_term_count = len(alphanum_terms)
        
        # Get info about the term's position
        term_positions = {}
        for position, term in enumerate(alphanum_terms):
            if term in term_positions:
                term_positions[term].append(position)
            else:
                term_positions[term] = [position]

        # Add the term positions and its term frequency in that doc_id to the inverted index
        for term, positions in term_positions.items():
            inverted_index[term][doc_id] = {'positions': positions, 'term frequency': ((math.log(len(positions),10) + 1))}

    sorted_inverted_index = {term: inverted_index[term] for term in sorted(inverted_index)}
    return sorted_inverted_index

def create_output_files(inverted_index):

    # Separate the terms and postings from the input inverted index
    terms_dict = {}
    postings_dict = {}

    # Copy term and its dict index into terms_dict; copy the postings_info (doc_ids, positions, term_frequencg)
    for i, (term, postings) in enumerate(inverted_index.items()):
        terms_dict[term] = len(inverted_index[term])
        postings_dict[i] = postings

    # Export the dicts as json files
    with open('terms_dict.json', 'w') as terms_file:
        json.dump(terms_dict, terms_file)
    with open('postings_dict.json', 'w') as postings_file:
        json.dump(postings_dict, postings_file)

def main():

    if len(sys.argv) < 2:
        print(f"No collection file found as input!\nUsage: invert.py [collection file]")
    else:
        while True:

            print(f"Hello! This program will create an inverted index from a given set of documents.")

            input_collection = sys.argv[1]

            raw_docs = load_raw_docs_file(input_collection)
            
            user_stemming = input(f"Please confirm if you wish to perform stemming and stop word removals (Enter Yes/No)\n")
            
            if user_stemming == "Yes" or user_stemming == 'yes':
                print(f"Documents pre-processing with stemming...")
                inverted_index = preprocess_and_inverted_index(raw_docs, True)
            elif user_stemming == "No" or user_stemming == 'no':
                print(f"Documents pre-processing without stemming...")
                inverted_index = preprocess_and_inverted_index(raw_docs, False)
            else:
                print(f"Invalid Input! Please only enter Yes or No")
                break

            # Export the inverted index to files
            create_output_files(inverted_index)

            if os.path.exists('terms_dict.json') and os.path.exists('postings_dict.json'):
                print(f"Both files were successfully created!")
            else:
                print(f"Uh oh! There was an error creating both files!")
            break
    
if __name__ == "__main__":
    main()