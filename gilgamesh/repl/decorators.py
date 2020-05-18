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
                    try:
                        return method.subcmds[subcmd](self, *args)
                    except KeyError:
                        return self._method_help(method, error=True)
            # Try to call the command.
            # try:
            return method(self, *args)
            # except TypeError:
            #    return self._method_help(method, error=True)

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
