import operator

import wrapt

from .lock import Lock


def debounce(lock, wrapped=None, key=None, repeat=False, callback=None):

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if instance and isinstance(lock, operator.attrgetter):
            decorated = Lock(lock(instance)).debounce(
                wrapped, key, repeat, callback)
        else:
            decorated = Lock(lock).debounce(
                wrapped, key, repeat, callback)
        return decorated(*args, **kwargs)

    def logger(func):
        func.debounce_applied = (key, repeat, callback)
        return wrapper(func)

    return logger


def skip_duplicates(lock, wrapped=None, key=None):

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if instance and isinstance(lock, operator.attrgetter):
            decorated = Lock(lock(instance)).skip_duplicates(wrapped, key)
        else:
            decorated = Lock(lock).skip_duplicates(wrapped, key)
        return decorated(*args, **kwargs)

    def logger(func):
        func.skip_duplicates_applied = (key,)
        return wrapper(func)

    return logger
