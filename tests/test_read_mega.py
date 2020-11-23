#!/usr/bin/python3

from __future__ import annotations

from explorer import *

def test_main():
    mega = read_eagle('tests/mega/mega.nets', 'tests/mega/mega.pins', 'tests/mega/mega.parts')
    mega.refdes = "mega"

    my_system = System()
    my_system.add_board(mega)

    # Verify the generated model

    assert mega.name == "mega"
    assert mega.refdes == "mega"
    assert len(mega._components) == 68
    assert len(mega._signals) == 108
    assert len(mega._interfaces) == 0
    assert len(mega._dummypins) == 0

    # verify signal ADC0
    adc0 = mega.get_signal("ADC0")
    assert adc0.parent == mega
    assert len(adc0._pins) == 2

    # verify connector ADCL
    adcl = mega.get_component("ADCL")
    assert adcl.parent == mega
    assert len(adcl._outer_pins) == 8

    # verify connector ADCH
    adch = mega.get_component("ADCH")
    assert adch.parent == mega
    assert len(adch._outer_pins) == 8

    # verify connector IC3
    ic3 = mega.get_component("IC3")
    assert ic3.parent == mega
    assert len(ic3._outer_pins) == 100

    assert adcl.get_pin("1") in adc0._pins
    assert ic3.get_pin("97").signal == adc0

    # import io
    # from contextlib import redirect_stdout
    # with open('outputfile.out','w') as f:
    #     with io.StringIO() as buf, redirect_stdout(buf):
    #         Dump(my_system)
    #         output = buf.getvalue()
    #         f.write(output)



