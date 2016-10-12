#!/usr/bin/env python3
"""Gilgamesh, the definitive reverse engineering tool for SNES."""

import sys

from gilgamesh.analyzer import Analyzer
from gilgamesh.database import Database
from gilgamesh.prompt import Prompt
from gilgamesh.rom import ROM


if __name__ == '__main__':
    # TODO: Use argparse/click.

    database = Database(sys.argv[1])
    rom = ROM(sys.argv[2])

    analyzer = Analyzer(database)
    prompt = Prompt(analyzer, rom)

    prompt.run()
