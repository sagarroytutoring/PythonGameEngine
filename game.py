from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene import Scene

from abc import ABC, abstractmethod


class Game(ABC):
    def __init__(self, start_scene: Scene):
        self.scene = start_scene
        self.scene.enter()

    def update(self) -> None:
        # Update game
        self.scene.update()

        # Transition if needed
        self.scene.transition(self)

    @abstractmethod
    def run(self) -> None:
        pass
