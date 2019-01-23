import operator

import wrapt

from .lock import Lock


def debounce(
    client, wrapped=None, key=None, repeat=False, callback=None, ttl=None
):

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if instance and isinstance(client, operator.attrgetter):
            decorated = Lock(client(instance), ttl).debounce(
                wrapped, key, repeat, callback
            )
        else:
            decorated = Lock(client, ttl).debounce(
                wrapped, key, repeat, callback
            )
        return decorated(*args, **kwargs)

    def logger(func):
        func.debounce_applied = (key, repeat, callback, ttl)
        return wrapper(func)

    return logger


def skip_duplicates(client, wrapped=None, key=None, ttl=None):

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if instance and isinstance(client, operator.attrgetter):
            decorated = Lock(client(instance), ttl).skip_duplicates(
                wrapped, key
            )
        else:
            decorated = Lock(client, ttl).skip_duplicates(wrapped, key)
        return decorated(*args, **kwargs)

    def logger(func):
        func.skip_duplicates_applied = (key, ttl)
        return wrapper(func)

    return logger
