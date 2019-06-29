#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="gilgamesh",
    version="0.1.0",
    description="The definitive reverse engineering tool for SNES",
    author="Andrea Orru",
    author_email="andrea@orru.io",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=["click", "prompt-toolkit"],
    extras_require={
        "dev": [
            "autoflake",
            "black",
            "epc",
            "flake8",
            "flake8-mypy",
            "importmagic",
            "ipython",
            "isort",
            "pdbpp",
            "virtualenvwrapper",
        ]
    },
)
