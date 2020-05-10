from abc import ABC
from typing import Iterable


class InvalidObjectError(Exception):
    ...


class Invalidable(ABC):
    def __init__(self):
        self._valid = True
        self._repr = None

    def __getattribute__(self, name: str):
        if name in ("_valid", "_repr") or self._valid:
            return super().__getattribute__(name)
        else:
            raise InvalidObjectError(self._repr)

    def invalidate(self) -> None:
        self._repr = repr(self)
        self._valid = False


def bulk_invalidate(iterable: Iterable):
    for obj in iterable:
        obj.invalidate()
