def invalidate(instance, name):
    try:
        del instance.__dict__[name]
    except KeyError:
        pass
