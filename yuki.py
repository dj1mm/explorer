#!/usr/bin/python3

from explorer import *


def main():

    # Create system
    my_system = System()

    # Read the netlist of the mega board
    mega = read_eagle('tests/mega/mega.nets', 'tests/mega/mega.pins', 'tests/mega/mega.parts')
    mega.refdes = "mega"
    my_system.add_board(mega)

    mega_headers = Interface("mega_headers")
    mega.add_interface(mega_headers)
    for number,pin in enumerate(mega.get_component("PWMH")._outer_pins.values()):
        mega_headers.add_pin(f"PWMH{number}", pin.name, pin.signal)
    for number,pin in enumerate(mega.get_component("PWML")._outer_pins.values()):
        mega_headers.add_pin(f"PWML{number}", pin.name, pin.signal)
    for number,pin in enumerate(mega.get_component("POWER")._outer_pins.values()):
        mega_headers.add_pin(f"POWER{number}", pin.name, pin.signal)
    for number,pin in enumerate(mega.get_component("ADCL")._outer_pins.values()):
        mega_headers.add_pin(f"ADCL{number}", pin.name, pin.signal)

    # Read the netlist of the base shield
    base = read_eagle('tests/base/base.nets', 'tests/base/base.pins', 'tests/base/base.parts')
    base.refdes = "base"
    my_system.add_board(base)

    base_headers = Interface("base_headers")
    base.add_interface(base_headers)
    base_headers.add_pin("PWMH7", "AREF", base.get_component("U2").get_pin("16").signal)
    base_headers.add_pin("PWMH6", "GND",  base.get_component("U2").get_pin("15").signal)
    base_headers.add_pin("PWMH5", "D13",  base.get_component("U2").get_pin("14").signal)
    base_headers.add_pin("PWMH4", "D12",  base.get_component("U2").get_pin("13").signal)
    base_headers.add_pin("PWMH3", "D11",  base.get_component("U2").get_pin("12").signal)
    base_headers.add_pin("PWMH2", "D10",  base.get_component("U2").get_pin("11").signal)
    base_headers.add_pin("PWMH1", "D9",   base.get_component("U2").get_pin("10").signal)
    base_headers.add_pin("PWMH0", "D8",   base.get_component("U2").get_pin("9").signal)

    base_headers.add_pin("PWML7", "D7",   base.get_component("U2").get_pin("8").signal)
    base_headers.add_pin("PWML6", "D6",   base.get_component("U2").get_pin("7").signal)
    base_headers.add_pin("PWML5", "D5",   base.get_component("U2").get_pin("6").signal)
    base_headers.add_pin("PWML4", "D4",   base.get_component("U2").get_pin("5").signal)
    base_headers.add_pin("PWML3", "D3",   base.get_component("U2").get_pin("4").signal)
    base_headers.add_pin("PWML2", "D2",   base.get_component("U2").get_pin("3").signal)
    base_headers.add_pin("PWML1", "D1",   base.get_component("U2").get_pin("2").signal)
    base_headers.add_pin("PWML0", "D0",   base.get_component("U2").get_pin("1").signal)

    base_headers.add_pin("POWER0", "RST", base.get_component("U2").get_pin("30").signal)
    base_headers.add_pin("POWER1", "3V3", base.get_component("U2").get_pin("29").signal)
    base_headers.add_pin("POWER2", "5V",  base.get_component("U2").get_pin("28").signal)
    base_headers.add_pin("POWER3", "GND", base.get_component("U2").get_pin("27").signal)
    base_headers.add_pin("POWER4", "GND", base.get_component("U2").get_pin("26").signal)
    base_headers.add_pin("POWER5", "VIN", base.get_component("U2").get_pin("25").signal)

    base_headers.add_pin("ADCL0", "ADC0", base.get_component("U2").get_pin("19").signal)
    base_headers.add_pin("ADCL1", "ADC1", base.get_component("U2").get_pin("20").signal)
    base_headers.add_pin("ADCL2", "ADC2", base.get_component("U2").get_pin("21").signal)
    base_headers.add_pin("ADCL3", "ADC3", base.get_component("U2").get_pin("22").signal)
    base_headers.add_pin("ADCL4", "ADC4", base.get_component("U2").get_pin("23").signal)
    base_headers.add_pin("ADCL5", "ADC5", base.get_component("U2").get_pin("24").signal)
    base_headers.add_pin("ADCL6", "ADC6", base.get_component("U2").get_pin("32").signal)
    base_headers.add_pin("ADCL7", "ADC7", base.get_component("U2").get_pin("31").signal)

    base_headers.connect(mega_headers)

    # Dump the whole thing to stdout
    Dump(my_system)


if __name__ == "__main__":
    main()
