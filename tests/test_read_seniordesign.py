#!/usr/bin/python3

from explorer import *

def test_main():

    # Create system
    my_system = System()

    # Read the netlist of the seniordesign board
    seniordesign = read_orcad('tests/seniordesign')
    seniordesign.identifier = "seniordesign"
    my_system.add_board(seniordesign)
