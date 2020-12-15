try:
    import rewrite_magic
except ImportError as ecx:
    if ecx.name == 'rewrite_magic':
        pass
    else:
        raise
else:
    rewrite_magic.activate()
