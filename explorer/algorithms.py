
from typing import Any

from explorer.models import *

def depth_first(obj: Any):
    """

    depth_first(obj)

    Given an object or an iterator of objects, visit the given object and its
    children, depth first.

    Parameters
    ----------
    obj: object, Iterable - required
        The object from where we start browsing.

    Returns
    -------
    models: generator
        An iterator of the object and its children visited depth first
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
        yield from depth_first(obj.wires)
        yield from depth_first(obj.interfaces)

    if isinstance(obj, Interface):
        yield obj

    if isinstance(obj, Component):
        yield obj
        yield from depth_first(obj._pins.values())

    if isinstance(obj, Pin):
        yield obj

    if isinstance(obj, Wire):
        yield obj

    if isinstance(obj, Net):
        yield obj

def get_boards(obj):
    """

    get_boards(obj, ...)

    Get boards within an object.

    Parameters
    ----------
    obj: object, Iterable - required
        The object from where we must look for boards. For example, executing
        `get_boards(system, ...)` will return all boards defined in the system.

    Returns
    -------
    boards: generator
        The non None boards associated to the object or collection thereof

    """
    
    # filter function: Cull result if
    # - board is None
    fn = lambda x: x is not None

    try:
        iter(obj)
    except TypeError:
        obj = iter([obj])

    for o in obj:
        yield from filter(fn, _get_boards(o))

def _get_boards(obj: Any):
    """
    Implementation of get_boards
    """
    if isinstance(obj, System):
        for board in obj.boards:
            yield board
    if isinstance(obj, Board):
        pass
    if isinstance(obj, Interface):
        yield obj.parent
    if isinstance(obj, Component):
        yield obj.parent
    if isinstance(obj, Pin):
        pass
    if isinstance(obj, Wire):
        yield obj.parent
    if isinstance(obj,  Net):
        pass

def get_interfaces(obj):
    """

    get_interfaces(obj, ...)

    Get an interface within an object.

    Parameters
    ----------
    obj: object, Iterable - required
        The object from where we must look for interfaces. For example doing
        `get_interfaces(pin, ...)` on a pin will get the interface (if any)
        connected to the pin.

    Returns
    -------
    interfaces: generator
        The non None interfaces associated to the object or collection thereof

    """
    
    # filter function: Cull result if
    # - interface is None
    fn = lambda x: x is not None

    try:
        iter(obj)
    except TypeError:
        obj = iter([obj])

    for o in obj:
        yield from filter(fn, _get_interfaces(o))

def _get_interfaces(obj: Any):
    """
    Implementation of get_interfaces
    """
    if isinstance(obj, System):
        pass
    if isinstance(obj, Board):
        for interface in obj.interfaces:
            yield interface
    if isinstance(obj, Interface):
        yield obj.other
    if isinstance(obj, Component):
        pass
    if isinstance(obj, Pin):
        for interface in obj.interfaces:
            yield interface
    if isinstance(obj, Wire):
        pass
    if isinstance(obj, Net):
        pass

def get_components(obj):
    """

    get_components(obj, ...)

    Get component within an object.

    Parameters
    ----------
    obj: object, Iterable - required
        The object from where we must look for components. For example, doing
        `get_components(system, ...)` will return all components defined in all
        boards in the system.

    Returns
    -------
    components: generator
        The non None components associated to the object or collection thereof

    """
    
    # filter function: Cull result if
    # - component is None
    fn = lambda x: x is not None

    try:
        iter(obj)
    except TypeError:
        obj = iter([obj])

    for o in obj:
        yield from filter(fn, _get_components(o))

def _get_components(obj: Any):
    """
    Implementation of get_components
    """
    if isinstance(obj, System):
        pass
    if isinstance(obj, Board):
        for component in obj.components:
            yield component
    if isinstance(obj, Interface):
        pass
    if isinstance(obj, Component):
        pass
    if isinstance(obj, Pin):
        yield obj._parent
    if isinstance(obj, Wire):
        pass
    if isinstance(obj,  Net):
        pass


def get_wires(obj):
    """

    get_wires(obj, ...)

    Get wire within an object.

    Parameters
    ----------
    obj: object, Iterable - required
        The object from where we must look for wires. For example, doing
        `get_wires(system, ...)` will return all wires defined in all the
        boards defined in system.

    Returns
    -------
    wires: generator
        The non None wires associated to the object or collection thereof

    """
    
    # filter function: Cull result if
    # - wire is None
    fn = lambda x: x is not None

    try:
        iter(obj)
    except TypeError:
        obj = iter([obj])

    for o in obj:
        yield from filter(fn, _get_wires(o))

def _get_wires(obj: Any):
    """
    Implementation of get_wires
    """
    if isinstance(obj, System):
        pass
    if isinstance(obj, Board):
        for wire in obj.wires:
            yield wire
    if isinstance(obj, Interface):
        pass
    if isinstance(obj, Component):
        pass
    if isinstance(obj, Pin):
        yield obj._wire
    if isinstance(obj, Wire):
        pass
    if isinstance(obj, Net):
        for wire in obj._wires:
            yield wire

def get_pins(obj):
    """

    get_pins(obj, ...)

    Get pin within an object.

    Parameters
    ----------
    obj: object, Iterable - required
        The object from where we must look for pins. `get_pins(component, ...)`
        will return all pins defined in said component.

    Returns
    -------
    pins: generator
        The non None pins associated to the object or collection thereof

    """
    
    # filter function: Cull result if
    # - pin is None
    fn = lambda x: x is not None

    try:
        iter(obj)
    except TypeError:
        obj = iter([obj])

    for o in obj:
        yield from filter(fn, _get_pins(o))

def _get_pins(obj: Any):
    """
    Implementation of get_pins
    """
    if isinstance(obj, System):
        pass
    if isinstance(obj, Board):
        pass
    if isinstance(obj, Interface):
        for pin in obj.pins:
            yield pin
    if isinstance(obj, Component):
        for name in obj._pins:
            yield obj._pins[name]
    if isinstance(obj, Pin):
        pass
    if isinstance(obj, Wire):
        for pin in obj._pins:
            yield pin
    if isinstance(obj, Net):
        pass

