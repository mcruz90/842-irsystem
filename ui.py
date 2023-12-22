import subprocess
from invert import load_raw_docs_file
import json

# Retieve all the docs with their title author and docID
def retrieve_doc(doc_id, raw_docs):
    
    raw_doc = raw_docs[doc_id]

    results = []

    title = None
    author = None

    lines = raw_doc.split('\n')

    # Set initial flag for the 'A' (i.e. Authors) section in text
    in_a_section = False

    # Iterate through the lines to extract only the title and the author's name 
    for i, line in enumerate(lines):
        if line.startswith('.T'):
            # The title is on the next line
            title = lines[i + 1].strip()
            in_a_section = False
        elif line.startswith('.A'):
            in_a_section = True
            # The Author's name is on the next line
            author = lines[i + 1].strip()

    result = {
        'Document ID': doc_id,
        'Title': title,
        'Author': author,
    }

    results.append(result)

    return results

def main():

    while True:

        argument_value = input("Please enter query: ")

        if argument_value == "ZZEND":
            print("Goodbye.")
            break

        stemming_val = input("Do you want to enable stemming? (Yes/No):\n")

        if stemming_val == "ZZEND":
            print("Goodbye.")
            break

        elif argument_value == "" or stemming_val == "":
            print("Query/Stemming cannot be blank!")
            
        else:
            
            result = subprocess.run(['C:/Users/maycr/anaconda3/python.exe', 'search.py', argument_value, stemming_val], stdout=subprocess.PIPE, text=True)
            
            # Check if the command executed successfully
            if result.returncode == 0:
                try:
                    lines = result.stdout.strip().split('\n')

                    if len(lines) <= 1:
                        print("No results found!")
                        
                    else:
                        retrieved_doc_ids = [int(line.split(': ')[0]) for line in lines]

                        raw_docs = load_raw_docs_file('cacm.tar')

                        doc_results = []

                        for id in retrieved_doc_ids:
                            doc_results.append(retrieve_doc(str(id), raw_docs))

                        for rank, item in enumerate(doc_results, start=1):
                            document = item[0]
                            doc_id = document['Document ID']
                            title = document['Title']
                            author = document['Author'] if document['Author'] is not None else "N/A"
                            
                            print(f'Rank: {rank}')
                            print(f'Document ID: {doc_id}')
                            print(f'Title: {title}')
                            print(f'Author: {author}')
                            print('\n')

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
            else:
                print(f"Command failed with return code {result.returncode}")

if __name__ == "__main__":
    main()