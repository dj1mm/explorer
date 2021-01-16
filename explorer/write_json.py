
import json

from explorer import *

class Serialize:
    def __init__(self, system: System) -> None:
        self.netlist = Netlist(system)
        self.result = {}

    def __call__(self, obj) -> None:
        if isinstance(obj, System):
            res = {"id": id(obj), "kind": "system", "name": obj.name, "boards": [], "nets": []}
            for brd in obj.boards:
                res["boards"] += [id(brd)]
            for net in self.netlist.nets.values():
                res["nets"] += [id(net)]
            self.result[id(obj)] = res
            self.result['root'] = id(obj)

            for net in self.netlist.nets.values():
                self.__call__(net)

        if isinstance(obj, Board):
            res = {"id": id(obj), "kind": "board", "name": obj.name, "parent": id(obj.parent), "identifier": obj.identifier, "components": [], "wires": [], "interfaces": []}
            for com in obj.components:
                res["components"] += [id(com)]
            for sig in obj.wires:
                res["wires"] += [id(sig)]
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
            res = {"id": id(obj), "kind": "component", "refdes": obj.refdes, "package": obj.package, "parent": id(obj.parent), "type": id(obj.type), "pins": [], "model": []}
            for pin in obj._pins:
                res["pins"] += [id(obj._pins[pin])]
            if not obj.ignore_model and len(obj.model) > 0:
                res["model"] = obj.model
            self.result[id(obj)] = res

        if isinstance(obj, Pin):
            res = {"id": id(obj), "kind": "pin", "number": id(obj.number), "name": id(obj.name), "parent": id(obj.parent), "wire": None, "interfaces": []}
            if obj.wire is not None:
                res["wire"] = id(obj.wire)
            res["interfaces"] = []
            for iface in obj.interfaces:
                res["interfaces"] += [id(iface)]
            self.result[id(obj)] = res

        if isinstance(obj, Wire):
            res = {"id": id(obj), "kind": "wire", "name": obj.name, "type": obj.type, "parent": id(obj.parent), "pins": [], "net": id(self.netlist.resolved_net(obj))}
            for pin in obj._pins:
                if isinstance(pin, Pin) is False:
                    continue
                res["pins"] += [id(pin)]
            self.result[id(obj)] = res

        if isinstance(obj, Net):
            res = {"id": id(obj), "kind": "net", "wires": []}
            for sig in obj._wires:
                res["wires"] += [id(sig)]
            self.result[id(obj)] = res

def write_json(system: System, file: str):

    serialize_and_add_id = Serialize(system)
    with open(file, "w") as f:
        for model in depth_first(system):
            serialize_and_add_id(model)
        f.write(json.dumps({"models": serialize_and_add_id.result}))


