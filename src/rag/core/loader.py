from __future__ import annotations

import importlib
import inspect
from collections.abc import Mapping
from typing import TypeVar

from rag.config import Settings

T = TypeVar("T")
TRUSTED_MODULE_ROOTS = ("rag",)


class ComponentLoadError(ValueError):
    """Raised when a configured component cannot be safely loaded or constructed."""


def _is_trusted_module(module_name: str) -> bool:
    return any(
        module_name == root or module_name.startswith(f"{root}.")
        for root in TRUSTED_MODULE_ROOTS
    )


def load_class(class_path: str, expected_base: type[T]) -> type[T]:
    """Import a trusted class path and verify it implements the requested contract."""
    if not isinstance(class_path, str) or class_path.count(":") != 1:
        raise ComponentLoadError(
            f"Class path must use 'module:ClassName' syntax: {class_path!r}"
        )
    if not isinstance(expected_base, type) or expected_base is object:
        raise TypeError("expected_base must be a specific class or abstract contract")

    module_name, class_name = class_path.split(":")
    if (
        not module_name
        or not class_name
        or not all(part.isidentifier() for part in module_name.split("."))
        or not class_name.isidentifier()
    ):
        raise ComponentLoadError(f"Invalid class path: {class_path!r}")
    if not _is_trusted_module(module_name):
        raise ComponentLoadError(f"Untrusted module in class path: {module_name!r}")

    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise ComponentLoadError(
            f"Could not import module {module_name!r} for {class_path!r}"
        ) from exc

    try:
        candidate = getattr(module, class_name)
    except AttributeError as exc:
        raise ComponentLoadError(
            f"Class {class_name!r} was not found in module {module_name!r}"
        ) from exc

    if not isinstance(candidate, type):
        raise ComponentLoadError(f"Configured object {class_path!r} is not a class")
    if not _is_trusted_module(candidate.__module__):
        raise ComponentLoadError(
            f"Class {class_path!r} resolves to untrusted module "
            f"{candidate.__module__!r}"
        )
    if not issubclass(candidate, expected_base):
        raise ComponentLoadError(
            f"Class {class_path!r} must subclass {expected_base.__module__}."
            f"{expected_base.__qualname__}"
        )
    if inspect.isabstract(candidate):
        raise ComponentLoadError(f"Configured class {class_path!r} is abstract")

    return candidate


def build_components(
    settings: Settings,
    expected_types: Mapping[str, type[object]],
) -> dict[str, object]:
    """Resolve named dependencies and construct all configured components."""
    built: dict[str, object] = {}
    resolving: list[str] = []

    def build(name: str) -> object:
        if name in built:
            return built[name]
        if name in resolving:
            cycle = " -> ".join([*resolving, name])
            raise ComponentLoadError(f"Circular component dependency: {cycle}")
        if name not in settings.components:
            raise ComponentLoadError(f"Unknown component reference: {name!r}")

        expected_base = expected_types.get(name)
        if expected_base is None:
            raise ComponentLoadError(
                f"No expected contract was provided for component {name!r}"
            )

        spec = settings.components[name]
        resolving.append(name)
        try:
            dependencies = {
                argument: build(target)
                for argument, target in spec.dependencies.items()
            }
            component_class = load_class(spec.class_path, expected_base)
            try:
                component = component_class(**dict(spec.options), **dependencies)
            except TypeError as exc:
                raise ComponentLoadError(
                    f"Could not construct component {name!r} from "
                    f"{spec.class_path!r}; check its options and dependencies"
                ) from exc
            built[name] = component
            return component
        finally:
            resolving.pop()

    for component_name in settings.components:
        build(component_name)

    return built