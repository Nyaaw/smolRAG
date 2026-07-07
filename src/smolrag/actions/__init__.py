import importlib
import os
from typing import Type

from smolrag.actions.action import Action

_registry: list[tuple[int, Type[Action]]] = []


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
            _registry.append(obj)


_actions_dir = os.path.dirname(__file__) #TODO: only use pathlib

actions : list[tuple[int, Type[Action]]] = []

for path in os.listdir(_actions_dir):
    split0 = path.split("_")[0]
    if path.endswith(".py") and not path.startswith("__") and split0.isnumeric():
        actions.append((int(split0), path))

actions.sort(key=lambda t: t[0])

#TODO: if not debug: filter(lambda t: t[0] < 50, actions)

for entry in (t[1] for t in actions):
    module_name = entry.removesuffix(".py")
    _load_action(module_name)
        

def list_actions() -> list[Type[Action]]:
    return (_registry)
