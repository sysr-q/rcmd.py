# -*- coding: utf-8 -*-
from __future__ import print_function
import collections
import functools
import inspect
import string
import sys
import re

import rcmd.parser

__all__ = ("Rcmd",)

__version__ = "1.1.1"
PROMPT = "(Rcmd) "
PY2 = sys.version_info[0] == 2
DEFAULT_PARSER = rcmd.parser.Regex

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


class Rcmd(object):
    def __init__(self, module=None, prompt=None, parser=None, stdin=None, stdout=None):
        """ TODO: document.
        """
        if parser is None:
            self.parser = DEFAULT_PARSER()
        else:
            self.parser = parser
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
        self._eof = "\x00\x00"  # any hard to enter string
        self.use_rawinput = True
        self.intro = None
        self.lastcmd = ""
        self.identchars = string.ascii_letters + string.digits + "_"
        # Register decorators and whatnot.
        self.command = self.parser.command
        self.unregister = self.parser.unregister
        self.events = OrderedDefaultDict(list)
        events = ["emptyline", "default", #"bang", "question",
                  "precmd", "postcmd", "preloop", "postloop"]
        for event in events:
            self.easy_handler(event)(rcmd.parser.noop)
        def _default(line):
            self.stdout.write("*** Unknown syntax: {0}\n".format(line))
            self.stdout.flush()
        self.default(_default)
        self.precmd(lambda line: line.strip())
        self.postcmd(lambda stop, results, line: (stop, results))

    def easy_handler(self, event):
        def handler(f):
            self.events[event] = [f]
            return f
        # Where the magic happens.
        setattr(self, event, handler)
        return handler

    def loop(self, intro=None):
        """ TODO as heck.
            See Python's cmd.Cmd.cmdloop for some (somewhat horrifying)
            example loops - that's what we're working similarly to.
        """
        self.fire("preloop")
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
                    line = self._eof
            else:
                self.stdout.write(self.prompt)
                self.stdout.flush()
                line = self.stdin.readline()
                if not len(line):
                    line = self._eof
                else:
                    line = line.rstrip("\r\n")
            line = self.fire("precmd", line)
            stop, results = self.onecmd(line)
            stop, results = self.fire("postcmd", stop, results, line)
        self.fire("postloop")

    def event(self, name):
        def handler(f):
            self.events[name].append(f)
            f._handling = name
            return f
        return handler

    def unevent(self, f):
        if not hasattr(f, "_handling") or not f in self.events[f._handling]:
            return False
        del self.events[f._handling][f]
        return True

    def fire(self, name, *args, **kwargs):
        if len(self.events[name]) == 1:
            return self.events[name][0](*args, **kwargs)
        for event in self.events[name]:
            event(*args, **kwargs)

    def onecmd(self, line):
        if not line:
            return self.fire("emptyline"), None
        if line == self._eof:
            return True, None
        self.lastcmd = line
        matches, args, kwargs = self.parser.best_guess(line)
        if len(matches) == 0:
            return self.fire("default", line), None
        kwargs.setdefault("line", line)
        results = []
        for handlers in matches:
            for function in handlers:
                if function.no_args:
                    results.append(function())
                elif function.options["inject"]:
                    results.append(function(*args, **kwargs))
                else:
                    results.append(function(args))
        return any(results), results
