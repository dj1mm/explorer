

import re
from itertools import groupby

from explorer.models import *

def split_line_into_tokens(line):
    """
    Given a line like this:

    ```
    line = 'Abcd EFGHI         Klmn 1 23456789'
    ```

    Split the line into words (seperated by spaces).
    Return a tuple containing the
    - starting position
    - finish position
    - and the word itself (but trimmed)

    In our example, function must return something like this:

    ```
    >>> list(split_lines_into_tokens(line))
    [(0, 4, 'Abcd'), (5, 18, 'EFGHI'), (19, 23, 'Klmn'), (24, 25, '1'), (26, 33, '23456789')]
    ```

    """
    temp = None
    for k, g in groupby(enumerate(line.strip()), lambda x: not x[1].isspace()):
        if k:
            pos, first_item = next(g)
            if temp is not None:
                yield (temp[0], pos-1, temp[1])
            temp = (pos, first_item + ''.join([x for _, x in g]))
    yield (temp[0], len(line)-1, temp[1])

def lookahead(it):
    """
    Is the current value of the iterable, the last value? Use this function.

    ```
    >>> for i, last in lookahead(range(3)):
    ...     print(i, last)
    0 False
    1 False
    2 True
    ```

    """
    it = iter(it)
    last = next(it)
    for val in it:
        yield last, False
        last = val
    yield last, True

def parse_eagle_9_6_2_report_table(lines, keys):
    """
    Parse Eagle 9.6.2 reports that look something like this:

    ```
    Part     Pad      Pin        Dir      Net

    0        A        A          pas      USR_LED0
             C        C          pas      N$47

    5VREG    1        VIN        in       N$79
             2        OUT        pwr      N$16
             3        FB         pwr      5.0V
             4        SD         in       GND
    ```

    Note key header must already have been parsed
    """

    vals = []
    for line in lines:
        line = line.rstrip()
        if line == '':
            continue

        values = []
        begin = 0
        # Remember key is a tuple similar to this: (9, 18, 'Pad')
        for key, last in lookahead(keys):
            end = begin + key[1] - key[0]
            if begin >= len(line):
                values.append('') 
            elif last or end >= len(line):
                values.append(line[begin:len(line)].strip())
            elif line[end].isspace():
                values.append(line[begin:end].strip())
            elif not line[end].isspace():
                value = line[begin:end].strip()
                extra = 0
                for char in line[end:]:
                    if char.isspace():
                        break
                    value += char
                    extra += 1
                end += extra
                values.append(value.strip())
            else:
                raise ValueError("not supposed to be here")
            begin = end + 1
        vals.append(dict(zip((key[2] for key in keys), values)))

    return vals

class Parser:
    """
    Parse eagle reports and populate an explorer Board object with content of
    the report.
    
    Generate reports by doing File -> Export -> (Netlist | Partlist | Pinlist)

    """

    def __init__(self):
        self.board = Board()
        self.keys = []
        self.vals = []

    def __call__(self, file):
        lines = (line for line in file)

        # Parse preambule, summary and the misc things before the actual table
        line = next(lines)
        filetype = line.strip()

        version = ''
        for line in lines:
            if re.match(r'(\w+\s{3,}){2,}', line):
                self.keys = [token for token in split_line_into_tokens(line)]
                break
            match = re.match(r'EAGLE Version ([\d.]+)', line)
            if match:
                version = match.groups()[0]
            match = re.match(r'Exported from ([a-zA-Z0-9.]+).(sch|brd) at', line)
            if match and match.groups()[1] != 'sch':
                raise ValueError("Reports must be generated from an eagle schematic")
            elif match:
                self.board.name = match.groups()[0]

        if self.board.name == '':
            raise ValueError("Eagle report seems to be invalid")

        if version != '9.6.2':
            raise ValueError("Unsupported eagle file version")

        self.vals = parse_eagle_9_6_2_report_table(lines, self.keys)
        if filetype == 'Netlist':
            self.parse_netlist_file()
        elif filetype == 'Pinlist':
            self.parse_pinlist_file()
        elif filetype == 'Partlist':
            self.parse_partlist_file()
        else:
            raise ValueError("how are we here again?")

    def parse_netlist_file(self):
        net = None
        for val in self.vals:
            if (set(['Net', 'Part', 'Pad']) - val.keys()):
                raise ValueError("Invalid pinlist file")

            if (val['Net'] != ''):
                net = Wire(val['Net'])
                self.board.add_wire(net)

            net.connect(self.board.get_component(val['Part']).get_pin(val['Pad']))

    def parse_pinlist_file(self):
        comp = None

        for val in self.vals:
            if (set(['Part', 'Pad', 'Pin', 'Net']) - val.keys()):
                raise ValueError("Invalid pinlist file")

            if (val['Part'] != '' or comp == None):
                comp = self.board.get_component(val['Part'])

            pin = Pin(val['Pad'], val['Pin'], comp)
            comp.add_pin(pin)

            if val['Net'] == '*** unconnected ***':
                try:
                    nc = self.board.get_wire('NC')
                except:
                    nc = Wire('NC')
                    nc.type = WireType.NC
                    self.board.add_wire(nc)
                nc.connect(comp.get_pin(val['Pad']))


    def parse_partlist_file(self):
        for val in self.vals:
            if (set(['Part', 'Value', 'Device', 'Package']) - val.keys()):
                raise ValueError("Invalid partlist file")

            comp = Component(val['Part'], val['Package'], val['Device'], val['Value'])
            self.board.add_component(comp)

def read_eagle(nets: str, pins: str, parts: str):
    """
    Read eagle report files and populate a board object
    """
    parse = Parser()

    with open(parts, 'r') as f:
        try:
            parse(f)
        except (ValueError) as e:
            print(f"Error parsing {parts}: {str(e)}")
            return Board()

    with open(pins, 'r') as f:
        try:
            parse(f)
        except (ValueError) as e:
            print(f"Error parsing {pins}: {str(e)}")
            return Board()

    with open(nets, 'r') as f:
        try:
            parse(f)
        except (ValueError) as e:
            print(f"Error parsing {nets}: {str(e)}")
            return Board()

    return parse.board

