#!/usr/bin/env python

import click

from gilgamesh.app import App


@click.command()
@click.argument("rom", type=click.Path(exists=True))
def run(rom: str):
    app = App(rom)
    app.run()


if __name__ == "__main__":
    run(prog_name="gilgamesh")
