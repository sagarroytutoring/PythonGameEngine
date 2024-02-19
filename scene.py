from __future__ import annotations
from typing import Callable, Type, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game import Game

from abc import ABC, abstractmethod
import inspect


class StateMachine(ABC):
    """
    State machine for a game with multiple scenes
    """

    def __init__(self):
        self.scenes: dict[str, "Scene"] = {}

    def register(self, id: str) -> Callable[[Type["Scene"]], Type["Scene"]]:
        """
        Register a class as a scene in this state machine.

        Used as a decorator
        :param id: ID to register scene under
        :return: Decorator for class
        """

        def dec(cls: Type[Scene]) -> Type[Scene]:
            if not issubclass(cls, Scene):
                raise TypeError("Class must be a subclass of Scene")
            if cls.data is None:
                raise TypeError("Scene must have a data class attribute")

            self.scenes[id] = cls()

            cls.id = id
            cls.transition_conditions = {
                m._transition_cond_for: m
                for _, m in inspect.getmembers(cls)
                if inspect.isfunction(m) and hasattr(m, "_transition_cond_for")
            }
            return cls

        return dec


transition_condition_type = Callable[["Scene", Game], bool]
def transition_condition(scene_id: str) -> Callable[[transition_condition_type], transition_condition_type]:
    def dec(method: transition_condition_type) -> transition_condition_type:
        method._transition_cond_for = scene_id
        return method
    return dec


class Scene(ABC):
    instance: Optional["Scene"] = None
    data: Optional[type] = None

    # This class attributse are automatically added when the class is registered, so no need to define it for your subclasses
    id: str
    transition_conditions: dict[str, list[Callable[["Scene"], bool]]]

    # Since each scene is just convenient way to wrap several functions, it shouldn't have multiple instances
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(Scene, cls).__new__(cls)
            return cls.instance
        raise RuntimeError(f"Cannot make another instance of {cls.__name__}")

    def __init__(self):
        self.dat = self.data()

    def transition(self, game: Game) -> str:
        """
        Transition function for a scene. Returns id of new scene (or the same scene)

        :param game: The current game
        :return: The scene id of the new scene
        """
        for scene_id, conditions in self.transition_conditions.items():
            if any(condition(self) for condition in conditions):
                return scene_id
        return self.id

    def enter(self, leaving: "Scene") -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self) -> None:
        pass
