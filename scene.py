from __future__ import annotations
from typing import Callable, Type, TYPE_CHECKING, Optional, Iterable

from abc import ABC, abstractmethod
import inspect
from collections import defaultdict
import data_store


transition_condition_type = Callable[[Type["Scene"], "Cursor", "data_store.Context"], bool]
transition_act_type = Callable[[Type["Scene"], Type["Scene"], "Cursor", "data_store.Context"], None]


class TransitionCondition:
    def __init__(self, fun: transition_condition_type, dest: Type["Scene"], act: Iterable[transition_act_type] = None):
        self.fun = fun
        self.dest = dest
        self.act: list[transition_act_type] = [] if act is None else act

    @classmethod
    def add_method(cls, dest: Type[Scene] | str) -> Callable[[transition_condition_type], TransitionCondition]:
        dest = Scene.classes_by_name.get(dest, dest)
        def dec(method: transition_condition_type) -> TransitionCondition:
            return cls(method, dest)
        return dec

    @classmethod
    def add_function(cls, src: Type[Scene] | str, dest: Type[Scene] | str) -> Callable[[TransitionCondition | TransitionConditionContextStore], TransitionCondition | TransitionConditionContextStore]:
        src = Scene.classes_by_name.get(src, src)
        dest = Scene.classes_by_name.get(dest, dest)

        # TODO: add some way to add to source even if src/dest is a string and the scene is not defined yet

        def dec(func: TransitionCondition | TransitionConditionContextStore) -> TransitionConditionContextStore:
            if not isinstance(func, TransitionConditionContextStore):
                store = TransitionConditionContextStore(func)
            else:
                store = func
            store.add_context(src, dest)
            src.transition_conditions[dest].append(cls(store.cond, dest, store.act))
            return store

        return dec

    def transition_action(self, act: transition_act_type | TransitionActionContextStore) -> transition_act_type | TransitionActionContextStore:
        if isinstance(act, TransitionActionContextStore):
            self.act.append(act.act)
        else:
            self.act.append(act)
        return act

    def __call__(self, scene: Type[Scene], cursor: Cursor, context: data_store.Context) -> bool:
        return self.fun(scene, cursor, context)


def transition_condition(*args, **kwargs) -> Callable[[TransitionCondition | TransitionConditionContextStore], TransitionCondition | TransitionConditionContextStore]:
    args = (
        ([kwargs['src']] if 'src' in kwargs else [])
        + list(args)
        + ([kwargs['dest']] if 'dest' in kwargs else [])
    )

    if len(args) == 2:
        src, dest = args
        return TransitionCondition.add_function(src, dest)
    elif len(args) == 1:
        dest = args[0]
        return TransitionCondition.add_method(dest)
    else:
        raise ValueError("transition_condition can accept a destination and decorate a method, or can accept a "
                         f"source and destination and decorate a function. {len(args)} arguments is not allowed.")


class TransitionContextStore: pass


class TransitionActionContextStore(TransitionContextStore):
    ENTER = 0
    LEAVE = 1

    def __init__(self, act: transition_act_type):
        self.act = act
        self.contexts: tuple[list[Type["Scene"]], list[Type["Scene"]]] = ([], [])

    def add_context(self, type: int, scene: Type["Scene"]):
        if not 0 <= type < len(self.contexts):
            raise ValueError("Invalid type")
        self.contexts[type].append(scene)

    def __call__(self, src: Type["Scene"], dest: Type["Scene"], cursor: Cursor, context: data_store.Context):
        return self.act(src, dest, cursor, context)


class TransitionConditionContextStore(TransitionContextStore):
    def __init__(self, cond: transition_condition_type):
        self.cond = cond
        self.contexts: dict[Type[Scene], Type[Scene]] = {}
        self.act: list[transition_act_type] = []

    def add_context(self, src: Type["Scene"], dest: Type["Scene"]):
        if src in self.contexts:
            raise ValueError(f"Each transition condition can only be associated with a single source. Source {src.__name__} is already associated with this condition.")
        self.contexts[src] = dest

    def __call__(self, scene: Type["Scene"], cursor: Cursor, context: data_store.Context):
        return self.cond(scene, cursor, context)

    def transition_action(self, act: transition_act_type | TransitionActionContextStore) -> transition_act_type | TransitionActionContextStore:
        if isinstance(act, TransitionActionContextStore):
            self.act.append(act.act)
        else:
            self.act.append(act)
        return act


def transition_action(src: Type[Scene] | str = None, dest: Type[Scene] | str = None, context: int = TransitionActionContextStore.LEAVE) -> Callable[[transition_act_type | TransitionActionContextStore], transition_act_type | TransitionActionContextStore]:
    if src is None and dest is None:
        raise ValueError("Have to set src or dest or both")

    if src is not None and dest is not None:
        src = Scene.classes_by_name.get(src, src)
        dest = Scene.classes_by_name.get(dest, dest)

        # TODO: add some way to add to source even if src/dest is a string and the scene is not defined yet

        if context == TransitionActionContextStore.LEAVE:
            def dec(func: transition_act_type) -> transition_act_type:
                src.leave_trans_acts[dest].append(func)
                return func
        elif context == TransitionActionContextStore.ENTER:
            def dec(func: transition_act_type) -> transition_act_type:
                dest.enter_trans_acts[src].append(func)
                return func
        else:
            raise ValueError("Not a valid transition context")

        return dec

    # We have determined either src or dest is None
    scene = src if src is not None else dest
    scene = Scene.classes_by_name.get(scene, scene)
    context = TransitionActionContextStore.ENTER if src is not None else TransitionActionContextStore.LEAVE


    def dec(method: transition_act_type | TransitionActionContextStore) -> TransitionActionContextStore:
        if not isinstance(method, TransitionActionContextStore):
            store = TransitionActionContextStore(method)
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
            elif isinstance(m, TransitionActionContextStore):
                for scene in m.contexts[TransitionActionContextStore.ENTER]:
                    cls.enter_trans_acts[scene].append(m.act)
                for scene in m.contexts[TransitionActionContextStore.LEAVE]:
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
    def _detect_transition(cls, cursor: Cursor, context: data_store.Context) -> Type[Scene]:
        for scene, conditions in cls.transition_conditions.items():
            for condition in conditions:
                if condition(cls, cursor, context):
                    for act in condition.act:
                        act(cls, scene, cursor, context)
                    return scene
        return cls

    @classmethod
    def _transition_cursor(cls, cursor: Cursor, scene: Optional[Type[Scene]], context: data_store.Context) -> None:
        curr_scene = cursor.scene
        if scene == curr_scene:
            return
        cursor.scene.leave(cursor, scene, context)
        cursor.scene = scene
        cursor.scene.enter(cursor, curr_scene, context)

    @classmethod
    def transition(cls, cursor: Cursor, context: data_store.Context) -> None:
        """
        Transition function for a scene. Changes Global scene to new scene (or leaves it alone if no transition)

        :param cursor: The current Global
        :return: The scene _id of the new scene
        """
        cls._transition_cursor(cursor, cls._detect_transition(cursor, context), context)

    @classmethod
    def enter(cls, cursor: Cursor, src: Optional[Type[Scene]], context: data_store.Context) -> None:
        for act in cls.enter_trans_acts[src]:
            act(src, cls, cursor, context)
        cursor.data.transition(cursor, src, cls, context)

    @classmethod
    def update(cls, cursor: Cursor, context: data_store.Context) -> None:
        for curs in cursor.data[cls].cursors():
            curs.update(context)

    @classmethod
    def leave(cls, cursor: Cursor, dest: Type[Scene], context: data_store.Context) -> None:
        for act in cls.leave_trans_acts[dest]:
            act(cls, dest, cursor, context)


class Cursor(ABC):
    context_key: str = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        if cls.context_key is None:
            cls.context_key = cls.__name__

    def __init__(self, storetype: Type, start_scene: Type[Scene], subcursors: list[Cursor] = None):
        self.data = data_store.DataStore(storetype)
        self.scene = start_scene
        self.subcursors = [] if subcursors is None else subcursors

    def update(self, context: Optional[data_store.Context] = None) -> None:
        context = data_store.Context() if context is None else context

        # Add self to context
        context.add_cursor(self.context_key, self)

        # Update self
        self.scene.update(self, context)

        # Update subcursors
        for curs in self.subcursors:
            curs.update(context)

        # Transition if needed
        self.scene.transition(self, context)

        # Remove self from context
        context.pop_cursor()

    def run(self) -> None:
        pass
