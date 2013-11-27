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

@r.bang
def bang(args):
    # Called when the user types "! [stuff]".
    # Convenience since this is a handy addition.
    pass

@r.question
def question(args):
    # Called when the user types "? [stuff]"
    # Convenience since this is a handy addition.
    pass

@r.precmd
def precmd(line):
    # Allows you to modify a line before it passes through
    # the parser and matchers.
    return line

@r.postcmd
def postcmd(stop, results, line):
    # `stop` -> truthy values mean we'll stop next loop.
    # `results` -> list of results any matching commands returned
    # `line` -> the line the user entered
    return stop, results

@r.preloop
def preloop():
    # Called before the initial command loop starts.
    pass

@r.postloop
def postloop():
    # Called after the command loop finishes.
    pass
```