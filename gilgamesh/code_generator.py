from abc import ABC, abstractmethod


class CodeGenerator(ABC):
    def __init__(self, analyzer, rom):
        self._analyzer = analyzer
        self._rom = rom

    @abstractmethod
    def compile(self):
        pass
