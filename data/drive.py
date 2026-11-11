import os.path
 
import json
from datetime import datetime
 
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
 
from datatypes import SourceFile

FOLDER = "application/vnd.google-apps.folder"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/userinfo.email", "openid"]
credentials_path = "F:/rag/secrets/credentials.json"
tokens_path = "F:/rag/secrets/token.json"

#google drive api call
def get_service(creds):
  return build("drive", "v3", credentials = creds)

#token creation after first login
def save_token(creds):
  with open(tokens_path, "w", encoding = "utf-8") as token:
    token.write(creds.to_json())

# check if token has scopes
def token_has_scopes(path, required_scopes):
  with open(path, encoding = "utf-8") as file:
    granted = set(json.load(file).get("scopes", []))
  return set(required_scopes) <= granted                  #check if required scopes is a subset of granted scopes

#building folder map, e.g getting folder name from their id
def build_folder_map(files):
  folders = {}
  for f in files:
    if f["mimeType"] == FOLDER:
      folders[f["id"]] = (f["name"], (f.get("parents") or [None])[0])

  return folders

#building folder paths 
def build_path(file,folders):
  parts = [file["name"]]
  parent = (file.get("parents") or [None])[0]
  seen = set()

  #finding parent folders if they havent already been found and making a file path
  while parent in folders and parent not in seen:
    seen.add(parent)
    name,parent = folders[parent]
    parts.insert(0, name)

  return "/".join(parts)

#appending folder path in to the files
def resolve_paths(files):
  folders = build_folder_map(files)
  for f in files:
    f["path"] = build_path(f,folders)
  return files

#drive authentication
def auth():
  creds = None

  if os.path.exists(tokens_path) and token_has_scopes(tokens_path, SCOPES):
    creds = Credentials.from_authorized_user_file(tokens_path, SCOPES)
  
  if creds and creds.expired and creds.refresh_token:
    try:
      creds.refresh(Request())
      save_token(creds)
    except RefreshError:
      creds = None


  if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port = 8000)
    save_token(creds)

  return creds

#def list files with their attributes
def list_files(service):
  files = []
  page_token = None
  while True:
    results = (
          service.files()
          .list(
            q = "trashed = false",
            pageSize = 1000, 
            fields = 
            "nextPageToken, files(id, name, mimeType, md5Checksum, modifiedTime, size, parents, trashed)",
            pageToken = page_token,
          )
          .execute(num_retries = 5)
    )
    files.extend(results.get("files",[]))
    page_token = results.get("nextPageToken")
    if not page_token:
      return files

#turn files into SourceFiles data type
def to_source_file(account_id, raw, path):
  size = raw.get("size")
  return SourceFile(
    account_id = account_id,
    source = "gdrive",
    external_id = raw["id"],
    name = raw["name"],
    path = path,
    mime_type = raw["mimeType"],
    source_hash = raw.get("md5Checksum"),
    modified_time = datetime.fromisoformat(raw["modifiedTime"].replace("Z", "+00:00")),
    size_bytes = int(size) if size is not None else None,
  )

#returns a list of files, no folders
def list_source_files(service, account_id):
  files = resolve_paths(list_files(service))
  return [to_source_file(account_id, f, f["path"]) for f in files if f["mimeType"] != FOLDER]

#print function
def print_files(files):
  print(f"Total: {len(files)}\n")
  print("Files:")
  for f in files:
    print(
      f"name: {f.name}",
      f"id: {f.external_id}",
      f"mimeType: {f.mime_type}",
      f"source_hash: {f.source_hash}",
      f"size: {f.size_bytes}",
      f"modifiedTime: {f.modified_time}",
      f"path: {f.path}",
      sep="\n",
      end="\n\n",
  )

if __name__ == "__main__":
  creds = auth()
  service = get_service(creds)
  account_id = service.about().get(fields="user(emailAddress)").execute()["user"]["emailAddress"]
  files = list_source_files(service, account_id)
  print_files(files)
