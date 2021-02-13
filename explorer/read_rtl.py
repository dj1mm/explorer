

from __future__ import annotations
import re

from explorer.models import Rtl

def read_rtl(from_xlnx_io: str):
    """

    read_rtl(from_xlnx_io)

    Read a xilinx io report and return an explorer rtl object. This object can
    then be added into the explorer models.
    """
    return _read_rtl_from_xlnx_io_report(from_xlnx_io)

def _read_rtl_from_xlnx_io_report(io_rpt):
    rtl = Rtl()
    cols = []
    keys = []
    vals = []

    with open(io_rpt, 'r') as file:

        # Parse preambule, summary and the misc things before the actual report
        for line in file:
            if re.match(r'(\+-+){2,}', line):
                p = [pos for pos,char in enumerate(line) if char == '+']
                cols = [(i+1,j-1) for i,j in zip(p[:-1], p[1:])]
                break

        # Parse the actual header
        line = file.readline()
        keys = [line[l:u].strip() for l,u in cols]

        # Parse the +---+---+-- ... --+-----+ delimiting the actual table
        line = file.readline().strip()
        table_delimiter = '+'.join(['', *[('-'*(u-l+1)) for l,u in cols], ''])
        if line != table_delimiter:
            return

        # This is the table
        for line in file:
            if line.strip() == table_delimiter:
                break
            values = [line[l:u].strip() for l,u in cols]
            vals.append(dict(zip(keys, values)))

        # Any postamble? Parse em here
        for line in file:
            pass

    for value in vals:
        if 'Signal Name' not in value or 'Pin Number' not in value:
            continue
        sig = value['Signal Name']
        loc = value['Pin Number']
        if sig == '' or loc == '':
            continue
        rtl.add_signal(sig, loc)

    return rtl

