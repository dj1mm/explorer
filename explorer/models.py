
from __future__ import annotations

from contextlib import contextmanager
from disjoint_set import DisjointSet

class System:
    """ system consists of one or more boards interconnected together."""
    def __init__(self, name = "Unnamed system") -> None:
        self.name = name
        self._boards: list[Board] = list()

    def add_board(self, board: Board):
        self._boards.append(board)

    def get_board(self, name: str):
        for board in self._boards:
            if board.refdes == name:
                return board
        raise RuntimeError(f"board {name} not found")

    @property
    def boards(self):
        return self._boards

    def __str__(self) -> str:
        return f"System {hex(id(self))}"

class Board:
    """
    a board has a name, a refdes, a bunch of components and lots of signals.
    Name v/s refdes. Consider multiple raspberry pi boards.
    Name is rpi. Refdes is rpi0, rpi1, rpi2 ...
    A board also has:
    - interfaces - these are connections to other interfaces on other boards
    - dummypins - something that connect two or more signals together
    """
    def __init__(self) -> None:
        self.name = ""
        self.refdes = ""
        self._components: list[Component] = list()
        self._signals: list[Signal] = list()
        self._interfaces: list[Interface] = list()
        self._dummypins: list[DummyPin] = list()

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

    def add_signal(self, signal: Signal):
        if signal._parent is self: raise RuntimeError(f"signal {signal.name} is already part of board")
        if signal._parent is not None: raise RuntimeError(f"signal {signal.name} is already part of another board")
        signal._parent = self
        self._signals.append(signal)

    def get_signal(self, name: str):
        for signal in self._signals:
            if signal.name == name:
                return signal
        raise RuntimeError(f"signal {name} not found")

    @property
    def signals(self):
        return self._signals

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

    def add_dummypin(self, dummypin: DummyPin):
        self._dummypins.append(dummypin)

    @property
    def dummypins(self):
        return self._dummypins

    def __str__(self) -> str:
        return f"Board {hex(id(self))}"

class Interface:
    """
    a board normally has no top level ports. It is a closed netlist. More often
    than not, it is desirable to physically mate multiple boards together, in
    which case the signals in both boards connect to the same electrical net.

    Eg 1, gpu has golden pins, and mates to a motherboard's pcie interface
    Eg 2, raspberry pi has a gpio header, and mates with a daughter board
    """
    def __init__(self, name: str) -> None:
        self._name = name

        self._parent: Board | None           = None
        self._other: Interface | None        = None
        self._pins: list[OuterPin]           = list()

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

    def add_pin(self, pin: OuterPin):
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

    def __str__(self) -> str:
        return f"Interface {hex(id(self))}"

class Component:
    """
    A component is found on a board. It has a refdes and corresponds to a
    package
    """
    def __init__(self, refdes: str, package: str) -> None:
        self._refdes = refdes
        self._package   = package

        self._parent: Board | None           = None
        self._outer_pins: dict[str,OuterPin] = dict()

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

    def add_pin(self, pin: OuterPin):
        if pin.number in self._outer_pins: raise RuntimeError("redefinition of pin")
        self._outer_pins[pin.number] = pin

    def get_pin(self, number: str):
        if number not in self._outer_pins: raise RuntimeError(f"pin {number} not found")
        return self._outer_pins[number]

    def __str__(self) -> str:
        return f"Component {hex(id(self))}"

class OuterPin:
    """
    when components are placed on a board, they have outerpins. Each outerpin
    have a pin number and a pin name and is connected to at most one signal.

    Same for interfaces. Each interface consists of several outerpins.
    """
    def __init__(self, number: str, name: str, parent: Component) -> None:
        self._number = number
        self._name = name
        self._parent = parent
        self._interfaces: list[Interface] = []

        self._signal: Signal | None = None

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
    def signal(self):
        return self._signal

    def __str__(self) -> str:
        return f"OuterPin {hex(id(self))}"

class Signal:
    """
    signal represents a physical pcb trace - it has a name, it connects pins
    together
    """
    def __init__(self, name: str) -> None:
        self._name = name

        self._parent: Board | None            = None
        self._pins: list[DummyPin | OuterPin] = list()

    @property
    def parent(self):
        if self._parent is None: raise RuntimeError("signal malformed")
        return self._parent

    @property
    def name(self):
        return self._name

    def connect(self, other: Signal | OuterPin):
        if isinstance(other, OuterPin):
            if self.parent != other.parent.parent: raise RuntimeError("signal and pin are on different board")

            outer_pin = other.parent._outer_pins[other.number]
            if outer_pin._signal is self: raise RuntimeError("signal is already connected to this pin")
            if outer_pin._signal is not None: raise RuntimeError("pin is already connected to another signal")
            other._signal = self
            outer_pin._signal = self
            self._pins.append(outer_pin)
        elif isinstance(other, Signal):
            if self.parent is None: raise RuntimeError("signal malformed")
            if other.parent is None: raise RuntimeError("signal malformed")
            if self.parent != other.parent: raise RuntimeError("signals are not part of same board")

            dummy_pin = DummyPin()
            dummy_pin._signals.append(self)
            dummy_pin._signals.append(other)

            self._pins.append(dummy_pin)
            other._pins.append(dummy_pin)

            self.parent.add_dummypin(dummy_pin)

    def __repr__(self) -> str:
        return f"Signal {self.parent.refdes}.{self.name}"

    def __str__(self) -> str:
        return f"Signal {hex(id(self))}"

class DummyPin:
    def __init__(self) -> None:
        super().__init__()
        self._signals: list[Signal] = list()

    @property
    def signals(self):
        return self._signals

    def __str__(self) -> str:
        return f"DummyPin {hex(id(self))}"

class Net:
    def __init__(self, net_number: int, signals: Set[Signal]):
        self.net_number = net_number
        self._signals = signals
    
    def __repr__(self) -> str:
        return f"Net id={self.net_number} {self._signals}"

class SignalMap:
    """
    The boards generated by the read_.* functions only provides a list of named
    signals and how they are interconnected together. There is no such notion
    of a net.

    In reality, for the data to be useful, every signal must map to exactly one
    net. Interconnected signals must map to the same net. This allows queries
    such as 'get list of pins connected to this pin' in decent time.

    This class scans every signals in a system, and does the net mapping.
    ```
    # Given:
    # sig_a = system.board1.sig_a
    # sig_b = system.board1.sig_b
    # sig_c = system.board1.sig_c
    # sig_a.connect(sig_c)

    sm = SignalMap(system)
    sm.resolved_net(sig_a) == sm.resolved_net(sig_c) != sm.resolved_net(sig_b)
    ```
    """
    def __init__(self, system: System):
        sigmap = DisjointSet()
        self.nets: dict[Signal, Net] = dict()

        for board in system.boards:
            for signal in board.signals:
                sigmap.find(signal)
            for dummypin in board.dummypins:
                # Note signal NC is a special signal. Any pins connected to the
                # NC signal are 'No connect', ie are open. So, dont even try to
                # merge NC signals with other signals if any
                for sig in dummypin.signals:
                    if (sig.name == 'NC') ^ (dummypin.signals[0].name == 'NC'):
                        continue
                    sigmap.union(sig, dummypin.signals[0])
            for interface in board.interfaces:
                if interface.other is None:
                    continue
                for i in range(len(interface.pins)):
                    lhs = interface.pins[i].signal
                    rhs = interface.other.pins[i].signal
                    if lhs is None or rhs is None:
                        continue
                    sigmap.union(lhs, rhs)

        net_number = 0
        for key,sigs in sigmap.itersets(with_canonical_elements=True):
            self.nets[key] = Net(net_number, sigs)
            net_number += 1
        self.sigmap = sigmap

    def resolved_net(self, signal: Signal):
        """
        Given a signal (which is part of the system provided while constructing
        this class), get its corresponding net
        """
        if signal not in self.nets:
            signal = self.sigmap.find(signal)
        if signal not in self.nets:
            raise ValueError("Signal not part of signal map")
        return self.nets[signal]


class Dump:
    def __init__(self, obj, offset = 4) -> None:

        self.current_state = []

        self.current_state.append((0, False))
        self.offset = offset

        result = self.dump(obj)
        print('\n'.join(result))

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
        result += [f"{self.title()}System {hex(id(inst))}"]

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
        result += [f"{self.title()}Board {hex(id(inst))} name: '{inst.name}' refdes: '{inst.refdes}'"]

        if len(inst._components) == 0:
            result += [f"{self.indentation()}components: []"]
        else:
            result += [f"{self.indentation()}components:"]
        for component in inst._components:
            with self.indent(True):
                result += self.dump(component)

        if len(inst._signals) == 0:
            result += [f"{self.indentation()}signals: []"]
        else:
            result += [f"{self.indentation()}signals:"]
        for signal in inst._signals:
            with self.indent(True):
                result += self.dump(signal)

        if len(inst._interfaces) == 0:
            result += [f"{self.indentation()}interfaces: []"]
        else:
            result += [f"{self.indentation()}interfaces:"]
        for interface in inst._interfaces:
            with self.indent(True):
                result += self.dump(interface)

        if len(inst._dummypins) == 0:
            result += [f"{self.indentation()}dummypins: []"]
        else:
            result += [f"{self.indentation()}dummypins:"]
        for dummypin in inst._dummypins:
            with self.indent(True):
                result += self.dump(dummypin)

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
        result += [f"{self.title()}Component {hex(id(inst))} refdes: '{inst.refdes}' package: '{inst.package}'"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]

        if len(inst._outer_pins) == 0:
            result += [f"{self.indentation()}outer_pins: {{}}"]
        else:
            result += [f"{self.indentation()}outer_pins:"]
        for pin in inst._outer_pins:
            with self.indent(True):
                result += [f"{self.title()}'{pin}' =>"]
                with self.indent():
                    result += self.dump(inst._outer_pins[pin])

        return result

    def dump_outerpin(self, inst: OuterPin):
        result = []
        result += [f"{self.title()}OuterPin {hex(id(inst))} number: {inst.number} name: {inst.name}"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]
        result += [f"{self.indentation()}signal&: {inst._signal}"]

        if len(inst._interfaces) == 0:
            result += [f"{self.indentation()}interfaces&: []"]
        else:
            result += [f"{self.indentation()}interfaces&:"]
        for interface in inst._interfaces:
            with self.indent(True):
                result += [f"{self.title()}{interface}"]

        return result

    def dump_signal(self, inst):
        result = []
        result += [f"{self.title()}Signal {hex(id(inst))} name: '{inst.name}'"]
        result += [f"{self.indentation()}parent&: {inst.parent}"]

        if len(inst._pins) == 0:
            result += [f"{self.indentation()}pins: []"]
        else:
            result += [f"{self.indentation()}pins:"]
        for pin in inst._pins:
            with self.indent(True):
                result += [f"{self.title()}{pin}"]

        return result

    def dump_dummypin(self, inst: DummyPin):
        result = []
        result += [f"{self.title()}DummyPin {hex(id(inst))}"]

        if len(inst._signals) == 0:
            result += [f"{self.indentation()}signals: []"]
        else:
            result += [f"{self.indentation()}signals:"]
        for signal in inst._signals:
            with self.indent(True):
                result += [f"{self.title()}{signal}"]

        return result

