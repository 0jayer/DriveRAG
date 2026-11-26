from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from rag.config import DEFAULT_CONFIG_PATH, load_settings
from rag.core.loader import ComponentLoadError, build_components
from rag.sources.data_source import DataSource
from rag.sources.gdrive.cred_provider import CredentialProvider
from rag.sources.gdrive.path_resolver import PathResolver
from rag.storage.database import Database
from rag.storage.file_repo import FileRepo

_COMPONENT_TYPES: dict[str, type[object]] = {
    "database": Database,
    "credential_provider": CredentialProvider,
    "path_resolver": PathResolver,
    "data_source": DataSource,
    "file_repo": FileRepo,
}
T = TypeVar("T")


@dataclass(frozen=True)
class AppContainer:
    data_source: DataSource
    database: Database
    file_repo: FileRepo


def build_container(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    env_file: str | Path | None = None,
) -> AppContainer:
    settings = load_settings(config_path, env_file=env_file)

    missing = _COMPONENT_TYPES.keys() - settings.components.keys()
    if missing:
        raise ComponentLoadError(
            f"Configuration is missing required component(s): {', '.join(sorted(missing))}"
        )

    components = build_components(settings, _COMPONENT_TYPES)
    return AppContainer(
        data_source=_require_component(components, "data_source", DataSource),
        database=_require_component(components, "database", Database),
        file_repo=_require_component(components, "file_repo", FileRepo),
    )


def _require_component(
    components: dict[str, object],
    name: str,
    expected_type: type[T],
) -> T:
    component = components[name]
    if not isinstance(component, expected_type):
        raise ComponentLoadError(
            f"Component {name!r} is not an instance of {expected_type.__name__}"
        )
    return component