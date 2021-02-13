
from jinja2 import FileSystemLoader, Environment
from pathlib import Path
import hashlib
import os

from explorer.models import *

class State:
    connectivity_index = 1

class Report:
    pass

class Connectivity(Report):
    def __init__(self, starting, to, title = None) -> None:
        if title is None:
            self.title = f"Connectivity report {State.connectivity_index}"
            State.connectivity_index += 1
        else:
            self.title = title
        self.id = hashlib.md5(self.title.encode('utf-8')).hexdigest()

        self.starting: Board | Component = starting
        self.to: list[Board | Component] = to

    def __call__(self, env, netlist, system) -> str:
        template = env.get_template("write_html_connectivity_template.jinja2")
        return template.render(title=self.title, starting=self.starting, to=self.to, netlist=netlist,system=system)

def write_html(system: System, *args, **kwargs):
    """
    write_html(system, ...)

    Write html report of the system.

    Parameters
    ----------
    system: System - required
        The system in question. Write an html report of the system.
    folder: str, positional or named, default: 'out/'
        The folder where to write the html report.
    extra: list[Report], named, default: []
        List of additional reports that are required
    """

    if len(args) == 1 and 'folder' in kwargs:
        raise TypeError('write_html() got multiple values for argument \'folder\'.')
    if len(args) > 1 or any(x not in {'folder', 'extra'} for x in kwargs):
        raise TypeError('Unknown usage of write_html()')

    # Default values
    folder = args[0] if len(args) == 1 else kwargs.get('folder', 'out')
    if not isinstance(folder, str):
        raise TypeError("folder must be a string")

    extra = kwargs.get('extra', [])
    if all(isinstance(x, Report) for x in extra) is False:
        raise TypeError("write_html() only supports extra reports")

    # look for files in the directory where write_html.py lives
    loader = FileSystemLoader(str(Path(__file__).parent)) # seems wsl need this
    env = Environment(loader=loader)

    netlist = Netlist(system)

    file = f'{folder}/index.html'
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w") as f:
        template = env.get_template("write_html_system_template.jinja2")
        f.write(template.render(system=system, extra=extra))

    for brd in system.boards:
        file = f'{folder}/{brd.identifier}.html'
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            template = env.get_template("write_html_board_template.jinja2")
            f.write(template.render(board=brd, netlist=netlist))

    for rtl in system.rtls:
        file = f'{folder}/{rtl.name}.html'
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            template = env.get_template("write_html_rtl_template.jinja2")
            f.write(template.render(rtl=rtl, netlist=netlist))

    for x in extra:
        file = f'{folder}/connectivity-{x.id}.html'
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            f.write(x(env, netlist, system))

