from abc import ABC, abstractmethod


class CodeGenerator(ABC):
    def __init__(self, db, rom):
        self._db = db
        self._rom = rom

    @abstractmethod
    def compile(self):
        pass
