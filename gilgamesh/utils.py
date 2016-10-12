from itertools import tee, zip_longest


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    groups = zip_longest(*args, fillvalue=fillvalue)
    return (filter(lambda el: el is not None, group) for group in groups)


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
