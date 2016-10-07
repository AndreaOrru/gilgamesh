from abc import ABC, abstractmethod


class CodeGenerator(ABC):
    def __init__(self, db):
        self._db = db

    @abstractmethod
    def compile(self):
        pass
