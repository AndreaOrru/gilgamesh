from functools import wraps


def command(method):
    @wraps(method)
    def wrapper(self, *args):
        if method.subcmds:
            try:
                subcmd, args = args[0], args[1:]
            except IndexError:
                return self._method_help(method)
            else:
                return method.subcmds[subcmd](self, *args)
        try:
            return method(self, *args)
        except TypeError:
            return self._method_help(method)

    # Flag this method as a command.
    wrapper.cmd = True
    # Initialize a empty dictionary of subcommands.
    wrapper.subcmds = method.subcmds = {}
    # Copy the `args` attribute from the wrapped method.
    wrapper.args = getattr(method, "args", [])
    return wrapper


def argument(name, completion=None):
    def wrapper(method):
        args = getattr(method, "args", [])
        args.insert(0, (name, completion))
        method.args = args
        return method

    return wrapper
