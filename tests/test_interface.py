#!/usr/bin/python3

from explorer import *


def test_main():

    # Create system
    my_system = System()

    # Read the netlist of the mega board
    mega = read_eagle('tests/mega/mega.nets', 'tests/mega/mega.pins', 'tests/mega/mega.parts')
    mega.identifier = "mega"
    my_system.add_board(mega)

    mega_headers = Interface("mega_headers")
    mega.add_interface(mega_headers)
    for pin in mega.get_component("PWMH")._pins.values():
        mega_headers.add_pin(pin)
    for pin in mega.get_component("PWML")._pins.values():
        mega_headers.add_pin(pin)
    for pin in mega.get_component("POWER")._pins.values():
        mega_headers.add_pin(pin)
    for pin in mega.get_component("ADCL")._pins.values():
        mega_headers.add_pin(pin)

    # Read the netlist of the base shield
    base = read_eagle('tests/base/base.nets', 'tests/base/base.pins', 'tests/base/base.parts')
    base.identifier = "base"
    my_system.add_board(base)

    base_headers = Interface("base_headers")
    base.add_interface(base_headers)
    base_headers.add_pin(base.get_component("U2").get_pin("9"))
    base_headers.add_pin(base.get_component("U2").get_pin("10"))
    base_headers.add_pin(base.get_component("U2").get_pin("11"))
    base_headers.add_pin(base.get_component("U2").get_pin("12"))
    base_headers.add_pin(base.get_component("U2").get_pin("13"))
    base_headers.add_pin(base.get_component("U2").get_pin("14"))
    base_headers.add_pin(base.get_component("U2").get_pin("15"))
    base_headers.add_pin(base.get_component("U2").get_pin("16"))

    base_headers.add_pin(base.get_component("U2").get_pin("1"))
    base_headers.add_pin(base.get_component("U2").get_pin("2"))
    base_headers.add_pin(base.get_component("U2").get_pin("3"))
    base_headers.add_pin(base.get_component("U2").get_pin("4"))
    base_headers.add_pin(base.get_component("U2").get_pin("5"))
    base_headers.add_pin(base.get_component("U2").get_pin("6"))
    base_headers.add_pin(base.get_component("U2").get_pin("7"))
    base_headers.add_pin(base.get_component("U2").get_pin("8"))

    base_headers.add_pin(base.get_component("U2").get_pin("30"))
    base_headers.add_pin(base.get_component("U2").get_pin("29"))
    base_headers.add_pin(base.get_component("U2").get_pin("28"))
    base_headers.add_pin(base.get_component("U2").get_pin("27"))
    base_headers.add_pin(base.get_component("U2").get_pin("26"))
    base_headers.add_pin(base.get_component("U2").get_pin("25"))

    base_headers.add_pin(base.get_component("U2").get_pin("19"))
    base_headers.add_pin(base.get_component("U2").get_pin("20"))
    base_headers.add_pin(base.get_component("U2").get_pin("21"))
    base_headers.add_pin(base.get_component("U2").get_pin("22"))
    base_headers.add_pin(base.get_component("U2").get_pin("23"))
    base_headers.add_pin(base.get_component("U2").get_pin("24"))
    base_headers.add_pin(base.get_component("U2").get_pin("32"))
    base_headers.add_pin(base.get_component("U2").get_pin("31"))

    base_headers.connect(mega_headers)

    assert len(base._interfaces) == 1
    assert len(mega._interfaces) == 1
    assert base.get_interface("base_headers") == base._interfaces[0]
    assert mega.get_interface("mega_headers") == mega._interfaces[0]
    assert base._interfaces[0].other == mega._interfaces[0]
    assert mega._interfaces[0].other == base._interfaces[0]

