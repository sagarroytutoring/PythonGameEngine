from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from state import StateMachine, State

from abc import ABC, abstractmethod


class Game(ABC):
    start_state_id = ""

    def __init__(self, statemachine: StateMachine):
        self._state_id = self.start_state_id
        self.statemachine = statemachine

    @property
    def state_id(self):
        return self._state_id

    @state_id.setter
    def state_id(self, id: str):
        if id not in self.statemachine.states:
            raise RuntimeError(f"Cannot set state id to invalid state id {self.state_id}")
        self._state_id = id
    @property
    def state(self):
        if self._state_id not in self.statemachine.states:
            raise RuntimeError(f"Game has invalid state id {self._state_id}")
        return self.statemachine.states[self._state_id]

    def update(self) -> None:
        # Update game
        self.state.update()

        # Transition if needed
        new_id = self.state.transition(self)
        if new_id != self._state_id:
            old_state = self.state
            self.state.leave()
            self.state_id = new_id
            self.state.enter(old_state)

    @abstractmethod
    def run(self) -> None:
        pass
