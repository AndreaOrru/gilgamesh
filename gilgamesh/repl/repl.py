from collections import OrderedDict
from inspect import getdoc, getmembers, isfunction
from os import makedirs
from os.path import dirname, expanduser
from shlex import split
from typing import Any, Callable, Dict

from cached_property import cached_property  # type: ignore
from dictlib import dug  # type: ignore
from prompt_toolkit import HTML, PromptSession, prompt  # type: ignore
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory  # type: ignore
from prompt_toolkit.completion import NestedCompleter  # type: ignore
from prompt_toolkit.history import FileHistory  # type: ignore
from prompt_toolkit.shortcuts import CompleteStyle, clear  # type: ignore

from gilgamesh.repl.colors import print_error, print_html, style
from gilgamesh.repl.completers import ArgsCompleter
from gilgamesh.repl.decorators import command


class Repl:
    def __init__(self, history_file=""):
        if history_file:
            history_file = expanduser(history_file)
            makedirs(dirname(history_file), exist_ok=True)

        self._session = PromptSession(
            style=style,
            swap_light_and_dark_colors=True,
            complete_style=CompleteStyle.MULTI_COLUMN,
            complete_while_typing=False,
            history=history_file and FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
        )
        self._commands = self._build_commands()
        self._completer = self._build_completer()

    @property
    def prompt(self) -> str:
        return HTML("<yellow>" + "> " + "</yellow>")

    def run(self) -> None:
        close = False
        while not close:
            # Take commands through the prompt.
            try:
                tokens = split(
                    self._session.prompt(self.prompt, completer=self._completer).strip()
                )
            # If Ctrl-D, get out.
            except EOFError:
                close = True
            # If Ctrl-C, abort the current command insertion.
            except KeyboardInterrupt:
                continue
            else:
                if tokens:
                    # Parse the command.
                    try:
                        cmd, args = self._commands[tokens[0]], tokens[1:]
                    # Couldn't parse, show help.
                    except KeyError:
                        self.do_help()
                    # Execute the command.
                    else:
                        # Commands can return True to quit the application.
                        if cmd(self, *args):
                            close = True

            # Ask for confirmation when quitting.
            if close and not self.yes_no_prompt(
                "Are you sure you want to quit without saving?"
            ):
                close = False
        print()

    @command()
    def do_help(self, *parts) -> None:
        """Show help on commands."""
        if len(parts) == 0:
            return self._help_list(self._commands, error=True)  # Generic help.

        # Retrieve the command.
        try:
            cmd = self._all_commands[".".join(parts)]
        except KeyError:
            # Command not found, show generic help.
            return self.do_help()

        if cmd.subcmds:
            # The command has subcommands, show an outline of all the possible ones.
            subcommand = "[SUBCOMMAND]" if cmd.executable else "SUBCOMMAND"
            self._help_usage(*[*parts, subcommand])
            print("{}\n".format(getdoc(cmd) or ""))
            self._help_list(cmd.subcmds, "Subcommands")
        else:
            # This is a "leaf" command, show info on its usage.
            self._help_usage(*[*parts, *map(str, cmd.args)])
            print("{}\n".format(getdoc(cmd) or ""))

    @command()
    def do_clear(self) -> None:
        """Clear the screen."""
        clear()

    @command()
    def do_quit(self) -> bool:
        """Quit the application."""
        return True

    def yes_no_prompt(self, question: str) -> bool:
        answer = prompt(HTML(f"<yellow>{question} (y/n) </yellow>"), style=style)
        if answer == "y":
            return True
        else:
            print()
            return False

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
            return ArgsCompleter(self, [arg.completion for arg in cmd.args])

        # Build a nested completion dictionary for commands and subcommands.
        completer_dict: Dict[str, Any] = {}
        for name, cmd in self._all_commands.items():
            dug(completer_dict, name, completer(cmd))

        # Define completions for all the help commands.
        for name in self._all_commands:
            dug(completer_dict, f"help.{name}", {})

        return NestedCompleter.from_nested_dict(completer_dict)

    def _method_help(self, method, error=False) -> None:
        # Unpack the method in its components (i.e 'list', 'subroutines')
        # and invoke the actual help method.
        parts = method.__name__.split("_")[1:]
        self.do_help(*parts)
        if error:
            print_error("Unknown syntax.")

    @staticmethod
    def _help_list(commands: Dict[str, Any], header="Commands", error=False) -> None:
        # Print help for a collection of commands.
        s = f"<yellow>{header}:</yellow>\n"
        for name, cmd in commands.items():
            name += "..." if cmd.subcmds else ""
            doc = (getdoc(cmd) or "").split("\n")[0]
            s += "  <green>{:15}</green>{}\n".format(name, doc)
        print_html(s)
        if error:
            print_error("Unknown syntax.")

    @staticmethod
    def _help_usage(*parts) -> None:
        # Print usage info on a command.
        if parts[0] == "help":
            # Special case for `help` itself.
            parts = ("help", "[COMMAND [SUBCOMMAND...]]")

        print_html(
            "<yellow>Usage:</yellow> <green>{}</green>\n".format(" ".join(parts))
        )
