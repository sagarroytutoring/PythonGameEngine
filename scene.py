from __future__ import annotations
from typing import Callable, Type, TYPE_CHECKING, Optional

from abc import ABC, abstractmethod
import inspect
from collections import defaultdict
import data_store


transition_condition_type = Callable[[Type["Scene"], "Cursor"], bool]
transition_act_type = Callable[[Type["Scene"], Type["Scene"], "Cursor"], None]


class TransitionCondition:
    def __init__(self, fun: transition_condition_type, dest: Type["Scene"]):
        self.fun = fun
        self.dest = dest
        self.act: list[transition_act_type] = []

    @classmethod
    def add(cls, dest: Type[Scene] | str) -> Callable[[transition_condition_type], TransitionCondition]:
        dest = Scene.classes_by_name.get(dest, dest)
        def dec(method: transition_condition_type) -> TransitionCondition:
            return cls(method, dest)
        return dec

    def transition_action(self, act: transition_act_type | TransitionContextStore) -> transition_act_type | TransitionContextStore:
        if isinstance(act, TransitionContextStore):
            self.act.append(act.act)
        else:
            self.act.append(act)
        return act

    def __call__(self, scene: Type[Scene], cursor: Cursor) -> bool:
        return self.fun(scene, cursor)


def transition_condition(dest: Type["Scene"] | str) -> Callable[[transition_condition_type], TransitionCondition]:
    return TransitionCondition.add(dest)


class TransitionContextStore:
    ENTER = 0
    LEAVE = 1
    types = {ENTER, LEAVE}

    def __init__(self, transition_act_type):
        self.act = transition_act_type
        self.contexts: tuple[list[Type["Scene"]], list[Type["Scene"]], list[Type["Scene"]]] = ([], [], [])

    def add_context(self, type: int, scene: Type["Scene"]):
        if type not in self.types:
            raise ValueError("Invalid type")
        self.contexts[type].append(scene)

    def __call__(self, src: Type["Scene"], dest: Type["Scene"], cursor: Cursor):
        self.act(src, dest, cursor)


def transition_action(src: Type[Scene] | str = None, dest: Type[Scene] | str = None, context: int = TransitionContextStore.LEAVE) -> Callable[[transition_act_type | TransitionContextStore], transition_act_type | TransitionContextStore]:
    if src is None and dest is None:
        raise ValueError("Have to set src or dest or both")

    if src is not None and dest is not None:
        src = Scene.classes_by_name.get(src, src)
        dest = Scene.classes_by_name.get(dest, dest)

        if context == TransitionContextStore.LEAVE:
            def dec(func: transition_act_type) -> transition_act_type:
                src.leave_trans_acts[dest].append(func)
                return func
        elif context == TransitionContextStore.ENTER:
            def dec(func: transition_act_type) -> transition_act_type:
                dest.enter_trans_acts[src].append(func)
                return func
        else:
            raise ValueError("Not a valid transition context")

        return dec

    # We have determined either src or dest is None
    scene = src if src is not None else dest
    scene = Scene.classes_by_name.get(scene, scene)
    context = TransitionContextStore.ENTER if src is not None else TransitionContextStore.LEAVE


    def dec(method: transition_act_type | TransitionContextStore) -> TransitionContextStore:
        if not isinstance(method, TransitionContextStore):
            store = TransitionContextStore(method)
        else:
            store = method
        store.add_context(context, scene)
        return store

    return dec


class Scene(ABC):
    classes_by_name: dict[str, Type["Scene"]] = {}
    class_keyed_dicts: set[str] = {"transition_conditions", "enter_trans_acts", "leave_trans_acts"}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Add class to dictionary of scene types
        cls.classes_by_name[cls.__name__] = cls

        # Make a copy of the parent dictionaries
        cls.transition_conditions = defaultdict(list, {scene: conds.copy() for scene, conds in cls.transition_conditions})
        cls.enter_trans_acts = defaultdict(list, {scene: acts.copy() for scene, acts in cls.enter_trans_acts})
        cls.leave_trans_acts = defaultdict(list, {scene: acts.copy() for scene, acts in cls.leave_trans_acts})

        # Add actions to dictionaries if any were created in this class by decoration
        for name, m in inspect.getmembers(cls):
            if isinstance(m, TransitionCondition):
                cls.transition_conditions[m.dest].append(m)
            elif isinstance(m, TransitionContextStore):
                for scene in m.contexts[TransitionContextStore.ENTER]:
                    cls.enter_trans_acts[scene].append(m.act)
                for scene in m.contexts[TransitionContextStore.LEAVE]:
                    cls.leave_trans_acts[scene].append(m.act)

        # Remove any strings in conditions or actions that refer to this class and replace with class
        cls._correct_strings()


    @classmethod
    def _correct_strings(cls) -> None:
        for scene in cls.classes_by_name.values():
            for dictname in cls.class_keyed_dicts:
                d = getattr(scene, dictname)
                if cls.__name__ in d:
                    d[cls] = d.pop(cls.__name__)

    @classmethod
    def assert_no_classnames(cls) -> None:
        for scene in cls.classes_by_name.values():
            for dictname in cls.class_keyed_dicts:
                d = getattr(scene, dictname)
                for key in d:
                    if isinstance(key, str):
                        raise TypeError(f"Dictionary {dictname} in scene {scene.__name__} has string key {key}")

    # These class attributes are automatically added when the scene is made, so don't define it for your subclasses
    transition_conditions: defaultdict[Type[Scene], list[TransitionCondition]] = defaultdict(list)
    enter_trans_acts: defaultdict[Type[Scene], list[transition_act_type]] = defaultdict(list)
    leave_trans_acts: defaultdict[Type[Scene], list[transition_act_type]] = defaultdict(list)

    # Since each scene is just convenient way to wrap several functions, it shouldn't have any instances
    def __new__(cls):
        raise RuntimeError(f"Cannot make instances of scenes")

    @classmethod
    def _detect_transition(cls, cursor: Cursor) -> Type[Scene]:
        for scene, conditions in cls.transition_conditions.items():
            for condition in conditions:
                if condition(cls, cursor):
                    for act in condition.act:
                        act(cls, scene, cursor)
                    return scene
        return cls

    @classmethod
    def _transition_cursor(cls, cursor: Cursor, scene: Optional[Type[Scene]]) -> None:
        curr_scene = cursor.scene
        if scene == curr_scene:
            return
        cursor.scene.leave(cursor, scene)
        cursor.scene = scene
        cursor.scene.enter(cursor, curr_scene)

    @classmethod
    def transition(cls, cursor: Cursor) -> None:
        """
        Transition function for a scene. Changes Global scene to new scene (or leaves it alone if no transition)

        :param cursor: The current Global
        :return: The scene _id of the new scene
        """
        cls._transition_cursor(cursor, cls._detect_transition(cursor))

    @classmethod
    def enter(cls, cursor: Cursor, src: Optional[Type[Scene]] = None) -> None:
        for act in cls.enter_trans_acts[src]:
            act(src, cls, cursor)
        cursor.data.transition(cursor, src, cls)

    @classmethod
    def update(cls, cursor: Cursor) -> None:
        pass

    @classmethod
    def leave(cls, cursor: Cursor, dest: Type[Scene]) -> None:
        for act in cls.leave_trans_acts[dest]:
            act(cls, dest, cursor)


class Cursor(ABC):
    def __init__(self, storetype: Type, start_scene: Type[Scene]):
        self.data = data_store.DataStore(storetype)
        self.scene = start_scene
        self.scene.enter(self)

    def update(self) -> None:
        # Update Global
        self.scene.update(self)

        # Transition if needed
        self.scene.transition(self)

    @abstractmethod
    def run(self) -> None:
        pass
