rcmd.py
=======

Sort of like Python's built in "cmd" module, but with regex handlers.

## Example usage

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
