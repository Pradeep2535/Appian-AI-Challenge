from pymongo.mongo_client import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings,GoogleGenerativeAI
from bson import ObjectId
import streamlit as st

from constants import GOOGLE_API_KEY, MONGODB_URI

class MongoDB:
    def __init__(self):
        uri = MONGODB_URI


        self.client = MongoClient(uri)
    def generate_embeddings(self,texts):
        
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = GoogleGenerativeAIEmbeddings(model='models/embedding-001',google_api_key=GOOGLE_API_KEY)
        embeddings = [gemini_model.embed_documents([text])[0] for text in texts]  # Ensure you pass a list to the model
        
    
        
        
        return np.array(embeddings)
 
    def find_most_similar_vector(self, query_vector: np.ndarray, vectors: np.ndarray):
        """
        Compute cosine similarity between the query vector and a list of vectors, 
        and return the best-matching vector along with its similarity score and index.

        Args:
            query_vector (np.ndarray): The query vector (1D or 2D array).
            vectors (np.ndarray): A 2D array of vectors to compare against.

        Returns:
            tuple: (max_similarity, max_index, best_vector) where
                - max_similarity is the highest cosine similarity value.
                - max_index is the index of the best-matching vector.
                - best_vector is the vector with the highest similarity.
        """
    # Reshape query_vector to 2D (if necessary) for compatibility
        query_vector = query_vector.reshape(1, -1)

    # Compute cosine similarities
        similarities = cosine_similarity(query_vector, vectors).flatten()
        # print(similarities)
    # Find the index of the maximum similarity
        max_index = np.argmax(similarities)
        max_similarity = similarities[max_index]

    # Get the most similar vector
        best_vector = vectors[max_index]
        
        return max_similarity, max_index

    
    def person_id(self,name,dob,address):
        name=name
        person_obj = None 

        db = self.client['Accounts']
        collection = db['accounts_details']
        # update_data = { 'name': 'Anita Sharma', 'DOB': '15/04/1992', 'account_number': '2345678901', 'account_type': 'Savings', 'balance': 40000.0, 'contact_number': '9876543211', 'aadhar_number': '2345-6789-0123', 'pan_number': 'BCDEF1234G', 'email': 'anita.sharma@example.com', 'address': '456 Avenue, Chennai, India'}
        # collection.update_one({'_id':ObjectId('676a987c5ca79ef0336e6df3')}, {'$set' :  update_data})
        if name:
            results_for_matching_name = collection.find({"name":name})
            results_list = [document for document in results_for_matching_name]
            # print(results_list)
            if len(results_list) < 1:
                #new customer (in case of documents like application form)

                person_obj = collection.insert_one({'name':name,"dob":dob,"address":address})
                
                                

                person_obj = collection.find_one({'name':name})
                

            elif len(results_list) > 1:

                #more than one customer with same name
                if dob:
                    results_for_matching_name_and_dob = [ document for document in results_list if str(document['DOB'])==str(dob)]

                    if len(results_for_matching_name_and_dob) == 1:
                        person_obj = results_for_matching_name_and_dob[0]
                    elif len(results_for_matching_name_and_dob) > 1:
                        address_list = [document['address'] for document in results_for_matching_name_and_dob]
                        
                        vector_list = self.generate_embeddings(address_list)
                        query_vector = self.generate_embeddings([address])[0]
                
                        max_similarity, max_index = self.find_most_similar_vector(query_vector, vector_list)
                        if(max_similarity)>=0.9 :
                            person_obj = [document for document in results_for_matching_name_and_dob if document['address']==address_list[max_index]]
                        else:
                            print('Passed to review')
                    elif len(results_for_matching_name_and_dob) < 1:
                        print('passed to review')

                elif address:
                    #no dob found in document so trying to match address
                    address_list = [document['address'] for document in results_list]
                    
                    vector_list = self.generate_embeddings(texts = address_list)
                    query_vector = self.generate_embeddings([address])[0]
                   
                    max_similarity, max_index = self.find_most_similar_vector(query_vector, vector_list)

                    print(max_similarity,max_index)
                    if(max_similarity)>=0.9 :
                        person_obj = [document for document in results_list if document['address']==address_list[max_index]]
                    else:
                        print('Passed to review')
                else:
                    # no dob and address for people more than 1 with same name, then passed to review ( very rare )
                    print('passed to review')
            elif len(results_list) == 1:

                #only one customer with that name
                person_obj = results_list[0]

        return person_obj
    
    def insert_document(self,account,file_document,document_type):
        db = self.client['Accounts']
        collection = db['accounts_details']
        insert_done = collection.update_one({'_id':account['_id']}, {
        '$set': {'name': account['name'].lower()},          # Update operation for 'name'
        '$push': {'uploaded_documents': file_document}  # Push operation for 'uploaded_documents'
        })
        db1 = self.client['AccountHolderDocuments']
        collection1 = db1['accounts']
        print(account)
        insert_done1 = collection1.update_one({'_id':account['_id']},{
        '$set': {'name': account['name'].lower()},          # Update operation for 'name'
        '$push': {'uploaded_documents': file_document}  # Push operation for 'uploaded_documents'
        },upsert=True)
        
        db2 = self.client['Documents']
        collection2 = db2[document_type]
        file_document['name'] = account['name'].lower()
        insert_done2 = collection2.insert_one(file_document)

        return insert_done and insert_done1 and insert_done2



# obj = MongoDB()
# response  = obj.upload_documents(name='Sharma',dob=None,address=' Delhi, India')

# print(response)

       



        

# name
# "Anita Sharma"
# DOB
# "15/03/1992"
# account_number
# "2345678901"
# account_type
# "Savings"
# balance
# 40000
# contact_number
# "9876543211"
# aadhar_number
# "2345-6789-0123"
# pan_number
# "BCDEF1234G"
# email
# "anita.sharma@example.com"
# address
# "456 Avenue, Delhi, India"