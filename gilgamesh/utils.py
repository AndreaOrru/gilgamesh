"""Generic utility functions."""

from itertools import tee
from itertools import zip_longest


def grouper(iterable, n):
    """Collect data into fixed-length chunks or blocks.

    If len(iterable) % n != 0, the last chunk is simply cut.
    Example:
      grouper('ABCDEFG', 3) -> ABC DEF G

    Args:
        iterable: Any iterable object.
        n: The length of the chunks.

    Returns:
        An iterator that returns the chunks.
    """
    args = [iter(iterable)] * n
    groups = zip_longest(*args, fillvalue=None)
    return (filter(lambda el: el is not None, group) for group in groups)


def pairwise(iterable):
    """Iterate through iterable in consecutive pairs.

    s -> (s0, s1), (s1, s2), (s2, s3), ...

    Args:
        iterable: Any iterable object.

    Returns:
        An iterator that returns the pairs.
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
