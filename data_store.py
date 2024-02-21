from typing import Type, Optional, Any, Callable
from collections import defaultdict, OrderedDict
from copy import deepcopy

import game
import scene

class DataStore:
    class _Accessor:
        def __init__(self, store: "DataStore", sc: Type["scene.Scene"]):
            super().__setattr__('_store', store)
            super().__setattr__('_scene', sc)

        def __getattr__(self, field: str):
            self._store._assert_access_allowed(field, self._scene)
            return getattr(self._store.storage_inst, field)

        def __setattr__(self, field, value):
            self._store._assert_access_allowed(field, self._scene)
            setattr(self._store.storage_inst, field, value)

    def __init__(self, cls: Type):
        self.storage_inst = cls()
        self.accessors: dict[Type[scene.Scene], DataStore._Accessor] = {}
        self.field_access: dict[str, access_types] = {}
        self.field_defaults: dict[str, Any] = {}
        self.transients: defaultdict[Type[scene.Scene], set] = defaultdict(set)
        self.transient_factories: dict[str, Callable[[game.Game], Any]] = {}
        for field in cls.__annotations__:
            try:
                default, access = getattr(cls, field)
            except (AttributeError, TypeError, ValueError):
                raise TypeError(
                    "Every data storage class must have type hint, default values, and access for all attributes"
                )

            self.field_access[field] = access
            self.field_defaults[field] = default
            if isinstance(access, Access.transient):
                for sc in access.args:
                    self.transients[sc].add(field)
                if access.factory is not None:
                    self.transient_factories[field] = access.factory

            setattr(self.storage_inst, field, deepcopy(default))

    def _assert_access_allowed(self, field: str, sc: Type["scene.Scene"]):
        try:
            access = self.field_access[field]
        except KeyError:
            raise AttributeError(f"Field {field} not present")
        if not (isinstance(access, Access.game) or sc in access.args):
            raise TypeError(f"Scene {sc.__name__} cannot access field {field}")

    def reset_transients(self, g: "game.Game", sc: Type["scene.Scene"]):
        for field in self.transients[sc]:
            if field in self.transient_factories:
                setattr(self.storage_inst, field, self.transient_factories[field](g))
            else:
                setattr(self.storage_inst, field, deepcopy(self.field_defaults[field]))

    def transition(self, g: "game.Game", leaving: Type["scene.Scene"], entering: Type["scene.Scene"]):
        self.reset_transients(g, leaving)
        self.reset_transients(g, entering)

    def __getitem__(self, item: Type["scene.Scene"]):
        # Put accessors in dictionary to avoid reinstantiating every time an attribute is needed
        try:
            return self.accessors[item]
        except KeyError:
            self.accessors[item] = self._Accessor(self, item)
        return self.accessors[item]


access_types = "Access.static | Access.transient | Access.game"
class Access:
    class _StoreArgs:
        def __init__(self, *args):
            self.args: Optional[set] = set(args)

    class static(_StoreArgs): pass
    class transient(_StoreArgs):
        def __init__(self, *args, factory=None):
            super().__init__(*args)
            self.factory = factory
    class game(_StoreArgs): pass


class Context:
    class _MultiAccessor:
        def __init__(self, context: "Context"):
            super().__setattr__('context', context)

        def __getattr__(self, field: str):
            key = self._guarded_which(field)
            cursor = self.context[key]
            return getattr(cursor.data[cursor.scene], field)

        def __setattr__(self, field, value):
            key = self._guarded_which(field)
            cursor = self.context[key]
            return setattr(cursor.data[cursor.scene], field, value)

        def which(self, field: str) -> Optional[str]:
            for key, cursor in reversed(self.context.cursors.items()):
                try:
                    # Check access is allowed
                    getattr(cursor.data[cursor.scene], field)
                    return key
                except (TypeError, AttributeError):
                    continue
            return None

        def _guarded_which(self, field: str) -> str:
            key = self.which(field)
            if key is None:
                raise AttributeError(f"Field {field} is not accessible from this context")
            return key

    def __init__(self):
        self.cursors: OrderedDict[str, game.Game] = OrderedDict()
        self.data = self._MultiAccessor(self)

    def add_cursor(self, key: str, cursor: "game.Game"):
        self.cursors[key] = cursor

    def pop_cursor(self) -> tuple[str, "game.Game"]:
        return self.cursors.popitem()

    def __getitem__(self, key: str) -> "game.Game":
        return self.cursors[key]
