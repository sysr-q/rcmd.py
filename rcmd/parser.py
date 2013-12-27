# -*- coding: utf-8 -*-
import inspect
import re

def noop(*args, **kwargs):
    pass

class Parser(object):
    def __init__(self, **options):
        # {rule: [f1, f2, ...]}
        # f.options = **options
        self.handlers = {}

    def command(self, rule, **options):
        def handler(f):
            return f
        return handler

    def best_guess(self, line, args=None, kwargs=None, multiple=True, **options):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        matches = []
        return (matches, args, kwargs)

    def unregister(self, rule, **options):
        return False

    def parse(self, line, **options):
        # parsed, args, kwargs
        return (False, (), {})

    def no_args(self, func):
        spec = inspect.getargspec(func)
        return (len(spec.args) == 0
                and spec.varargs is None  # *args
                and spec.keywords is None)  # **kwargs

class Regex(Parser):
    def __init__(self, rank_best=False, **options):
        super(Regex, self).__init__(**options)
        self.rank_best = rank_best

    def command(self, rule, **options):
        """\
        direct=False, override=True, inject=False, flags=0
        """
        options.setdefault("direct", False)
        options.setdefault("override", True)
        options.setdefault("inject", False)
        options.setdefault("flags", 0)
        if not options["direct"]:
            rule = self.regexy(rule)
        regex = re.compile(rule, flags=options["flags"])
        self.handlers.setdefault(regex, [])
        def handler(f):
            if f == noop:
                f.options = {}
            else:
                f.options = options
            if options["override"]:
                self.handlers[regex] = [f]
            else:
                self.handlers[regex].append(f)
            f.no_args = self.no_args(f)
            return f
        return handler

    def best_guess(self, line, args=None, kwargs=None, multiple=True, **options):
        """\
        Given multiple=False, this will simply return the first matching
        regexes first handler; otherwise, this will return a list of all
        the matching handler function(s).

        If rank_best was set on the parser, this will attempt to "rank" the
        regexes, and will return the highest ranked handler(s).

        Returns (matches, args, kwargs) - it's up to the caller to apply these
        and test whether f.options["inject"]/f.no_args is set, etc.
        """
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        matches = []
        for regex, funcs in self.handlers.items():
            if not regex.findall(line):
                continue
            if not multiple:
                return ((funcs[0], args, kwargs)
                         if len(funcs) > 0
                         else (None, args, kwargs))
            matches.append(funcs)
        if self.rank_best:
            # TODO: rank regexes.
            pass
        return (matches, args, kwargs)

    def unregister(self, rule, **options):
        options.setdefault("direct", False)
        options.setdefault("flags", 0)
        if not options["direct"]:
            rule = self.regexy(rule)
        regex = re.compile(rule, flags=options["flags"])
        return self.handlers.pop(regex, None) is not None

    def parse(self, line, **options):
        """\
        Parse a line and return (parsed, args, kwargs)

        Relatively simple in the Regex parser - anything can be "parsed",
        but is not guaranteed to match.
        """
        line = line.strip()
        if not line:
            return (False, (), {})
        split = line.split()
        cmd, args = split[0], split[1:]
        return (True, args, {})

    def regexy(self, r):
        if r[0] != "^":
            r = "^{0}".format(r)
        if r[-1] != "$":
            r = "{0}$".format(r)
        return r

class Rule(Parser):
    """\
    TODO: parse 'rules' like "foo <bar>" to {constants=["foo"], bar=...}.
    """

    def command(self, rule, **options):
        """\
        inject=False
        """
        def handler(f):
            return f
        return handler

    def best_guess(self, line, args=None, kwargs=None, multiple=True, **options):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        matches = []
        return (matches, args, kwargs)

    def unregister(self, rule, **options):
        return False

    def parse(self, line, **options):
        # parsed, args, kwargs
        return (False, (), {})
