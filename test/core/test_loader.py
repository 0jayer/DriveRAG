import pytest

from rag.config import ComponentSpec, Settings
from rag.core.loader import ComponentLoadError, build_components, load_class
from rag.sources.data_source import DataSource
from rag.sources.gdrive.cred_provider import CredentialProvider
from rag.sources.gdrive.drive_auth_cred_provider import DriveAuth
from rag.sources.gdrive.drive import Drive
from rag.sources.gdrive.path_resolver import PathResolver
from rag.storage.database import Database
from rag.storage.file_repo import FileRepo
from rag.storage.postgres_file_repo import PostgresFileRepo


def make_settings() -> Settings:
    return Settings(
        components={
            "database": ComponentSpec(
                class_path="rag.storage.postgres_database:PostgresDatabase",
                options={"db_url": "postgresql://localhost/test"},
                dependencies={},
            ),
            "credential_provider": ComponentSpec(
                class_path="rag.sources.gdrive.drive_auth_cred_provider:DriveAuth",
                options={
                    "credentials_path": "credentials.json",
                    "tokens_path": "token.json",
                },
                dependencies={},
            ),
            "path_resolver": ComponentSpec(
                class_path="rag.sources.gdrive.gdrive_path_resolver:GDrivePathResolver",
                options={},
                dependencies={},
            ),
            "data_source": ComponentSpec(
                class_path="rag.sources.gdrive.drive:Drive",
                options={},
                dependencies={
                    "credential_provider": "credential_provider",
                    "resolver": "path_resolver",
                },
            ),
            "file_repo": ComponentSpec(
                class_path="rag.storage.postgres_file_repo:PostgresFileRepo",
                options={},
                dependencies={"database": "database"},
            ),
        }
    )


def expected_types() -> dict[str, type[object]]:
    return {
        "database": Database,
        "credential_provider": CredentialProvider,
        "path_resolver": PathResolver,
        "data_source": DataSource,
        "file_repo": FileRepo,
    }


def test_load_class_rejects_untrusted_module_before_import():
    with pytest.raises(ComponentLoadError, match="Untrusted module"):
        load_class("os:path", DataSource)


def test_load_class_rejects_class_that_does_not_match_contract():
    with pytest.raises(ComponentLoadError, match="must subclass"):
        load_class("rag.storage.database:Database", DataSource)


def test_drive_auth_requires_configured_paths():
    with pytest.raises(TypeError):
        DriveAuth()


def test_build_components_resolves_dependencies_and_reuses_instances():
    components = build_components(make_settings(), expected_types())

    source = components["data_source"]
    repository = components["file_repo"]
    database = components["database"]

    assert isinstance(source, Drive)
    assert isinstance(source._credential_provider, DriveAuth)
    assert isinstance(source._resolver, PathResolver)
    assert isinstance(repository, PostgresFileRepo)
    assert repository._database is database


def test_build_components_rejects_unknown_dependency_reference():
    settings = Settings(
        components={
            "source": ComponentSpec(
                class_path="rag.sources.gdrive.drive:Drive",
                options={},
                dependencies={"resolver": "missing"},
            )
        }
    )

    with pytest.raises(ComponentLoadError, match="Unknown component reference"):
        build_components(settings, {"source": DataSource})


def test_build_components_rejects_dependency_cycles():
    settings = Settings(
        components={
            "first": ComponentSpec(
                class_path="rag.storage.postgres_database:PostgresDatabase",
                options={},
                dependencies={"db_url": "second"},
            ),
            "second": ComponentSpec(
                class_path="rag.storage.postgres_database:PostgresDatabase",
                options={},
                dependencies={"db_url": "first"},
            ),
        }
    )

    with pytest.raises(ComponentLoadError, match="Circular component dependency"):
        build_components(settings, {"first": Database, "second": Database})
