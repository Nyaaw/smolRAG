import importlib
import os
from typing import Type

from smolrag.actions.action import Action

_registry: dict[str, Type[Action]] = {}


def _load_action(module_name: str) -> None:
    """Import a module from the actions package and register any Action subclass."""
    mod = importlib.import_module(f".{module_name}", package="smolrag.actions")
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if (
            isinstance(obj, type)
            and issubclass(obj, Action)
            and obj is not Action
            and hasattr(obj, "name")
        ):
            _registry[obj.name] = obj


_actions_dir = os.path.dirname(__file__)
for entry in os.listdir(_actions_dir):
    if entry.endswith(".py") and not entry.startswith("__"):
        module_name = entry.removesuffix(".py")
        _load_action(module_name)


def list_actions() -> dict[str, Type[Action]]:
    return dict(_registry)
