import importlib
from pathlib import Path
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
            and hasattr(obj, "description")
        ):
            _registry.append(obj)


_actions_dir = Path(__file__).parent

actions : list[tuple[int, Type[Action]]] = []

for entry in _actions_dir.iterdir():
    split0 = entry.name.split("_")[0]
    if entry.suffix == ".py" and not entry.name.startswith("__") and split0.isnumeric():
        actions.append((int(split0), entry.name))

actions.sort(key=lambda t: t[0])

#TODO: if not debug: filter(lambda t: t[0] < 50, actions)

for entry in (t[1] for t in actions):
    module_name = entry.removesuffix(".py")
    _load_action(module_name)
        

def list_actions() -> list[Type[Action]]:
    return (_registry)
