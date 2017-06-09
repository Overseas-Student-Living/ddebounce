import redis


class Lock:

    def __init__(self, client, ttl=None):
        self.client = client
        self.ttl = ttl or 30

    format_key = 'lock:{}'.format

    def acquire(self, key):
        """ Try to acquire a lock and return `True` on success

        Returns `False` if the lock is already acquired by someone else

        """
        key = self.format_key(key)
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.ttl)
        count, _ = pipe.execute()
        return count <= 1

    def release(self, key):
        """ Release the lock

        Returns `True` if somebody else tried to acquire the same lock during
        the time it was held. Otherwise returns `False`.

        """
        count = self.client.getset(self.format_key(key), 0)
        count = int(count) if count else 0
        return count > 1
