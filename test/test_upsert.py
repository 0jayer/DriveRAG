from data.drive import auth, get_service, list_source_files
from data.metadata import get_conn, upsert_files

service = get_service(auth())
account_id = service.about().get(fields="user(emailAddress)").execute()["user"]["emailAddress"]
files = list_source_files(service, account_id)

with get_conn() as conn:
    upsert_files(conn, files)
    print(conn.execute("SELECT count(*) FROM files").fetchone())