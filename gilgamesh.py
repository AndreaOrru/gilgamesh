#!/usr/bin/env python3
"""Gilgamesh, the definitive reverse engineering tool for SNES."""

import sys

from gilgamesh.database import Database
from gilgamesh.prompt import Prompt
from gilgamesh.rom import ROM


if __name__ == '__main__':
    # TODO: Use argparse.

    database = Database(sys.argv[1])
    rom = ROM(sys.argv[2])
    prompt = Prompt(database, rom)
    prompt.run()
