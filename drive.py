import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tempfile import NamedTemporaryFile
from constants import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN
# Replace these with your credentials and settings
CLIENT_ID = CLIENT_ID
CLIENT_SECRET = CLIENT_SECRET
REFRESH_TOKEN = REFRESH_TOKEN

# Initialize credentials
creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    token_uri='https://oauth2.googleapis.com/token'
)

# Build the Drive API service
drive_service = build('drive', 'v3', credentials=creds)

def get_folder_id_by_name(folder_name):
    """
    Checks if a folder with the given name exists in Google Drive and returns its ID.
    """
    try:
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        response = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get('files', [])
        if files:
            return files[0]['id']
        return None
    except Exception as e:
        st.error(f"Error checking folder: {str(e)}")
        return None

def create_folder(folder_name):
    """
    Creates a folder in Google Drive and returns its ID.
    """
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    try:
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']
    except Exception as e:
        st.error(f"Error creating folder: {str(e)}")
        return None

def create_or_get_folder(folder_name):
    """
    Ensures a folder exists in Google Drive. If it doesn't exist, creates it.
    """
    folder_id = get_folder_id_by_name(folder_name)
    if folder_id:
        return folder_id
    return create_folder(folder_name)

def upload_file_to_folder(file, file_name, folder_id):
    """
    Uploads a file to a specific folder in Google Drive.
    """
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    try:
        media = MediaFileUpload(file.name, mimetype='application/octet-stream')
        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
    except Exception as e:
        return False




def get_folder_id_by_name_in_parent(folder_name, parent_id):
   
    try:
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        response = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get('files', [])
        if files:
            return files[0]['id']
        return None
    except Exception as e:
        print(f"Error checking folder in parent: {str(e)}")
        return None

def create_nested_folders(folder_name, parent_id):
    
    current_parent_id = parent_id
    
    
       
    folder_id = get_folder_id_by_name_in_parent(folder_name, current_parent_id)
        
    if not folder_id:
            # Folder does not exist, create it
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',                
            'parents': [current_parent_id] if current_parent_id else []
            }
        try:
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder['id']
            print(f"Folder '{folder_name}' created with ID: {folder_id}")
        except Exception as e:
            print(f"Error creating folder '{folder_name}': {str(e)}")
            return None
        else:
            print(f"Folder '{folder_name}' already exists with ID: {folder_id}")

        
        
    current_parent_id = folder_id
    
    return current_parent_id

