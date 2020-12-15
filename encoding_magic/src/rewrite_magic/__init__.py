def activate():
    from rewrite_magic.encoding_glue import _finder
    import codecs
    codecs.register(_finder)
