from datetime import datetime

from googleapiclient.discovery import build
 
from rag.sources.source_file import SourceFile
from rag.sources.data_source import DataSource
from rag.sources.gdrive.path_resolver import PathResolver
from rag.sources.gdrive.cred_provider import CredentialProvider

class Drive(DataSource):
  def __init__(self, credential_provider: CredentialProvider, resolver:PathResolver,service_builder=build):
    #super().__init__()       DataSource has no init
    self._credential_provider = credential_provider
    self._resolver = resolver
    self._service_builder = service_builder
    self._service = None
    self._account_id = None



  #google drive api call
  def connect(self) -> None:
    credentials = self._credential_provider.get_credentials()
    self._service = self._service_builder(
            "drive",
            "v3",
            credentials=credentials,
        )
    self._account_id = (self._service.about().get(fields="user(emailAddress)").execute()["user"]["emailAddress"])
  def list_source_files(self) -> list[SourceFile]:
      files = self._resolver.resolve_paths(self._list_raw_files())
      return [
          self.to_source_file(f)
          for f in files
          if f["mimeType"] != PathResolver.FOLDER
      ]
  
  def fetch_content(self, file) -> bytes:
    raise NotImplementedError("Coming with the parsing step")

  #def list files with their attributes
  def _list_raw_files(self):
    files = []
    page_token = None
    while True:
      results = (
            self._service.files()
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
      account_id = self._account_id,
      source = "gdrive",
      external_id = raw["id"],
      name = raw["name"],
      path = raw["path"],
      mime_type = raw["mimeType"],
      source_hash = raw.get("md5Checksum"),
      modified_time = datetime.fromisoformat(raw["modifiedTime"].replace("Z", "+00:00")),
      size_bytes = int(size) if size is not None else None,
    )
