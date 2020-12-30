#!/usr/bin/python3

from explorer import *

def test_main():

    # Create system
    my_system = System()

    # Read the netlist of the watersensor board
    watersensor = read_allegro('tests/watersensor')
    watersensor.refdes = "watersensor"
    my_system.add_board(watersensor)
