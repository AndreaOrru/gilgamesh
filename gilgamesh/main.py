#!/usr/bin/env python

import click


@click.command()
@click.argument("rom", type=click.Path(exists=True))
def run(rom: str):
    print("Hello, world!")


if __name__ == "__main__":
    run()
