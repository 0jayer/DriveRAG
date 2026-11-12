from googleapiclient.discovery import build

from rag.sources.gdrive.drive_auth_cred_provider import DriveAuth

auth = DriveAuth(
    credentials_path="F:/rag/secrets/credentials.json",
    tokens_path="F:/rag/secrets/token.json",
)

creds = auth.get_credentials()
print("valid:", creds.valid)
print("has refresh token:", bool(creds.refresh_token))

service = build("drive", "v3", credentials=creds)
about = service.about().get(fields="user(emailAddress)").execute()
print("logged in as:", about["user"]["emailAddress"])

