#!/usr/bin/python3

from __future__ import annotations

from explorer import *

def test_main():
    base = read_eagle('tests/base/base.nets', 'tests/base/base.pins', 'tests/base/base.parts')
    base.refdes = "base"

    my_system = System()
    my_system.add_board(base)

    # Verify the generated model

    assert base.name == "base"
    assert base.refdes == "base"
    assert len(base._components) == 24
    assert len(base._signals) == 31 + 1
    assert len(base._interfaces) == 0
    assert len(base._dummypins) == 0

    # import io
    # from contextlib import redirect_stdout
    # with open('outputfile.out','w') as f:
    #     with io.StringIO() as buf, redirect_stdout(buf):
    #         Dump(my_system)
    #         output = buf.getvalue()
    #         f.write(output)



