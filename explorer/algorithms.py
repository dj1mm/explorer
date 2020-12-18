
from typing import Any
from explorer.models import *

def depth_first(obj: Any):
    """
    Given an object or an iterator of objects, visit the given object and its
    children, depth first.
    Takes single argument ``obj``.
    ``Obj`` can be a FirstClassModel or an iterator of FirstClassModels.
    """

    try:
        obj = iter(obj)
    except TypeError:
        obj = iter([obj])

    for o in obj:
        yield from _depth_first(o)

def _depth_first(obj: Any):
    """
    Implementation of depth_first
    """
    if isinstance(obj, System):
        yield obj
        yield from depth_first(obj.boards)

    if isinstance(obj, Board):
        yield obj
        yield from depth_first(obj.components)
        yield from depth_first(obj.signals)
        yield from depth_first(obj.interfaces)

    if isinstance(obj, Interface):
        yield obj

    if isinstance(obj, Component):
        yield obj
        yield from depth_first(obj._outer_pins)

    if isinstance(obj, OuterPin):
        yield obj

    if isinstance(obj, Signal):
        yield obj

    if isinstance(obj, Net):
        yield obj
