"""
    Testing of context object and data access from context
"""

import data_store
import scene

class OuterCursor(scene.Cursor):
    def run(self) -> None: pass


class OuterScene1(scene.Scene): pass
class OuterScene2(scene.Scene): pass


class InnerCursor(scene.Cursor):
    def run(self) -> None: pass


class InnerScene1(scene.Scene): pass
class InnerScene2(scene.Scene): pass


class OuterData:
    test1: int = 1,             data_store.Access.Global()
    test2: int = 2,             data_store.Access.Global()
    test3: int = 3,             data_store.Access.Static(OuterScene1)


class InnerData:
    test4: int = 4,             data_store.Access.Global()
    test1: int = 5,             data_store.Access.Global()
    test5: int = 6,             data_store.Access.Static(InnerScene1)


cur1 = OuterCursor(OuterData, OuterScene1)
cur2 = InnerCursor(InnerData, InnerScene1)


test_cont = data_store.Context()


if __name__ == '__main__':
    test_cont.add_cursor("outer", cur1)
    test_cont.add_cursor("inner", cur2)

    print(test_cont.data.which("test1"))
    print(test_cont.data.which("test2"))
    print(test_cont.data.which("test3"))
    print(test_cont.data.which("test4"))
    print(test_cont.data.which("test5"))
    print(test_cont.data.which("test6"))

    test_cont.data.test1 = 7
    print(test_cont.data.test1)
    print(test_cont["outer"].data[OuterScene1].test1)
    test_cont["outer"].data[OuterScene1].test1 = 8
    print(test_cont.data.test1)
    print(test_cont["outer"].data[OuterScene1].test1)
