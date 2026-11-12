from abc import ABC, abstractmethod
from google.auth.credentials import Credentials


class CredentialProvider(ABC):
    @abstractmethod
    def get_credentials(self) -> Credentials:
        """Return valid credentials for the Google Drive API."""