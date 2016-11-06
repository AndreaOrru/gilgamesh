# pylint: disable=too-few-public-methods
"Interface for code generators."

from abc import ABC
from abc import abstractmethod


class CodeGenerator(ABC):
    """Interface for code generators."""

    def __init__(self, analyzer, rom):
        self._analyzer = analyzer
        self._rom = rom

    @abstractmethod
    def compile(self):
        """Generate the code.

        Returns:
            The compiled code as a string.
        """
        pass
