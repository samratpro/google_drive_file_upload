from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

# Define the scope for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    """
    Authenticate with Google Drive API and return the service object.
    Handles token storage and refresh.
    """
    creds = None
    token_path = 'token.pickle'

    # Check if token.pickle exists and load it
    if os.path.exists(token_path):
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Error loading token.pickle: {e}. Re-authenticating...")
            creds = None

    # Perform reauthentication if credentials are invalid or missing
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}. Re-authenticating...")
                creds = None
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            except FileNotFoundError:
                print("Error: 'credentials.json' not found. Please download it from the Google Cloud Console.")
                return None
            except Exception as e:
                print(f"Error during authentication: {e}")
                return None

        # Save the credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    # Build the service object
    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building Google Drive service: {e}")
        return None

def create_folder(service, folder_name, parent_id):
    """
    Create a new folder in Google Drive under the specified parent folder.
    :param service: Google Drive service object
    :param folder_name: Name of the new folder
    :param parent_id: ID of the parent folder
    :return: ID of the created folder
    """
    try:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        print(f"Folder '{folder_name}' created successfully with ID: {folder.get('id')}")
        return folder.get('id')
    except Exception as e:
        print(f"Error creating folder '{folder_name}': {e}")
        return None

def upload_file_to_folder(service, folder_id, file_path):
    """
    Upload a file to a specific folder in Google Drive.
    :param service: Google Drive service object
    :param folder_id: ID of the folder to upload to
    :param file_path: Path of the file to upload
    :return: ID of the uploaded file
    """
    try:
        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"File '{file_name}' uploaded successfully with ID: {uploaded_file.get('id')}")
        return uploaded_file.get('id')
    except Exception as e:
        print(f"Error uploading file '{file_path}': {e}")
        return None

def get_folder_link(folder_id):
    """
    Generate a shareable link for a Google Drive folder.
    :param folder_id: ID of the folder
    :return: Shareable link of the folder
    """
    return f"https://drive.google.com/drive/folders/{folder_id}"

if __name__ == '__main__':
    # Authenticate and get the Google Drive service
    service = authenticate_google_drive()
    if not service:
        print("Failed to authenticate with Google Drive API. Exiting...")
        exit(1)

    # Parent folder ID (from the provided URL)
    # example parent folder location https://drive.google.com/drive/folders/1MXdX5VLVGmqEF
    parent_folder_id = '1MXdX5VLVGmqEF'

    # Create a new folder
    new_folder_name = 'samrat file'
    new_folder_id = create_folder(service, new_folder_name, parent_folder_id)
    if not new_folder_id:
        print("Failed to create folder. Exiting...")
        exit(1)

    # Directory containing files to upload
    local_directory = r"C:\Users\pc\Documents\Downloads"
    if not os.path.exists(local_directory):
        print(f"The directory '{local_directory}' does not exist. Exiting...")
        exit(1)

    # Upload files from the local directory to the created folder
    for file_name in os.listdir(local_directory):
        file_path = os.path.join(local_directory, file_name)
        if os.path.isfile(file_path):
            upload_file_to_folder(service, new_folder_id, file_path)

    # Get and print the shareable link of the folder
    folder_link = get_folder_link(new_folder_id)
    print(f"Shareable Folder Link: {folder_link}")
