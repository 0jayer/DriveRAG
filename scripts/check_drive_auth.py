import os

from dotenv import load_dotenv

import os

from dotenv import load_dotenv

from googleapiclient.discovery import build

from rag.sources.gdrive.drive_auth_cred_provider import DriveAuth

load_dotenv()

auth = DriveAuth(
    credentials_path=os.environ["GDRIVE_CREDENTIALS_PATH"],
    tokens_path=os.environ["GDRIVE_TOKEN_PATH"],
)

creds = auth.get_credentials()
print("valid:", creds.valid)
print("has refresh token:", bool(creds.refresh_token))

service = build("drive", "v3", credentials=creds)
about = service.about().get(fields="user(emailAddress)").execute()
print("logged in as:", about["user"]["emailAddress"])

