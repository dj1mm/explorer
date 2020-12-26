
from jinja2 import FileSystemLoader, Environment
from pathlib import Path
import os

from explorer.models import *


def write_html(system: System, folder: str):

    # look for files in the directory where write_html.py lives
    loader = FileSystemLoader(Path(__file__).parent)
    env = Environment(loader=loader)

    sigmap = SignalMap(system)

    file = f'{folder}/index.html'
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w") as f:
        template = env.get_template("write_html_system_template.jinja2")
        f.write(template.render(system=system))

    for brd in system.boards:
        file = f'{folder}/{brd.refdes}.html'
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            template = env.get_template("write_html_board_template.jinja2")
            f.write(template.render(board=brd, sigmap=sigmap))


