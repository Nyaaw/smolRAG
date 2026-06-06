from abc import ABC, abstractmethod


class Action(ABC):
    """Abstract base class for action pipelines."""

    def __init__(self, project_root: str) -> None:
        self.project_root = project_root

    @abstractmethod
    def run(self) -> None:
        ...
