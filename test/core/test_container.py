import pytest

from rag.container import AppContainer, build_container
from rag.core.loader import ComponentLoadError
from rag.sources.data_source import DataSource
from rag.sources.gdrive.cred_provider import CredentialProvider
from rag.sources.gdrive.drive import Drive
from rag.sources.gdrive.path_resolver import PathResolver
from rag.storage.database import Database
from rag.storage.file_repo import FileRepo
from rag.storage.postgres_file_repo import PostgresFileRepo


def write_config(path):
    path.write_text(
        """
components:
  database:
    class: rag.storage.database:Database
    options:
      db_url: ${DATABASE_URL}
  credential_provider:
    class: rag.sources.gdrive.drive_auth_cred_provider:DriveAuth
    options:
      credentials_path: ${GDRIVE_CREDENTIALS_PATH}
      tokens_path: ${GDRIVE_TOKEN_PATH}
  path_resolver:
    class: rag.sources.gdrive.path_resolver:PathResolver
  data_source:
    class: rag.sources.gdrive.drive:Drive
    dependencies:
      credential_provider:
        ref: credential_provider
      resolver:
        ref: path_resolver
  file_repo:
    class: rag.storage.postgres_file_repo:PostgresFileRepo
    dependencies:
      database:
        ref: database
""",
        encoding="utf-8",
    )


def set_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("GDRIVE_CREDENTIALS_PATH", "credentials.json")
    monkeypatch.setenv("GDRIVE_TOKEN_PATH", "token.json")


def test_build_container_constructs_components_without_connecting(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "config.yaml"
    write_config(config_path)
    set_environment(monkeypatch)

    container = build_container(config_path)

    assert isinstance(container, AppContainer)
    assert isinstance(container.data_source, Drive)
    assert isinstance(container.data_source, DataSource)
    assert isinstance(container.database, Database)
    assert isinstance(container.file_repo, PostgresFileRepo)
    assert isinstance(container.file_repo, FileRepo)
    assert isinstance(container.data_source._credential_provider, CredentialProvider)
    assert isinstance(container.data_source._resolver, PathResolver)
    assert container.file_repo._database is container.database


def test_build_container_rejects_missing_required_component(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "components:\n"
        "  database:\n"
        "    class: rag.storage.database:Database\n"
        "    options:\n"
        "      db_url: ${DATABASE_URL}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

    with pytest.raises(ComponentLoadError, match="missing required component"):
        build_container(config_path)
