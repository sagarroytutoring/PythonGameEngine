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
            if cls._machine is not None:
                raise ValueError("Scene is already registered with a statemachine")

            self.scenes[id] = cls()
            cls._machine = self

            cls._id = id
            cls.transition_conditions = {
                m._transition_cond_for: m
                for _, m in inspect.getmembers(cls)
                if inspect.isfunction(m) and hasattr(m, "_transition_cond_for")
            }
            return cls

        return dec


transition_condition_type = Callable[["Scene"], bool]
def transition_condition(scene_id: str) -> Callable[[transition_condition_type], transition_condition_type]:
    def dec(method: transition_condition_type) -> transition_condition_type:
        method._transition_cond_for = scene_id
        return method
    return dec


class Scene(ABC):
    _instance: Optional[Scene] = None
    data: Optional[type] = None

    # These class attributes are automatically added when the class is registered, so no need to define it for your subclasses
    _id: str
    transition_conditions: dict[str, list[transition_condition_type]]
    _machine: Optional[StateMachine] = None

    # Since each scene is just convenient way to wrap several functions, it shouldn't have multiple instances
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Scene, cls).__new__(cls)
            return cls._instance
        raise RuntimeError(f"Cannot make another instance of {cls.__name__}")

    def __init__(self):
        self.dat = self.data()

    def __eq__(self, other: Scene):
        return self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def _detect_transition(self) -> Scene:
        for scene_id, conditions in self.transition_conditions.items():
            if any(condition(self) for condition in conditions):
                return self._machine.scenes[scene_id]
        return self

    def _transition_game(self, game: Game, scene: Optional["Scene"]) -> None:
        curr_scene = game.scene
        if scene == curr_scene:
            return
        game.scene.leave(scene)
        game.scene = scene
        game.scene.enter(curr_scene)

    def transition(self, game: Game) -> None:
        """
        Transition function for a scene. Changes game scene to new scene (or leaves it alone if no transition)

        :param game: The current game
        :return: The scene _id of the new scene
        """
        self._transition_game(game, self._detect_transition())

    def enter(self, leaving: Optional[Scene] = None) -> None:
        pass

    def update(self) -> None:
        pass

    def leave(self, entering: Optional[Scene] = None) -> None:
        pass
