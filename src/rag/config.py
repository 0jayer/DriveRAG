from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml
from dotenv import load_dotenv

_ENV_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_ENV_PLACEHOLDER = re.compile(r"\$\{[^}]*\}")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"


class ConfigError(ValueError):
    """Raised when application configuration is missing or invalid."""


@dataclass(frozen=True)
class ComponentSpec:
    class_path: str
    options: Mapping[str, object]
    dependencies: Mapping[str, str]


@dataclass(frozen=True)
class Settings:
    components: Mapping[str, ComponentSpec]


def _expand_environment(value: object, location: str) -> object:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in os.environ:
                raise ConfigError(
                    f"Environment variable {name!r} referenced at {location} is not set"
                )
            return os.environ[name]

        expanded = _ENV_REFERENCE.sub(replace, value)
        if _ENV_PLACEHOLDER.search(expanded):
            raise ConfigError(f"Invalid environment variable reference at {location}")
        return expanded

    if isinstance(value, list):
        return [
            _expand_environment(item, f"{location}[{index}]")
            for index, item in enumerate(value)
        ]

    if isinstance(value, dict):
        return {
            key: _expand_environment(item, f"{location}.{key}")
            for key, item in value.items()
        }

    return value


def _parse_component(name: str, raw: object) -> ComponentSpec:
    if not isinstance(raw, dict):
        raise ConfigError(f"Component {name!r} must be a mapping")

    unknown_fields = set(raw) - {"class", "options", "dependencies"}
    if unknown_fields:
        raise ConfigError(
            f"Component {name!r} has unsupported field(s): "
            f"{', '.join(sorted(map(str, unknown_fields)))}"
        )

    class_path = raw.get("class")
    if not isinstance(class_path, str) or not class_path.strip():
        raise ConfigError(f"Component {name!r} requires a non-empty 'class' path")

    options = raw.get("options", {})
    if not isinstance(options, dict):
        raise ConfigError(f"Component {name!r} 'options' must be a mapping")

    dependencies = raw.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise ConfigError(f"Component {name!r} 'dependencies' must be a mapping")

    parsed_dependencies: dict[str, str] = {}
    for argument, reference in dependencies.items():
        if not isinstance(argument, str) or not argument:
            raise ConfigError(f"Component {name!r} dependency names must be non-empty strings")
        if argument in options:
            raise ConfigError(
                f"Component {name!r} sets {argument!r} in both options and dependencies"
            )
        if not isinstance(reference, dict) or set(reference) != {"ref"}:
            raise ConfigError(
                f"Component {name!r} dependency {argument!r} must contain only a 'ref'"
            )
        target = reference["ref"]
        if not isinstance(target, str) or not target.strip():
            raise ConfigError(
                f"Component {name!r} dependency {argument!r} requires a non-empty reference"
            )
        parsed_dependencies[argument] = target

    return ComponentSpec(
        class_path=class_path,
        options=options,
        dependencies=parsed_dependencies,
    )


def load_settings(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    env_file: str | Path | None = None,
) -> Settings:
    """Load component settings, an optional dotenv file, and environment references."""
    config_path = Path(config_path)
    if env_file is None:
        candidate_env_file = config_path.parent / ".env"
        if candidate_env_file.is_file():
            load_dotenv(candidate_env_file, override=False)
    else:
        env_path = Path(env_file)
        if not env_path.is_file():
            raise FileNotFoundError(f"Environment file not found: {env_path}")
        load_dotenv(env_path, override=False)

    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise ConfigError(f"Configuration in {config_path} must be a YAML mapping")

    unknown_fields = set(raw_config) - {"components"}
    if unknown_fields:
        raise ConfigError(
            "Unsupported top-level field(s): "
            f"{', '.join(sorted(map(str, unknown_fields)))}"
        )

    raw_components = raw_config.get("components")
    if not isinstance(raw_components, dict) or not raw_components:
        raise ConfigError("Configuration must define a non-empty 'components' mapping")

    expanded_components = _expand_environment(raw_components, "components")
    if not isinstance(expanded_components, dict):
        raise ConfigError("'components' must be a mapping")

    components: dict[str, ComponentSpec] = {}
    for name, raw_component in expanded_components.items():
        if not isinstance(name, str) or not name.strip():
            raise ConfigError("Component names must be non-empty strings")
        components[name] = _parse_component(name, raw_component)

    return Settings(components=components)