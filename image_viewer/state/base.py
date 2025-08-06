"""Base classes for state"""

from abc import ABC, abstractmethod


class StateBase(ABC):
    """Base class for states"""

    __slots__ = ()

    @abstractmethod
    def reset(self) -> None:
        """Reset state to default values"""
