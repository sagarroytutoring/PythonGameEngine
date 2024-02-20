from __future__ import annotations
from typing import Callable, Type, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game import Game

from abc import ABC, abstractmethod
import inspect
from collections import defaultdict

import util
from data_store import DataStore


transition_condition_type = Callable[[Type["Scene"], DataStore], bool]
transition_act_type = Callable[[Type["Scene"], Type["Scene"], Game], None]


class StateMachine:
    """
    State machine for a game with multiple scenes
    """

    def __init__(self):
        self.scenes: set[Type[Scene]] = set()
        self.store: Optional[DataStore] = None
        self._finalized = False

    def register(self, cls: Type[Scene]) -> Type[Scene]:
        """
        Register a class as a scene in this state machine.
        Used as a decorator

        :return: Decorator for class
        """

        # Error checking
        if not issubclass(cls, Scene):
            raise TypeError("Class must be a subclass of Scene")

        # Add to scenes set and keep track of machine in class
        self.scenes.add(cls)

        return cls

    def finalize(self) -> None:
        self._check_finalized()

    def _check_finalized(self):
        if self._finalized:
            raise ValueError("Cannot re-finalize statemachine")
        self._finalize()

    def _finalize(self):
        self._finalized = True
        self._replace_class_strings()

    def _replace_class_strings(self):
        scenes_by_name = {scene.__name__: scene for scene in self.scenes if issubclass(scene, Scene)}
        self._remove_str_trans_conds(scenes_by_name)
        self._remove_str_trans_acts(scenes_by_name)

    def _remove_str_trans_conds(self, scenes_by_name: dict[str, Type[Scene]]):
        for scene_name, scene in scenes_by_name.items():
            for name, m in inspect.getmembers(scene):
                if inspect.isfunction(m):
                    if hasattr(m, "_transition_cond_for"):
                        # Replace string with scene if needed
                        if isinstance(m._transition_cond_for, str):
                            m._transition_cond_for = scenes_by_name[m._transition_cond_for]

                        # Add function to dictionary
                        scene.transition_conditions[m._transition_cond_for].add(m)
                else:
                    raise TypeError(f"Transition condition {name} in class {scene_name} is not a function")

    def _remove_str_trans_acts(self, scenes_by_name: dict[str, Type[Scene]]):
        for scene_name, scene in scenes_by_name.items():
            for name, m in inspect.getmembers(scene):
                if inspect.isfunction(m):
                    if hasattr(m, "_transition_act_entering") and m._transition_act_entering is not None:
                        # Replace string with scene if needed
                        if isinstance(m._transition_act_entering, str):
                            try:
                                m._transition_act_entering = scenes_by_name[m._transition_act_entering]
                            except KeyError:
                                raise ValueError(f"Scene referred to in transition conditions but not registered: {scene}")

                        # Add function to dictionary
                        scene.enter_trans_acts[m._transition_act_entering].add(m)

                    if hasattr(m, "_transition_act_leaving") and m._transition_act_leaving is not None:
                        # Replace string with scene if needed
                        if isinstance(m._transition_act_leaving, str):
                            try:
                                m._transition_act_leaving = scenes_by_name[m._transition_act_leaving]
                            except KeyError:
                                raise ValueError(f"Scene referred to in transition actions but not registered: {scene}")

                        # Add function to dictionary
                        scene.leave_trans_acts[m._transition_act_leaving].add(m)
                else:
                    raise TypeError(f"Transition action {name} in class {scene_name} is not a function")


def transition_condition(scene: Type[Scene] | str) -> Callable[[transition_condition_type], transition_condition_type]:
    def dec(method: transition_condition_type) -> transition_condition_type:
        method._transition_cond_for = scene
        return method
    return dec


def transition_action(entering: Type[Scene] | str = None, leaving: Type[Scene] | str = None) -> Callable[[transition_act_type], transition_act_type]:
    if entering is None and leaving is None:
        raise ValueError("Have to set entering or leaving or both")

    if entering is not None and leaving is not None:
        if isinstance(entering, str) or isinstance(leaving, str):
            raise ValueError("Leaving and entering cannot be strings when both are used")

        def dec(func: transition_act_type) -> transition_act_type:
            # Flipped because if "entering" is the state we are entering when we leave and vice versa
            entering.enter_trans_acts[leaving].add(func)
            # Just adding this for predictability:
            func._transition_act_entering = leaving
            return func
    else:
        def dec(method: transition_act_type) -> transition_act_type:
            # Flipped because if "entering" is the state we are entering when we leave and vice versa
            method._transition_act_leaving = entering
            method._transition_act_entering = leaving
            return method
    return dec


class Scene(ABC):
    # These class attributes are automatically added when the state machine is finalized, so no need to define it for your subclasses
    transition_conditions: defaultdict[Type[Scene], set[transition_condition_type]] = defaultdict(set)
    enter_trans_acts: defaultdict[Type[Scene], set[transition_act_type]] = defaultdict(set)
    leave_trans_acts: defaultdict[Type[Scene], set[transition_act_type]] = defaultdict(set)

    # Since each scene is just convenient way to wrap several functions, it shouldn't have any instances
    def __new__(cls):
        raise RuntimeError(f"Cannot make instances of scenes")

    @classmethod
    def _detect_transition(cls, data: DataStore) -> Type[Scene]:
        for scene, conditions in cls.transition_conditions.items():
            if any(condition(cls, data) for condition in conditions):
                return scene
        return cls

    @classmethod
    def _transition_game(cls, game: Game, scene: Optional[Type[Scene]]) -> None:
        curr_scene = game.scene
        if scene == curr_scene:
            return
        game.scene.leave(game.data, scene)
        game.scene = scene
        game.scene.enter(game.data, curr_scene)

    @classmethod
    def transition(cls, game: Game) -> None:
        """
        Transition function for a scene. Changes game scene to new scene (or leaves it alone if no transition)

        :param game: The current game
        :return: The scene _id of the new scene
        """
        cls._transition_game(game, cls._detect_transition(game.data))

    @classmethod
    def enter(cls, game: Game, leaving: Optional[Type[Scene]] = None) -> None:
        for act in cls.enter_trans_acts[leaving]:
            act(cls, leaving, game)
        game.data.transition(leaving, cls)

    @classmethod
    def update(cls, game: Game = None) -> None:
        pass

    @classmethod
    def leave(cls, game: Game, entering: Optional[Type[Scene]] = None) -> None:
        for act in cls.leave_trans_acts[entering]:
            act(cls, entering, game)
