from __future__ import annotations

import importlib
from pathlib import Path
from typing import Type

from smolrag.tools.tool import Tool

_registry: list[Type[Tool]] = []


def _load_tool(module_name: str) -> None:
    """Import a module from the tools package and register any Tool subclass."""
    mod = importlib.import_module(f".{module_name}", package="smolrag.tools")
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if (
            isinstance(obj, type)
            and issubclass(obj, Tool)
            and obj is not Tool
            and hasattr(obj, "name")
        ):
            _registry.append(obj)


_tools_dir = Path(__file__).parent

for entry in _tools_dir.iterdir():
    if entry.suffix == ".py" and not entry.name.startswith("__"):
        module_name = entry.stem
        _load_tool(module_name)


def list_tools() -> list[Type[Tool]]:
    """Return all registered Tool subclasses."""
    return list(_registry)
