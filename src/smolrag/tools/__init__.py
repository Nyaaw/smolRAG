from __future__ import annotations

import importlib
import os
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


_tools_dir = os.path.dirname(__file__)

for path in os.listdir(_tools_dir):
    if path.endswith(".py") and not path.startswith("__"):
        module_name = path.removesuffix(".py")
        _load_tool(module_name)


def list_tools() -> list[Type[Tool]]:
    """Return all registered Tool subclasses."""
    return list(_registry)
