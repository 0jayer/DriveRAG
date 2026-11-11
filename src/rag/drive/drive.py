from datetime import datetime

from googleapiclient.discovery import build
 
from rag.drive.source_file import SourceFile
from rag.drive.drive_auth import DriveAuth
from rag.drive.data_source import DataSource
from rag.drive.path_resolver import PathResolver

class Drive(DataSource):
  def __init__(self, auth:DriveAuth, resolver:PathResolver):
    #super().__init__()       DataSource has no init
    self.auth = auth
    self.resolver = resolver
    self.service = None
    self.account_id = None



  #google drive api call
  def connect(self):
    self.service = build("drive", "v3", credentials = self.auth.get_credentials())
    self.account_id = (self.service.about().get(fields="user(emailAddress)").execute()["user"]["emailAddress"])
    return self

  def list_source_files(self):
      files = self.resolver.resolve_paths(self._list_raw_files())
      return [
          self.to_source_file(f)
          for f in files
          if f["mimeType"] != PathResolver.FOLDER
      ]
  
  def fetch_content(self, file):
    raise NotImplementedError("Coming with the parsing step")

  #def list files with their attributes
  def _list_raw_files(self):
    files = []
    page_token = None
    while True:
      results = (
            self.service.files()
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
  def to_source_file(self, raw):
    size = raw.get("size")
    return SourceFile(
      account_id = self.account_id,
      source = "gdrive",
      external_id = raw["id"],
      name = raw["name"],
      path = raw["path"],
      mime_type = raw["mimeType"],
      source_hash = raw.get("md5Checksum"),
      modified_time = datetime.fromisoformat(raw["modifiedTime"].replace("Z", "+00:00")),
      size_bytes = int(size) if size is not None else None,
    )
