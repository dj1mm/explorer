
from __future__ import annotations
from enum import IntEnum

from contextlib import contextmanager
from disjoint_set import DisjointSet

class ComponentType(IntEnum):
    """
    A component is either be a connector, a discrete, a chip or unspecified.
    """
    Default = 0
    Connector = 1
    Discrete = 2
    Chip = 3

class WireType(IntEnum):
    """
    A wire is either a wire carrying an ac signal, a wire carrying a static dc
    signal (eg a Gnd or Power net) or allegro's special no connect.
    """
    Default = 0
    DC = 1
    NC = 2

class System:
    """ system consists of one or more boards interconnected together."""
    def __init__(self, name = "Unnamed system") -> None:
        self.name = name
        self._boards: list[Board] = list()

    def add_board(self, board: Board):
        if board._parent is self: raise RuntimeError(f"board {board.identifier} is already part of system")
        if board._parent is not None: raise RuntimeError("board {board.identifier} is already part of a system")
        self._boards.append(board)
        board._parent = self

    def get_board(self, name: str):
        for board in self._boards:
            if board.identifier == name:
                return board
        raise RuntimeError(f"board {name} not found")

    @property
    def boards(self):
        return self._boards

    def __repr__(self) -> str:
        return f"System {self.name} ({len(self.boards)} boards)"

    def __str__(self) -> str:
        return f"System {hex(id(self))}"

class Board:
    """
    a board has a name, a identifier, a bunch of components and lots of wires.
    Name v/s identifier. Consider multiple raspberry pi boards.
    Name is rpi. identifier is rpi0, rpi1, rpi2 ...
    A board also has:
    - interfaces - these are connections to other interfaces on other boards
    """
    def __init__(self) -> None:
        self.name = ""
        self.identifier = ""
        self._parent: System | None       = None
        self._components: list[Component] = list()
        self._wires: list[Wire]           = list()
        self._interfaces: list[Interface] = list()

    @property
    def parent(self):
        if self._parent is None: raise RuntimeError("board malformed")
        return self._parent

    def add_component(self, component: Component):
        if component._parent is self: raise RuntimeError(f"component {component.refdes} is already part of board")
        if component._parent is not None: raise RuntimeError(f"component {component.refdes} is already part of another board")
        component._parent = self
        self._components.append(component)

    def get_component(self, name: str):
        for component in self._components:
            if component.refdes == name:
                return component
        raise RuntimeError(f"component {name} not found")

    @property
    def components(self):
        return self._components

    def add_wire(self, wire: Wire):
        if wire._parent is self: raise RuntimeError(f"wire {wire.name} is already part of board")
        if wire._parent is not None: raise RuntimeError(f"wire {wire.name} is already part of another board")
        wire._parent = self
        self._wires.append(wire)

    def get_wire(self, name: str):
        for wire in self._wires:
            if wire.name == name:
                return wire
        raise RuntimeError(f"wire {name} not found")

    @property
    def wires(self):
        return self._wires

    def add_interface(self, interface: Interface):
        if interface._parent is self: raise RuntimeError(f"interface {interface.name} is already part of board")
        if interface._parent is not None: raise RuntimeError(f"interface {interface.name} is already part of another board")
        interface._parent = self
        self._interfaces.append(interface)

    def get_interface(self, name: str):
        for interface in self._interfaces:
            if interface.name == name:
                return interface
        raise RuntimeError(f"interface {name} not found")

    @property
    def interfaces(self):
        return self._interfaces

    def __repr__(self) -> str:
        return f"Board {self.identifier} ({self.name}) ({len(self.components)} components) ({len(self.wires)} wires) ({len(self.interfaces)} interfaces)"

    def __str__(self) -> str:
        return f"Board {hex(id(self))}"

class Interface:
    """
    a board normally has no top level ports. It is a closed netlist. More often
    than not, it is desirable to physically mate two, or more boards together.

    In explorer, board connections are represented as interfaces and interfaces
    are connected together.

    ```
    # Consider a raspberry pi and its daughter board
    # rpi_brd = Board(...)
    # daughter_brd = Board(...)

    # Create board interfaces like so:
    rpi_40x2_header = Interface('male_headers')
    rpi_brd.add_interface(rpi_40x2_header)
    db_40x2_header = Interface('female_headers')
    daughter_brd.add_interface(db_40x2_header)

    # And connect both boards like that:
    rpi_40x2_header.connect(db_40x2_header)
    ```
    """
    def __init__(self, name: str) -> None:
        self._name = name

        self._parent: Board | None    = None
        self._other: Interface | None = None
        self._pins: list[Pin]         = list()

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        if self._parent is None: raise RuntimeError("interface malformed")
        return self._parent

    @property
    def other(self):
        return self._other

    def add_pin(self, pin: Pin):
        if pin.parent is None: raise RuntimeError("pin does not belong to a valid component")
        if pin.parent.parent is None or pin.parent.parent is not self.parent: raise RuntimeError("component and interface are on different board")
        if self in pin.interfaces: raise RuntimeError("pin already belongs to this interface")
        if self.other is not None: raise RuntimeError("cannot add pin to already connected interface")

        self._pins.append(pin)
        pin._interfaces.append(self)

    @property
    def pins(self):
        return self._pins

    def connect(self, other: Interface):
        if self.parent is None: raise RuntimeError("interface malformed")
        if other.parent is None: raise RuntimeError("interface malformed")

        if self._other is not None: raise RuntimeError(f"interface {self.name} is already connected")
        if other._other is not None: raise RuntimeError(f"interface {other.name} is already connected")
        if len(self._pins) != len(other._pins): raise RuntimeError("interface do not match")

        self._other = other
        other._other = self

    def __repr__(self) -> str:
        if self.other is None:
            return f"Interface {self.name} -> None ({len(self.pins)} pins)"
        return f"Interface {self.parent.identifier}.{self.name} -> {self.other.parent.identifier}.{self.other.name} ({len(self.pins)} pins)"

    def __str__(self) -> str:
        return f"Interface {hex(id(self))}"

class Component:
    """
    A component is found on a board. It has a refdes and corresponds to a
    package
    """
    def __init__(self, refdes: str, package: str) -> None:
        self._refdes  = refdes
        self._package = package
        self.type     = ComponentType.Default

        self._parent: Board | None = None
        self._pins: dict[str,Pin]  = dict()


        # A model is a list of pins that are actually connected when looked
        # from a system level pov.
        #
        # For example, from a system designer's pov, a resistor or a capacitor
        # electrically connects two net together (even though they are named
        # differently). Same goes for buffers
        self._model: list[tuple[str, str]] = []
        
        # If true, we will not apply the component model during mapping
        self.ignore_model = False

    @property
    def refdes(self):
        return self._refdes

    @property
    def package(self):
        return self._package

    @property
    def parent(self):
        if self._parent is None: raise RuntimeError("component malformed")
        return self._parent

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value: list[tuple[str, str]]):
        for (lhs, rhs) in value:
            if lhs not in self._pins: raise RuntimeError(f"Invalid {lhs} is not a valid pin")
            if rhs not in self._pins: raise RuntimeError(f"Invalid {rhs} is not a valid pin")
        self._model = value

    def add_pin(self, pin: Pin):
        if pin.number in self._pins: raise RuntimeError("redefinition of pin")
        self._pins[pin.number] = pin

    def get_pin(self, number: str):
        if number not in self._pins: raise RuntimeError(f"pin {number} not found")
        return self._pins[number]

    def __repr__(self) -> str:
        return f"Component {self.refdes} ({len(self._pins)} pins)"

    def __str__(self) -> str:
        return f"Component {hex(id(self))}"

class Pin:
    """
    when components are placed on a board, they have outerpins. Each outerpin
    have a pin number and a pin name and is connected to at most one signal.

    Same for interfaces. Each interface consists of several outerpins.

    A pin of a component can be part of multiple interfaces.
    """
    def __init__(self, number: str, name: str, parent: Component) -> None:
        self._number = number
        self._name = name
        self._parent = parent
        self._interfaces: list[Interface] = []

        self._wire: Wire | None = None

    @property
    def number(self):
        return self._number

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        return self._parent

    @property
    def interfaces(self):
        return self._interfaces

    @property
    def wire(self):
        return self._wire

    def __repr__(self) -> str:
        return f"Pin {self.parent.refdes}.{self.number}:{self.name} -> {repr(self.wire)}"

    def __str__(self) -> str:
        return f"Pin {hex(id(self))}"

class Wire:
    """
    wire represents a physical pcb trace - it has a name, it connects pins
    together
    """
    def __init__(self, name: str) -> None:
        self._name = name
        self.type = WireType.Default

        self._parent: Board | None = None
        self._pins: list[Pin] = list()

    @property
    def parent(self):
        if self._parent is None: raise RuntimeError("wire malformed")
        return self._parent

    @property
    def name(self):
        return self._name

    def connect(self, other: Pin):
        if self.parent != other.parent.parent: raise RuntimeError("wire and pin are on different board")

        pin = other.parent._pins[other.number]
        if pin._wire is self: raise RuntimeError("wire is already connected to this pin")
        if pin._wire is not None: raise RuntimeError("pin is already connected to another wire")
        other._wire = self
        pin._wire = self
        self._pins.append(pin)

    def __repr__(self) -> str:
        return f"Wire {self.name} ({self.type.name}) ({len(self._pins)} pins)"

    def __str__(self) -> str:
        return f"Wire {hex(id(self))} {self.type}"


class Net:
    def __init__(self, net_number: int, wires: set[Wire]):
        self.net_number = net_number
        self._wires = wires

    def __repr__(self) -> str:
        return f"Net #{self.net_number} ({len(self._wires)} wires)"

class Netlist:
    """
    The boards generated by the read_.* functions only provides a list of named
    wires and how they are interconnected together. There is no such notion
    of a net.

    In reality, for the data to be useful, every wire must map to exactly one
    net. Interconnected wires must map to the same net. This allows queries
    such as 'get list of pins connected to this pin' in decent time.

    This class scans every wires in a system, and does the net mapping.
    ```
    # Given:
    # sig_a = system.board1.sig_a
    # sig_b = system.board1.sig_b
    # sig_c = system.board1.sig_c
    # sig_a.connect(sig_c)

    sm = Netlist(system)
    sm.resolved_net(sig_a) == sm.resolved_net(sig_c) != sm.resolved_net(sig_b)
    ```
    """
    def __init__(self, system: System):
        set_of_wires_and_signals = DisjointSet()
        self.nets: dict[Wire, Net] = dict()

        for board in system.boards:
            for wire in board.wires:
                set_of_wires_and_signals.find(wire)
            for interface in board.interfaces:
                if interface.other is None:
                    continue
                for i in range(len(interface.pins)):
                    lhs = interface.pins[i].wire
                    rhs = interface.other.pins[i].wire
                    if lhs is None or rhs is None:
                        continue
                    # Note wire NC is a special wire. Any pins connected to
                    # the NC wire are 'No connect', ie are open. So,dont even
                    # try to merge NC wires with other wires if any
                    if (lhs.type == WireType.NC) ^ (rhs.type == WireType.NC):
                        continue
                    set_of_wires_and_signals.union(lhs, rhs)
            for component in board.components:
                if component.ignore_model:
                    continue
                for shorts in component.model:
                    lhs = component.get_pin(shorts[0]).wire
                    rhs = component.get_pin(shorts[1]).wire
                    if lhs is None or rhs is None:
                        continue
                    if (lhs.type == WireType.NC) ^ (rhs.type == WireType.NC):
                        continue
                    if lhs.type == WireType.DC or rhs.type == WireType.DC:
                        continue
                    set_of_wires_and_signals.union(lhs, rhs)

        net_number = 0
        for key,sigs in set_of_wires_and_signals.itersets(with_canonical_elements=True):
            self.nets[key] = Net(net_number, sigs)
            net_number += 1
        self.set_of_wires_and_signals = set_of_wires_and_signals

    def resolved_net(self, wire: Wire):
        """
        Given a wire (which is part of the system provided while constructing
        this class), get its corresponding net
        """
        if wire not in self.nets:
            wire = self.set_of_wires_and_signals.find(wire)
        if wire not in self.nets:
            raise ValueError("Wire not part of wire map")
        return self.nets[wire]

    def resolved_wires(self, wire: Wire):
        """
        Given a wire (which is part of the system provided while constructing
        this class), get all other wires electrically connected to it
        """
        return (sig for sig in self.resolved_net(wire)._wires if sig != wire)


class Dump:
    def __init__(self, obj, file = None, offset = 4) -> None:

        self.current_state = []

        self.current_state.append((0, False))
        self.offset = offset

        result = self.dump(obj)
        if file is None:
            print('\n'.join(result))
            return
        with open(file, "w") as f:
            f.write('\n'.join(result))

    def indentation(self):
        return ' ' * self.current_state[-1][0]

    def title(self):
        if self.current_state[-1][0] >= 2 and self.current_state[-1][1]:
            return ' ' * (self.current_state[-1][0]-2) + '- '
        return ' ' * self.current_state[-1][0]

    @contextmanager
    def indent(self, is_array: bool = False):
        state = (self.current_state[-1][0] + self.offset, is_array)
        self.current_state.append(state)
        yield self
        self.current_state.pop()

    def dump(self, obj):
        fcall = f'dump_{obj.__class__.__name__.lower()}'
        return getattr(self, fcall, lambda x: [f"{self.title()}Unsupported feature {fcall}"])(obj)

    def dump_system(self, inst: System):
        result = []
        result += [f"{self.title()}System {hex(id(inst))} name: '{inst.name}'"]

        if len(inst._boards) == 0:
            result += [f"{self.indentation()}boards: []"]
        else:
            result += [f"{self.indentation()}boards:"]
        for brd in inst._boards:
            with self.indent(True):
                result += self.dump(brd)


        return result

    def dump_board(self, inst: Board):
        result = []
        result += [f"{self.title()}Board {hex(id(inst))} name: '{inst.name}' identifier: '{inst.identifier}'"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]

        if len(inst._components) == 0:
            result += [f"{self.indentation()}components: []"]
        else:
            result += [f"{self.indentation()}components:"]
        for component in inst._components:
            with self.indent(True):
                result += self.dump(component)

        if len(inst._wires) == 0:
            result += [f"{self.indentation()}wires: []"]
        else:
            result += [f"{self.indentation()}wires:"]
        for wire in inst._wires:
            with self.indent(True):
                result += self.dump(wire)

        if len(inst._interfaces) == 0:
            result += [f"{self.indentation()}interfaces: []"]
        else:
            result += [f"{self.indentation()}interfaces:"]
        for interface in inst._interfaces:
            with self.indent(True):
                result += self.dump(interface)

        return result

    def dump_interface(self, inst: Interface):
        result = []
        result += [f"{self.title()}Interface {hex(id(inst))} name: '{inst.name}'"]
        result += [f"{self.indentation()}other&: {inst.other}"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]

        if len(inst._pins) == 0:
            result += [f"{self.indentation()}pins: []"]
        else:
            result += [f"{self.indentation()}pins:"]
        for pin in inst._pins:
            with self.indent(True):
                result += [f"{self.title()}{pin}"]

        return result

    def dump_component(self, inst):
        result = []
        result += [f"{self.title()}Component {hex(id(inst))} refdes: '{inst.refdes}' package: '{inst.package}' model: {inst.model} ignore_model: {inst.ignore_model}"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]

        if len(inst._pins) == 0:
            result += [f"{self.indentation()}pins: {{}}"]
        else:
            result += [f"{self.indentation()}pins:"]
        for pin in inst._pins:
            with self.indent(True):
                result += [f"{self.title()}'{pin}' =>"]
                with self.indent():
                    result += self.dump(inst._pins[pin])

        return result

    def dump_pin(self, inst: Pin):
        result = []
        result += [f"{self.title()}Pin {hex(id(inst))} number: {inst.number} name: {inst.name}"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]
        result += [f"{self.indentation()}wire&: {inst._wire}"]

        if len(inst._interfaces) == 0:
            result += [f"{self.indentation()}interfaces&: []"]
        else:
            result += [f"{self.indentation()}interfaces&:"]
        for interface in inst._interfaces:
            with self.indent(True):
                result += [f"{self.title()}{interface}"]

        return result

    def dump_wire(self, inst):
        result = []
        result += [f"{self.title()}Wire {hex(id(inst))} name: '{inst.name}' type: {inst.type.name}"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]

        if len(inst._pins) == 0:
            result += [f"{self.indentation()}pins: []"]
        else:
            result += [f"{self.indentation()}pins:"]
        for pin in inst._pins:
            with self.indent(True):
                result += [f"{self.title()}{pin}"]

        return result


