# Magic encoding based rewriter

Inspired by https://github.com/asottile/future-fstrings

Allows a relativly easily manipualation of file contents before the interpreter parses it and so allows one to implement
new syntax structures.

## How to use

You need the package `rewrite_magic` in your python path, as well as a `sitecustomize.py` or `usercustomize.py` file
containing content like the file in `src` directory.

On way to achieve this is to use `pip install -e .` inside of this directory. Alternatively, Just installing the package
and manually adding a `sitecustomize.py` somewhere should also work.

If you can't add a `sitecustomize.py` somewhere, you can also create a `main` wrapper that first activates the rewriter
and then imports the actual main module.

Whichever option you choose, if you now add a line of the form

```
# -*- coding: rewrite-{rewriter-names} -*-
```

as the first or second line in a file, the package should now try to transform the file before it is interpreter.

`rewriter-names` should be a dash separated list of names as listed below, or with whatever rewriter you write yourself.

## Existing rewriter

### fstringbackport

Allows `f"{expr=}"` (e.g. debug `=`) f-strings in python3.6. Does not work for earlier python versions, since this
doesn't contain an actual f-string implementation, only the expression transformation (at the moment.)

## How to create your own

If you want to create your own rewriters, the easiest way is to create a new sub module of `rewrite_magic`, containing a
subclass of `FileRewriter` and a call to `rewrite_magic.encoding_glue.register`. As long as you use the same name for
the module and the encoding, the module will be automatically imported when a rewriter with that name is requested.