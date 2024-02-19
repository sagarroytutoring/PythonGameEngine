from __future__ import annotations
from typing import Callable, Type, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game import Game

from abc import ABC, abstractmethod
import inspect


class StateMachine(ABC):
    """
    State machine for a game with multiple states
    """

    def __init__(self):
        self.states: dict[str, "State"] = {}

    def register(self, id: str) -> Callable[[Type["State"]], Type["State"]]:
        """
        Register a class as a state in this state machine.

        Used as a decorator
        :param id: ID to register state under
        :return: Decorator for class
        """

        def dec(cls: Type[State]) -> Type[State]:
            if not issubclass(cls, State):
                raise TypeError("Class must be a subclass of State")
            if cls.data is None:
                raise TypeError("State must have a data class attribute")

            self.states[id] = cls()

            cls.id = id
            cls.transition_conditions = {
                m._transition_cond_for: m
                for _, m in inspect.getmembers(cls)
                if inspect.isfunction(m) and hasattr(m, "_transition_cond_for")
            }
            return cls

        return dec


transition_condition_type = Callable[["State", Game], bool]
def transition_condition(state_id: str) -> Callable[[transition_condition_type], transition_condition_type]:
    def dec(method: transition_condition_type) -> transition_condition_type:
        method._transition_cond_for = state_id
        return method
    return dec


class State(ABC):
    instance: Optional["State"] = None
    data: Optional[type] = None

    # This class attributse are automatically added when the class is registered, so no need to define it for your subclasses
    id: str
    transition_conditions: dict[str, list[Callable[["State"], bool]]]

    # Since each state is just convenient way to wrap several functions, it shouldn't have multiple instances
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(State, cls).__new__(cls)
            return cls.instance
        raise RuntimeError(f"Cannot make another instance of {cls.__name__}")

    def __init__(self):
        self.dat = self.data()

    def transition(self, game: Game) -> str:
        """
        Transition function for a state. Returns id of new state

        :param game: The current game
        :return: The state id of the new state
        """
        for state_id, conditions in self.transition_conditions.items():
            if any(condition(self) for condition in conditions):
                return state_id
        return self.id

    @abstractmethod
    def enter(self, leaving: "State") -> None:
        pass

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def leave(self) -> None:
        pass
