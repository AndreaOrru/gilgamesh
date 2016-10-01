#!/usr/bin/env python3
"""Gilgamesh, the definitive reverse engineering tool for SNES."""

import sqlite3
import sys

from instruction import Instruction


if __name__ == '__main__':
    db = sqlite3.connect(sys.argv[1])
    db.row_factory = sqlite3.Row
    c = db.cursor()

    instructions = c.execute('SELECT * FROM instructions')
    for instruction in map(Instruction.from_row, instructions):
        print(instruction)
