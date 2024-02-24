from typing import Type, Optional, Any, Callable
from collections import defaultdict, OrderedDict
from copy import deepcopy
from abc import ABC

import scene


factory_type = Callable[["scene.Cursor", Type["scene.Scene"], "Context"], Any]
class DataStore:
    class _Accessor:
        def __init__(self, store: "DataStore", sc: Type["scene.Scene"]):
            super().__setattr__('_store', store)
            super().__setattr__('_scene', sc)
            super().__setattr__('_cursors', store.cursors_by_scene[sc] + store.cursors_global)

        def __getattr__(self, field: str):
            self._store._assert_access_allowed(field, self._scene)
            return getattr(self._store.storage_inst, field)

        def __setattr__(self, field, value):
            self._store._assert_access_allowed(field, self._scene)
            setattr(self._store.storage_inst, field, value)

        def cursors(self) -> list["scene.Cursor"]:
            return [getattr(self, curs) for curs in self._cursors]

    def __init__(self, cls: Type):
        self.storage_inst = cls()
        self.accessors: dict[Type[scene.Scene], DataStore._Accessor] = {}

        self.field_access: dict[str, access_types] = {}
        self.field_defaults: dict[str, Any] = {}

        self.transients: defaultdict[Type[scene.Scene], set] = defaultdict(set)
        self.transient_factories: dict[str, factory_type] = {}

        self.cursors_by_scene: defaultdict[Type[scene.Scene], list[str]] = defaultdict(list)
        self.cursors_global: list[str] = list()

        for field, hinttype in cls.__annotations__.items():
            try:
                default, access = getattr(cls, field)
            except (AttributeError, TypeError, ValueError):
                raise TypeError(
                    "Every data storage class must have type hint, default values, and access for all attributes"
                )

            self.field_access[field] = access
            self.field_defaults[field] = default
            if isinstance(access, StoreField.Transient):
                for sc in access.args:
                    self.transients[sc].add(field)
                if access.factory is not None:
                    self.transient_factories[field] = access.factory

            setattr(self.storage_inst, field, deepcopy(default))
            setattr(self.storage_inst, field, deepcopy(default))

            access.outer_class.field_action(self, field, default, hinttype, access)

    def _assert_access_allowed(self, field: str, sc: Type["scene.Scene"]):
        try:
            access = self.field_access[field]
        except KeyError:
            raise AttributeError(f"Field {field} not present")
        if not (isinstance(access, StoreField.Global) or sc in access.args):
            raise TypeError(f"Scene {sc.__name__} cannot access field {field}")

    def reset_transients(self, cursor: "scene.Cursor", sc: Type["scene.Scene"], context: "Context"):
        for field in self.transients[sc]:
            if field in self.transient_factories:
                setattr(self.storage_inst, field, self.transient_factories[field](cursor, sc, context))
            else:
                setattr(self.storage_inst, field, deepcopy(self.field_defaults[field]))

    def transition(self, cursor: "scene.Cursor", leaving: Type["scene.Scene"], entering: Type["scene.Scene"], context: "Context"):
        self.reset_transients(cursor, leaving, context)
        self.reset_transients(cursor, entering, context)

    def __getitem__(self, item: Type["scene.Scene"]):
        # Put accessors in dictionary to avoid reinstantiating every time an attribute is needed
        try:
            return self.accessors[item]
        except KeyError:
            self.accessors[item] = self._Accessor(self, item)
        return self.accessors[item]


access_types = "StoreField.Static | StoreField.Transient | StoreField.Global"
class StoreField(ABC):
    def __init_subclass__(cls):
        super().__init_subclass__()

        # Make copy of access classes so they are distinct in subclasses
        # Useful in data store to check for StoreField vs StoreChild
        for access_class in cls.access_classes:
            copy_class = type(cls.__name__ + '.' + access_class.__name__, (access_class,), {})
            setattr(cls, access_class.__name__, copy_class)
            setattr(copy_class, "outer_class", cls)

    class _StoreArgs:
        outer_class: Type["StoreField"]

        def __init__(self, *args, factory: factory_type = None):
            self.args: Optional[set] = set(args)
            self.factory = factory

    class Static(_StoreArgs): pass
    class Transient(_StoreArgs): pass

    class Global(_StoreArgs): pass

    access_classes = [Static, Transient, Global]

    @classmethod
    def field_action(cls, store: DataStore, field: str, default: Any, hint: type, access: access_types) -> None:
        pass


# This occurs automatically for subclasses via __init_subclass__, but have to do manually for StoreField
for access_class in StoreField.access_classes:
    access_class.outer_class = StoreField
del access_class


class StoreCursor(StoreField):
    @classmethod
    def field_action(cls, store: DataStore, field: str, default: Any, hint: type, access: access_types) -> None:
        if not issubclass(hint, scene.Cursor):
            raise TypeError("StoreCursor can only be applied to fields type hinted with scene.Cursor")
        if not isinstance(default, scene.Cursor):
            raise TypeError("StoreCursor default must be a scene.Cursor object")

        if isinstance(access, cls.Transient) or isinstance(access, cls.Static):
            for sc in access.args:
                store.cursors_by_scene[sc].append(field)
        elif isinstance(access, cls.Global):
            store.cursors_global.append(field)


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
        self.cursors: OrderedDict[str, scene.Cursor] = OrderedDict()
        self.data = self._MultiAccessor(self)

    def add_cursor(self, key: str, cursor: "scene.Cursor"):
        self.cursors[key] = cursor

    def pop_cursor(self) -> tuple[str, "scene.Cursor"]:
        return self.cursors.popitem()

    def __getitem__(self, key: str) -> "scene.Cursor":
        return self.cursors[key]
