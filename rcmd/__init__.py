# -*- coding: utf-8 -*-
from __future__ import print_function
import collections
import functools
import string
import sys
import re

__all__ = ("Rcmd",)

PROMPT = "(Rcmd) "
PY2 = sys.version_info[0] == 2

class OrderedDefaultDict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultDict, self).__init__(*args, **kwargs)

    def __missing__ (self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default

    def __reduce__(self):  # optional, for pickle support
        args = (self.default_factory,) if self.default_factory else tuple()
        return self.__class__, args, None, None, self.iteritems()

def noop(*args, **kwargs):
    """ THIS METHOD INTENTIONALLY LEFT BLANK.
    """
    pass

class Rcmd(object):
    handlers = OrderedDefaultDict(list)
    def __init__(self, module=None, prompt=None, stdin=None, stdout=None):
        """ TODO: document.
        """
        self.module = module
        if prompt is not None:
            self.prompt = prompt
        else:
            self.prompt = PROMPT
        if stdin is not None:
            self.stdin = stdin
        else:
            self.stdin = sys.stdin
        if stdout is not None:
            self.stdout = stdout
        else:
            self.stdout = sys.stdout
        if PY2:
            self.inputter = raw_input
        else:
            self.inputter = input
        # Junk we need in our loop.
        self.use_rawinput = True
        self.intro = None
        self.lastcmd = ""
        self.identchars = string.ascii_letters + string.digits + "_"
        # Register our handy decorator registrars.
        self.emptyline = self.registrar("_emptyline")
        self.default = self.registrar("_default")
        self.bang = self.register_parenless(r"!")
        self.precmd = self.registrar("_precmd")
        self.postcmd = self.registrar("_postcmd")
        self.preloop = self.registrar("_preloop")
        self.postloop = self.registrar("_postloop")
        # Setup our defaults where required.
        self.bang(noop)
        def _default(line):
            self.stdout.write("*** Unknown syntax: {0}\n".format(line))
        self.default(_default)
        self.precmd(lambda line: line)
        self.postcmd(lambda stop, results, line: stop)

    def register_parenless(self, regex):
        """ Allows registration of 'simple' handlers - e.g.
            `@r.emptyline`, which can be used to register a handler
            without having to use parenthesis.

            Simply a thin wrapper around `r.command`.
        """
        def outer(f):
            return self.command(regex)(f)
        return outer

    def registrar(self, handler):
        """ TODO: document.

            Differs from @r.command in that it's just a simple decorator,
            no regexes are involved - it just places the registered func
            on the instance.

            Lets you do stuff like this:
            >>> r.precmd = r.registrar("_precmd")
            # ... some time later ...
            >>> @r.precmd
            ... def precmd(*a, **k):
            ...    pass
            >>> r._precmd()
        """
        if not hasattr(self, handler):
            setattr(self, handler, noop)
        def outer(f):
            setattr(self, handler, f)
            return f
        return outer

    def command(self, regex, direct=False, override=True, with_cmd=False):
        """ Registers a command handler by appending the registered
            function and regex to `r.handlers`, and also placing the
            (compiled) regex as an attribute on the registered function.

            NB: If `direct` is not set, the regex will have a caret
            prepended to it to ensure it only matches the start of
            a command.
            NB: If `override` isn't set, you can have *multiple* handlers
            for a single order - they'll be called in order of registration.
            NB: If `with_line` is set, your function will be called: f(args, cmd)
        """
        if not direct and len(regex) > 0 and regex[0] != "^":
            regex = "^{0}".format(regex)
        def outer(f):
            reg = re.compile(regex)
            if override:
                self.handlers[reg] = [f]
            else:
                self.handlers[reg].append(f)
            if f != noop:
                f.regex = reg
            f.with_cmd = with_cmd
            return f
        return outer

    def unregister(self, regex, direct=False):
        if not direct and len(regex) > 0 and regex[0] != "^":
            regex = "^{0}".format(regex)
        return self.handlers.pop(regex, None) is not None

    def loop(self, intro=None):
        """ TODO as heck.
            See: cmd.Cmd.cmdloop for some (somewhat horrifying) example loops.
        """
        self._preloop()
        if intro is not None:
            self.intro = intro
        if self.intro is not None:
            self.stdout.write(self.intro + "\n")
            self.stdout.flush()
        stop = None
        while not stop:
            if self.use_rawinput:
                try:
                    line = self.inputter(self.prompt)
                except EOFError:
                    line = "EOF"
            else:
                self.stdout.write(self.prompt)
                self.stdout.flush()
                line = self.stdin.readline()
                if not len(line):
                    line = "EOF"
                else:
                    line = line.rstrip("\r\n")
            line = self._precmd(line)
            stop, results = self.onecmd(line)
            stop = self._postcmd(stop, results, line)
        self._postloop()

    def parseline(self, line):
        """ Parse the line into the command name and a list of the remaining
            arguments (rest.split()). Returns a tuple (cmd, args, line)
            `cmd` and `args` may be None if the line couldn't be parsed.

            Modeled off of Python's `cmd.Cmd.parseline`.
        """
        line = line.strip()
        if not line:
            return None, None, line
        split = line.strip().split()
        cmd, args = split[0], split[1:]
        return cmd, args, line

    def onecmd(self, line):
        """ TODO: clean up and document this behemoth.

            Returns a tuple of (stop, results) - results may be None
            if no function handlers matched the command.
        """
        cmd, args, line = self.parseline(line)
        if not line:
            return self._emptyline(), None
        if cmd is None:
            return self._default(line), None
        self.lastcmd = line
        if line == "EOF":
            self.lastcmd = ""
            return True, None
        if cmd == "":
            return self._default(line), None
        matches = None
        for regex, funcs in self.handlers.items():
            if not regex.findall(cmd):
                continue
            matches = funcs
        if matches:
            results = []
            for func in matches:
                if func.with_cmd:
                    results.append(func(args, cmd))
                else:
                    results.append(func(args))
            return any(results), results
        return self._default(line), None
