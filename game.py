from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene import StateMachine, Scene

from abc import ABC, abstractmethod


class Game(ABC):
    start_scene_id = ""

    def __init__(self, statemachine: StateMachine):
        self._scene_id = self.start_scene_id
        self.statemachine = statemachine

    @property
    def scene_id(self):
        return self._scene_id

    @scene_id.setter
    def scene_id(self, id: str):
        if id not in self.statemachine.scenes:
            raise RuntimeError(f"Cannot set scene id to invalid scene id {self.scene_id}")
        self._scene_id = id
    @property
    def scene(self):
        if self._scene_id not in self.statemachine.scenes:
            raise RuntimeError(f"Game has invalid scene id {self._scene_id}")
        return self.statemachine.scenes[self._scene_id]

    def update(self) -> None:
        # Update game
        self.scene.update()

        # Transition if needed
        new_id = self.scene.transition(self)
        if new_id != self._scene_id:
            old_scene = self.scene
            self.scene.leave()
            self.scene_id = new_id
            self.scene.enter(old_scene)

    @abstractmethod
    def run(self) -> None:
        pass
