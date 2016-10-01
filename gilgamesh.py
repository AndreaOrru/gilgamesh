#!/usr/bin/env python3
"""Gilgamesh, the definitive reverse engineering tool for SNES."""

import sys

from database import Database
from prompt import Prompt


if __name__ == '__main__':
    database = Database(sys.argv[1])
    prompt = Prompt(database)
    prompt.run()
