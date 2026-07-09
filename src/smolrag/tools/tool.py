from abc import ABC, abstractmethod
from pathlib import Path


class Tool(ABC):
    """Abstract base class for agent tools.

    Subclasses must set ``name``, ``description``, and ``parameters`` (JSON Schema)
    as class attributes, and implement ``execute()``.

    ``execute()`` receives keyword arguments matching the declared parameters
    and must return a plain string (result or error message).
    """

    name: str
    description: str
    parameters: dict

    def __init__(self, project_root: str) -> None:
        self.project_root = project_root

    @abstractmethod
    def execute(self, **kwargs: object) -> str:
        ...
