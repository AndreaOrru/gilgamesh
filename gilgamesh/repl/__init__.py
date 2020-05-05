from collections import OrderedDict
from inspect import getmembers, isfunction
from typing import Any, Callable, Dict

from cached_property import cached_property  # type: ignore
from dictlib import dug  # type: ignore
from prompt_toolkit import HTML, PromptSession  # type: ignore
from prompt_toolkit.completion import NestedCompleter  # type: ignore
from prompt_toolkit.shortcuts import CompleteStyle, clear  # type: ignore

from gilgamesh.repl.colors import print_error, print_html, style  # noqa
from gilgamesh.repl.completers import ArgsCompleter
from gilgamesh.repl.decorators import argument, command  # noqa


class Repl:
    def __init__(self):
        self._session = PromptSession(
            style=style,
            complete_style=CompleteStyle.MULTI_COLUMN,
            complete_while_typing=False,
        )
        self._commands = self._build_commands()
        self._completer = self._build_completer()

    @property
    def prompt(self) -> str:
        return HTML("<yellow>" + "> " + "</yellow>")

    def run(self) -> None:
        while True:
            try:
                tokens = (
                    self._session.prompt(self.prompt, completer=self._completer)
                    .strip()
                    .split()
                )
            except EOFError:
                break
            except KeyboardInterrupt:
                continue
            if not tokens:
                continue

            try:
                cmd, args = self._commands[tokens[0]], tokens[1:]
            except KeyError:
                self.do_help()
            else:
                if cmd(self, *args):
                    return

    @command
    def do_help(self, *parts) -> None:
        """Show help on commands."""
        if len(parts) == 0:
            return self._help_list(self._commands)

        try:
            cmd = self._all_commands[".".join(parts)]
        except KeyError:
            return self.do_help()

        if cmd.subcmds:
            self._help_usage(*[*parts, "SUBCOMMAND"])
            print("{}\n".format(cmd.__doc__ or ""))
            self._help_list(cmd.subcmds, "Subcommands")
        else:
            self._help_usage(*[*parts, *[arg[0].upper() for arg in cmd.args]])
            print("{}\n".format(cmd.__doc__ or ""))

    @command
    def do_clear(self) -> None:
        """Clear the screen."""
        clear()

    @command
    def do_quit(self) -> bool:
        """Quit the application."""
        return True

    @cached_property
    def _all_commands(self) -> Dict[str, Callable]:
        # Get a dictionary from command names to commands (methods).
        # Methods tagged with the attribute `cmd` are considered
        # commands. Commands are expected to begin with `do_`.
        # Subcommands are defined by using underscores.
        # We return an `OrderedDict` so that parent commands always
        # come before their children.
        # We use "." to define the hierarchy so that we can later make
        # use of `dug` from `dictlib` to access nested dictionaries.
        #
        # Example "input":
        #   { do_list(), do_list_subroutines() }
        # Example "output":
        #   { 'list': do_list(), 'list.subroutines': do_list_subroutines() }
        #
        return OrderedDict(
            sorted(
                (
                    (x[0].split("_", 1)[1].replace("_", "."), x[1])
                    for x in getmembers(self.__class__, isfunction)
                    if getattr(x[1], "cmd", False)
                )
            )
        )

    def _build_commands(self) -> Dict[str, Callable]:
        # Build the hierarchy of commands.
        #
        # Example "input":
        #   { 'list': do_list(), 'list.subroutines': do_list_subroutines() }
        # Example "output":
        #   { 'list': do_list() -> .subcmds = { 'subroutines': do_list_subroutines() } }
        #
        commands: Dict[str, Any] = {}
        for name, cmd in self._all_commands.items():
            try:
                # Subcommand. Add it to the parent command.
                parts = name.split(".")
                parent = self._all_commands[".".join(parts[:-1])]
                parent.subcmds[parts[-1]] = cmd
            except KeyError:
                # Simple command.
                commands[name] = cmd
        return commands

    def _build_completer(self) -> NestedCompleter:
        def completer(cmd):
            # Build a completer for a command.
            if not cmd.args:
                return {}
            return ArgsCompleter(self, [arg[1] for arg in cmd.args])

        # Build a nested completion dictionary for commands and subcommands.
        completer_dict: Dict[str, Any] = {}
        for name, cmd in self._all_commands.items():
            dug(completer_dict, name, completer(cmd))

        # Define completions for all the help commands.
        for name in self._all_commands:
            dug(completer_dict, f"help.{name}", {})

        return NestedCompleter.from_nested_dict(completer_dict)

    def _method_help(self, method) -> None:
        return self.do_help(*method.__name__.split("_")[1:])

    @staticmethod
    def _help_list(commands: Dict[str, Any], header="Commands") -> None:
        s = f"<yellow>{header}</yellow>:\n"
        for name, cmd in commands.items():
            name += "..." if cmd.subcmds else ""
            s += "  <green>{:15}</green>{}\n".format(name, cmd.__doc__ or "")
        print_html(s)

    @staticmethod
    def _help_usage(*parts) -> None:
        if parts[0] == "help":
            parts = ("help", "[COMMAND [SUBCOMMAND]...]")

        print_html(
            "<yellow>Usage:</yellow> <green>{}</green>\n".format(" ".join(parts))
        )
