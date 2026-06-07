"""Base classes for simulation events."""

from __future__ import annotations
from dataclasses import dataclass
from abc import ABC, abstractmethod
from ..physics.kinematics import State


@dataclass
class Event(ABC):
    name: str

    @abstractmethod
    def apply(self, state: State) -> State:
        raise NotImplementedError
