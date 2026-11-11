import os
import json

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
 
class DriveAuth:
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/userinfo.email", "openid"]
    credentials_path = "F:/rag/secrets/credentials.json"
    tokens_path = "F:/rag/secrets/token.json"

    def __init__(self,
                 credentials_path = "F:/rag/secrets/credentials.json",
                 tokens_path = "F:/rag/secrets/token.json",
                 port = 8000
                ):
        self.credentials_path = credentials_path
        self.tokens_path = tokens_path
        self.port = port
    #token creation after first login
    def _save_token(self, creds):
        with open(self.tokens_path, "w", encoding = "utf-8") as token:
            token.write(creds.to_json())

    # check if token has scopes
    def _token_has_scopes(self):
        with open(self.tokens_path, encoding = "utf-8") as file:
            granted = set(json.load(file).get("scopes", []))
        return set(self.SCOPES) <= granted                  #check if required scopes is a subset of granted scopes


    def _load_saved_creds(self):
        if os.path.exists(self.tokens_path) and self._token_has_scopes():
            return Credentials.from_authorized_user_file(self.tokens_path, self.SCOPES)
        return None
    
    #drive authentication
    def get_credentials(self):
        creds = self._load_saved_creds()
        
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
            except RefreshError:
                creds = None

        if not creds or not creds.valid:
            creds = self._login()

        return creds

    def _login(self):
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
        creds = flow.run_local_server(port = 8000)
        self._save_token(creds)
        return creds