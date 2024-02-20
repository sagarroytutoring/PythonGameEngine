from __future__ import annotations
from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from scene import Scene

from abc import ABC, abstractmethod
import data_store


class Game(ABC):
    def __init__(self, storetype: Type, start_scene: Type[Scene]):
        self.data = data_store.DataStore(storetype)
        self.scene = start_scene
        self.scene.enter(self.data)

    def update(self) -> None:
        # Update game
        self.scene.update()

        # Transition if needed
        self.scene.transition(self)

    @abstractmethod
    def run(self) -> None:
        pass
