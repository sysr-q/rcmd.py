rcmd.py
=======

Sort of like Python's built in "cmd" module, but with regex handlers.

## Basic usage

```python
# -*- coding: utf-8 -*-
from rcmd import Rcmd

r = Rcmd(__name__)

# Note: this will match "foo!", and "foober" - use "foo$" if you want
# to avoid this sort of stuff. Regexes are like that, yeah?
@r.command(r"foo")
def foo(args):
    print("Foo!")

@r.command(r"\d+!", with_cmd=True)
def fact(args, cmd):
    print(cmd[:-1] + "?")

r.loop()
```

## Registering various handlers

Rcmd has a few handlers you can override (through decorators, of course!).

```python
@r.emptyline
def emptyline():
    # Called when the user doesn't type anything.
    pass

@r.default
def default(line):
    # Called when nothing matches the user's line.
    pass

@r.precmd
def precmd(line):
    # Allows you to modify a line before it passes through
    # the parser and matchers.
    return line.strip()

@r.postcmd
def postcmd(stop, results, line):
    # `stop` -> truthy values mean we'll stop next loop.
    # `results` -> list of results any matching commands returned
    # `line` -> the line the user entered
    return (stop, results)

@r.preloop
def preloop():
    # Called before the initial command loop starts.
    pass

@r.postloop
def postloop():
    # Called after the command loop finishes.
    pass
```

## Example `help` command

This isn't built in because to each his own - you might want different things to me, so here's a basic structure you can work with. Evidently, this one only works if you use the Regex parser.  
This will let people do `help` and `help thing` (with optional `?` alias to help), and prints the `__doc__` of each command handler that _thing_ matches.

```python
import textwrap

@r.command(r"help")
def help(args):
    def tidy_regex(regex):
        return regex.lstrip("^").rstrip("$")

    def create_help(regex, functions, matching=None):
        if matching is not None and not regex.match(matching):
            return None
        out = [">>> {0}".format(tidy_regex(regex.pattern))]
        for i, function in enumerate(functions, 1):
            if function.__doc__:
                out.append(textwrap.dedent(function.__doc__))
            else:
                out.append("{0}. No help provided. :( ({1})".format(i, function.__name__))
            out.append("")
        return "\n".join(out)

    # No arguments provided, just list things.
    if not args or len(args) != 1:
        for regex, functions in r.parser.handlers.iteritems():
            print(create_help(regex, functions))
        return

    # Do a search for matching handlers.
    cmd, matched = args[0], True
    print('"{0}" would run:\n'.format(cmd))
    for regex, functions in r.parser.handlers.iteritems():
        t = create_help(regex, functions, matching=cmd)
        if t is None:
            continue
        matched = True
        print(t)

    if not matched:
        print("nothing :(\n")
```
