import re
from dataclasses import dataclass
from functools import wraps
from inspect import Parameter, signature
from typing import Callable, Optional


def command(container=False):
    def command_decorator(method):
        @wraps(method)
        def wrapper(self, *args):
            if method.subcmds:
                # Parse the command line as subcommand + args.
                try:
                    subcmd, args = args[0], args[1:]
                # No subcommand was specified.
                except IndexError:
                    # If the command is just a container, calling it is an error.
                    # Otherwise, keep going and try to call the command.
                    if container:
                        return self._method_help(method)
                # Found a candidate subcommand.
                else:
                    if subcmd not in method.subcmds:
                        return self._method_help(method, "Unknown subcommand.")
                    return method.subcmds[subcmd](self, *args)
            # Try to call the command.
            try:
                return method(self, *args)
            except TypeError as e:
                msg = get_unknown_syntax_message(method, e)
                if not msg:
                    raise
                return self._method_help(method, msg)

        # Flag this method as a command.
        wrapper.cmd = True
        # Whether the command is executable on its own, or is just a container.
        wrapper.executable = not container
        # Initialize a empty dictionary of subcommands.
        wrapper.subcmds = method.subcmds = {}
        # Copy the `args` attribute from the wrapped method.
        wrapper.args = getattr(method, "args", [])
        return wrapper

    return command_decorator


@dataclass
class Argument:
    name: str
    has_default: bool
    completion: Optional[Callable]

    def __str__(self):
        return ("[{}]" if self.has_default else "{}").format(self.name.upper())


def argument(name, completion=None):
    def wrapper(method):
        args = getattr(method, "args", [])
        has_default = signature(method).parameters[name].default is not Parameter.empty
        args.insert(0, Argument(name, has_default, completion))
        method.args = args
        return method

    return wrapper


def get_unknown_syntax_message(method, exception) -> Optional[str]:
    more = re.match(
        r"{}\(\) takes (\d+) positional arguments but (\d+) were given".format(
            method.__name__
        ),
        exception.args[0],
    )
    less = re.match(
        r"{}\(\) missing (\d+) required positional arguments?: (.*)".format(
            method.__name__
        ),
        exception.args[0],
    )
    if more or less:
        name = " ".join(method.__name__.split("_")[1:])

    if more:
        required, given = int(more.group(1)), int(more.group(2))
        return '"{}" takes {} positional arguments but {} were given.'.format(
            name, required - 1, given - 1
        )
    elif less:
        missing = int(less.group(1))
        return '"{}" missing {} required positional argument(s).'.format(name, missing)

    return None
