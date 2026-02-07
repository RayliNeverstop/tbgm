import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

class DriveManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DriveManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized: return
        self.initialized = True
        self.service = None
        self.creds = None
        
        # Folder Name in Google Drive to store saves
        self.FOLDER_NAME = "TBGM_Saves"
        self.folder_id = None

    def set_credentials(self, token: str):
        """
        Initialize Drive Service using the OAuth token received from Flet login.
        Works on Mobile via Flet's Native Auth.
        """
        try:
            # We assume 'token' is the access_token. 
            self.creds = Credentials(token=token)
            self.service = build('drive', 'v3', credentials=self.creds)
            print("DEBUG: Google Drive Service Initialized via Token")
            
            # Check/Create Folder
            self._ensure_folder()
            return True, "Login Success"
        except Exception as e:
            print(f"Error init Drive: {e}")
            return False, str(e)

    def _ensure_folder(self):
        """Check if TBGM_Saves folder exists, if not create it."""
        if not self.service: return
        
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and name='{self.FOLDER_NAME}' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if not items:
                # Create Folder
                file_metadata = {
                    'name': self.FOLDER_NAME,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                self.folder_id = file.get('id')
                print(f"DEBUG: Created Drive Folder {self.FOLDER_NAME} ({self.folder_id})")
            else:
                self.folder_id = items[0]['id']
                print(f"DEBUG: Found Drive Folder {self.FOLDER_NAME} ({self.folder_id})")
                
        except Exception as e:
            print(f"Error ensuring folder: {e}")

    def upload_save(self, local_path: str, filename: str):
        """Uploads (or updates) an encrypted save file to Drive."""
        if not self.service or not self.folder_id:
            return False, "Not Connected"
            
        try:
            # 1. Check if file exists to decide Update vs Create
            query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            file_metadata = {'name': filename}
            media = MediaFileUpload(local_path, mimetype='application/octet-stream', resumable=True)
            
            if items:
                # Update
                file_id = items[0]['id']
                updated_file = self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                print(f"DEBUG: Updated file on Drive ({updated_file.get('id')})")
            else:
                # Create
                file_metadata['parents'] = [self.folder_id]
                created_file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                print(f"DEBUG: Created file on Drive ({created_file.get('id')})")
                
            return True, "Upload Success"
            
        except Exception as e:
            print(f"Error uploading: {e}")
            return False, str(e)

    def download_save(self, filename: str, target_path: str):
        """Downloads a save file from Drive to local path."""
        if not self.service or not self.folder_id:
            return False, "Not Connected"
            
        try:
            # 1. Find File
            query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if not items:
                return False, "Cloud File Not Found"
                
            file_id = items[0]['id']
            
            # 2. Download
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            # Write to disk
            with open(target_path, "wb") as f:
                f.write(fh.getvalue())
                
            return True, "Download Success"
            
        except Exception as e:
            print(f"Error downloading: {e}")
            return False, str(e)
            
    def list_cloud_saves(self):
        """Lists available saves in the Cloud Folder."""
        if not self.service or not self.folder_id:
            return []
            
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields="nextPageToken, files(id, name, modifiedTime)").execute()
            return results.get('files', [])
        except Exception as e:
            print(f"Error listing: {e}")
            return []
