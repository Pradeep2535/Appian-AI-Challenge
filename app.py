import streamlit as st
from parameters_extract import analyze_keywords, identify_document
from pinecone_db import MongoDB
from bson.binary import Binary
import os
import mimetypes
from pdf2image import convert_from_bytes
import pytesseract
from pdf2image import convert_from_path,convert_from_bytes
from PIL import Image
import magic
from io import BytesIO
from tempfile import NamedTemporaryFile
from drive import upload_file_to_folder, create_nested_folders, create_or_get_folder

pytesseract.pytesseract.tesseract_cmd = r"C:\\Tesseract\\Tesseract-OCR\\tesseract.exe"

def detect_file_type(uploaded_file):
    
    mime = magic.Magic(mime=True)
    
    file_type = mime.from_buffer(uploaded_file)

    if 'pdf' in file_type:
        return 'pdf'
    elif 'image' in file_type:
        return 'image'
    else:
        return 'unknown'


# --- Text Extraction ---
# def extract_text_with_pymupdf(pdf_path):
#     """
#     Extract text from a PDF using PyMuPDF.
#     """
#     text = ""
#     try:
#         pdf = fitz.open(pdf_path)
#         for page in pdf:
#             text += page.get_text()
#         pdf.close()
#     except Exception as e:
#         print(f"Error extracting text with PyMuPDF: {e}")
#     return text


def extract_text_with_ocr(uploaded_file):
    text = ""
    try:
        # Read the uploaded file into a BytesIO object
        file_bytes = BytesIO(uploaded_file)
        print("------------------")
        print(uploaded_file)
        # Convert PDF to images using the correct Poppler path
        images = convert_from_bytes(file_bytes.getvalue(), poppler_path=r'C:\\Users\\malap\\Downloads\\Release-24.08.0-0\\poppler-24.08.0\\Library\\bin')
        
        # Perform OCR on each image and extract text
        for image in images:
            text += pytesseract.image_to_string(image, lang='eng+hin+tam')  # Adding Tamil language
    except Exception as e:
        print(f"Error performing OCR: {e}")
    return text


# def extract_text_from_pdf(pdf_path):
#     """
#     Extract text from a PDF using PyMuPDF, fallback to OCR.
#     """
#     text = extract_text_with_pymupdf(pdf_path)
#     if not text.strip():
#         print("No text found with PyMuPDF. Using OCR...")
#         text = extract_text_with_ocr(pdf_path)
#     return text


def extract_text_from_image(uploaded_file):
   
    text = ""
    try:
        # Read the uploaded file into a BytesIO object
        image_bytes = BytesIO(uploaded_file)
        
        # Open the image from the BytesIO object
        image = Image.open('aadhar_backside.png')
        
        # Use pytesseract to extract text from the image
        text = pytesseract.image_to_string(image, lang='tam+eng+hin')
    except Exception as e:
        print(f"Error extracting text from image: {e}")
    
    return text


# --- Document Classification ---
def classify_document(text):
    """
    Classify the document as Aadhaar, PAN, or Voter ID based on keywords.
    """
    aadhaar_keywords = ["aadhaar", "uidai"]

    pan_keywords = ["permanent account number", "income tax department"]

    voter_keywords = ["election commission of india", "epic number", "electoral photo identity card"]

    text_lower = text.lower()

    if all(keyword in text_lower for keyword in aadhaar_keywords):
        return "aadhaar"
    elif all(keyword in text_lower for keyword in pan_keywords):
        return "pan"
    elif all(keyword in text_lower for keyword in voter_keywords):
        return "voter"
    else:

        #if not able to identify then using gemini model

        identified_document_type = identify_document(text=text)

        return identified_document_type.lower()

        




file = st.file_uploader('Upload documents',type=['pdf','jpg','jpeg','png'])

if file:
    st.dialog('yes')
    file_read = file.read()
    file.seek(0)
    file_type = detect_file_type(file_read)
    

    extracted_text = ""
    print(file_read,file_type)
    if file_type == 'pdf':
        extracted_text = extract_text_with_ocr(file_read)
    elif file_type == 'image':
        extracted_text = extract_text_from_image(file_read)
    else:
        st.write("Unsupported file type. Please provide a valid PDF or image file.")
        
    
    document_type = classify_document(extracted_text)
    name, dob, address = analyze_keywords(text=extracted_text)
    
    mongo_client = MongoDB()
    account = mongo_client.person_id(name=name,dob=dob,address=address)
    if account is None:
        st.write('Try uploading a different file.')
    else:
        file_type = file.type
        file_name = str(document_type)
        file_data = file.getvalue()
        bson_file_data = Binary(file_data)

        file_document = { 
            
            'file_type' : file_type,
            'file_name' : file_name,
            'file_data' : bson_file_data
            
        }

        print(file_type)
        result = mongo_client.insert_document(account,file_document,document_type)

        if result:
            st.write('Document Uploaded Successfully in DataBase')
        else:
            st.write('Network Error, Try Again to Upload in Database')


        

        if file:

            #Document-wise Heirarchy in Drive

            folder_name1 = "Documents"
        
            internal_folder_name1 = document_type

            folder_id1 = create_or_get_folder(folder_name1)
            nested_folder_id1 = create_nested_folders(internal_folder_name1,folder_id1)

            with NamedTemporaryFile(delete=False) as temp_file1:
                temp_file1.write(file.read())
                temp_file1.flush()
                temp_file1_path = temp_file1.name

            upload_file_to_folder(temp_file1, name, nested_folder_id1)


            #Person-wise Heirarchy in Drive
            
            file.seek(0)

            folder_name2 = "Account_Holders"

            internal_folder_name2 = name

            folder_id2 = create_or_get_folder(folder_name2)
            nested_folder_id2 = create_nested_folders(internal_folder_name2,folder_id2)

            with NamedTemporaryFile(delete=False) as temp_file2:
                temp_file2.write(file.read())
                temp_file2.flush()
                temp_file2_path = temp_file2.name

            upload_file_to_folder(temp_file2, document_type, nested_folder_id2)



        
    


    
# import sys
# import os

# # Add the parent directory to the Python path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


