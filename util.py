import dataclasses
from typing import ClassVar, Dict, Protocol, Type


class IsDataclass(Protocol):
    """
    Protocol for static typechecking of dataclasses
    stolen from:
    https://stackoverflow.com/questions/54668000/type-hint-for-an-instance-of-a-non-specific-dataclass
    """
    __dataclass_fields__: ClassVar[Dict]


def handover_to_dataclass(old_obj: IsDataclass, new_class: Type[IsDataclass]):
    """
    Makes a new dataclass object of new type and transfers all attribute values it can from given object
    Transferred attributes are those fields that are shared in both classes (which is checked by checking field names)

    :param old_obj: Dataclass object to transfer data from
    :param new_class: Class of new object to create
    :return: New object of class that has data from old object

    >>> @dataclasses.dataclass
    ... class Old:
    ...     a: int = 0
    ...     b: str = "hi"
    ...     c: float = .5
    >>> @dataclasses.dataclass
    ... class New:
    ...     a: int = 2
    ...     b: str = "bye"
    ...     d: float = .7
    >>> o1 = Old()
    >>> o2 = handover_to_dataclass(o1, New)
    >>> o2.a
    0
    >>> o2.b
    'hi'
    >>> o2.c
    Traceback (most recent call last):
    AttributeError: 'New' object has no attribute 'c'
    >>> o2.d
    0.7
    """
    new_obj = new_class()
    for field in dataclasses.fields(old_obj):
        if hasattr(new_obj, field.name):
            setattr(new_obj, field.name, getattr(old_obj, field.name))
    return new_obj


if __name__ == '__main__':
    import doctest
    doctest.testmod()
