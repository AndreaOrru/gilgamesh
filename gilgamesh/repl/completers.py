from functools import partial
from inspect import getfullargspec
from typing import Callable, Iterable, List, Union

from prompt_toolkit.completion import (  # type: ignore
    CompleteEvent,
    Completer,
    WordCompleter,
)
from prompt_toolkit.document import Document  # type: ignore


class ArgsCompleter(Completer):
    def __init__(self, repl, args: List[Union[Iterable[str], Callable, None]]):
        # Bind callables to the instance of Repl, if necessary.
        self.args = [
            partial(arg, repl) if (callable(arg) and getfullargspec(arg).args) else arg
            for arg in args
        ]

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[str]:
        # Get completion choices for the current argument.
        parts = document.text_before_cursor.lstrip().split(" ")
        try:
            completion = self.args[len(parts) - 1]
        except IndexError:
            completion = None
        if completion is None:
            return []

        completer = WordCompleter(completion, ignore_case=True)
        for c in completer.get_completions(document, complete_event):
            yield c
