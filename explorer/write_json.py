
import json

from explorer import *

class Serialize:
    def __init__(self, system: System) -> None:
        self.sigmap = SignalMap(system)
        self.result = {}

    def __call__(self, obj) -> None:
        if isinstance(obj, System):
            res = {"id": id(obj), "kind": "system", "name": obj.name, "boards": [], "nets": []}
            for brd in obj.boards:
                res["boards"] += [id(brd)]
            for net in self.sigmap.nets.values():
                res["nets"] += [id(net)]
            self.result[id(obj)] = res
            self.result['root'] = id(obj)

            for net in self.sigmap.nets.values():
                self.__call__(net)

        if isinstance(obj, Board):
            res = {"id": id(obj), "kind": "board", "name": obj.name, "parent": id(obj.parent), "refdes": obj.refdes, "components": [], "signals": [], "interfaces": []}
            for com in obj.components:
                res["components"] += [id(com)]
            for sig in obj.signals:
                res["signals"] += [id(sig)]
            for iface in obj.interfaces:
                res["interfaces"] += [id(iface)]
            self.result[id(obj)] = res

        if isinstance(obj, Interface):
            res = {"id": id(obj), "kind": "interface", "name": obj.name, "parent": id(obj.parent), "other": None, "pins": []}
            if obj.other is not None:
                res["other"] = id(obj.other)
            res["pins"] = []
            for pin in obj._pins:
                res["pins"] += [id(pin)]
            self.result[id(obj)] = res

        if isinstance(obj, Component):
            res = {"id": id(obj), "kind": "component", "refdes": obj.refdes, "package": obj.package, "parent": id(obj.parent), "pins": []}
            for pin in obj._outer_pins:
                res["pins"] += [id(obj._outer_pins[pin])]
            self.result[id(obj)] = res

        if isinstance(obj, OuterPin):
            res = {"id": id(obj), "kind": "outerpin", "number": id(obj.number), "name": id(obj.name), "parent": id(obj.parent), "signal": None, "interfaces": []}
            if obj.signal is not None:
                res["signal"] = id(obj.signal)
            res["interfaces"] = []
            for iface in obj.interfaces:
                res["interfaces"] += [id(iface)]
            self.result[id(obj)] = res

        if isinstance(obj, Signal):
            res = {"id": id(obj), "kind": "signal", "name": obj.name, "parent": id(obj.parent), "pins": [], "net": id(self.sigmap.resolved_net(obj))}
            for pin in obj._pins:
                if isinstance(pin, OuterPin) is False:
                    continue
                res["pins"] += [id(pin)]
            self.result[id(obj)] = res

        if isinstance(obj, Net):
            res = {"id": id(obj), "kind": "net", "signals": []}
            for sig in obj._signals:
                res["signals"] += [id(sig)]
            self.result[id(obj)] = res

def write_json(system: System, file: str):

    serialize_and_add_id = Serialize(system)
    with open(file, "w") as f:
        for model in depth_first(system):
            serialize_and_add_id(model)
        f.write(json.dumps({"models": serialize_and_add_id.result}))


