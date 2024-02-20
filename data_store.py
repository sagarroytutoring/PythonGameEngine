from typing import Type, Optional, Any
from collections import defaultdict
from copy import deepcopy

import scene


class DataStore:
    class _Accessor:
        instances: dict[tuple["DataStore", Type[scene.Scene]], "DataStore._Accessor"] = {}

        def __new__(cls, store: "DataStore", sc: Type[scene.Scene]):
            tup = (store, sc)
            try:
                return cls.instances[tup]
            except KeyError:
                cls.instances[tup] = super().__new__(cls, *tup)
                return cls.instances[tup]

            # Other ways to write this and issues with them:

            # return cls.instances.setdefault(tup, super().__new__(cls, *tup))
            # This would create a new instance every time even if there was one already

            # if tup not in cls.instances:
            #     cls.instances[tup] = super().__new__(cls, *tup)
            # return cls.instances[tup]
            # This would run slower when the instance does exist, which is likely the most common case

        def __init__(self, store: "DataStore", sc: Type[scene.Scene]):
            self.store = store
            self.scene = sc

        def __getattr__(self, field: str):
            self.store._assert_access_allowed(field, self.scene)
            return getattr(self.store.storage_inst, field)

        def __setattr__(self, field, value):
            self.store._assert_access_allowed(field, self.scene)
            setattr(self.store.storage_inst, field, value)

    def __init__(self, cls: Type):
        self.storage_inst = cls()
        self.field_access: dict[str, access_types] = {}
        self.field_defaults: dict[str, Any] = {}
        self.transients: defaultdict[Type[scene.Scene], set] = defaultdict(set)
        for field in cls.__annotations__:
            try:
                default, access = getattr(cls, field)
            except (AttributeError, TypeError, ValueError):
                raise TypeError(
                    "Every data storage class must have type hint, default values, and access for all attributes"
                )

            self.field_access[field] = access
            self.field_defaults[field] = default
            if access.__class__ == Access.transient:
                for sc in access.args:
                    self.transients[sc].add(field)

            setattr(self.storage_inst, field, deepcopy(default))

    def _assert_access_allowed(self, field: str, sc: Type[scene.Scene]):
        if not (isinstance(self.field_access[field], Access.game) or sc in self.field_access[field].args):
            raise TypeError(f"Scene {sc.__name__} cannot access field {field}")

    def reset_transients(self, sc: Type[scene.Scene]):
        for field in self.transients[sc]:
            setattr(self.storage_inst, field, deepcopy(self.field_defaults[field]))

    def transition(self, leaving: Type[scene.Scene], entering: Type[scene.Scene]):
        self.reset_transients(leaving)
        self.reset_transients(entering)

    def __getitem__(self, item: Type[scene.Scene]):
        return self._Accessor(self, item)


access_types = "Access.static | Access.transient | Access.game"
class Access:
    class _StoreArgs:
        def __init__(self):
            self.args: Optional[set] = None

        def __call__(self, *args):
            self.args = set(args)

    class static(_StoreArgs): pass
    class transient(_StoreArgs): pass
    class game(_StoreArgs): pass
