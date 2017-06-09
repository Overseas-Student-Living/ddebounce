from mock import call, Mock
import pytest

from debounce_lock import Lock


class TestLock:

    def test_simple_acquire_and_release(self, redis_):

        lock = Lock(redis_)

        assert lock.acquire('101') is True
        assert lock.acquire('101') is False
        assert lock.acquire('102') is True
        assert lock.acquire('101') is False
        assert lock.acquire('102') is False

        assert lock.acquire('100') is True

        assert lock.release('101') is True
        assert lock.release('102') is True

        assert lock.release('102') is False

        assert lock.release('wat') is False  # never acquired

    def test_complex_scenario(self, redis_):

        lock = Lock(redis_)

        key = '101'

        # P1 acquires and starts processing the task
        assert lock.acquire(key) is True

        # P2 and P3 must not acquire - they should not process the task
        assert lock.acquire(key) is False
        assert lock.acquire(key) is False

        # P1 finishes the task processing and releases the lock
        # as there were others trying to acquire the same lock during
        # the time P1 was holding it, P1 will will retry the process
        # and acquire the lock again
        should_retry = lock.release(key)
        assert should_retry is True
        assert lock.acquire(key) is True

        # P4, P5, P6 kick in - all ignoring the task processing
        assert lock.acquire(key) is False
        assert lock.acquire(key) is False
        assert lock.acquire(key) is False

        # P1 finishes the task processing and releases the lock
        # as there were others trying to acquire the same lock during
        # the time P1 was holding it, P1 will will retry the process
        # and acquire the lock again
        should_retry = lock.release(key)
        assert should_retry is True
        # BUT P7 kicks in before P1 acquires the lock again
        assert lock.acquire(key) is True
        # then P1 will fail acquiring the lock
        assert lock.acquire(key) is False

        # P7 finishes and releases, as P1 tried to acquire, P7 will retry
        should_retry = lock.release(key)
        assert should_retry is True
        assert lock.acquire(key) is True

        # P7 finishes retry and leaves
        should_retry = lock.release(key)
        assert should_retry is False

        # P8 ...
        assert lock.acquire(key) is True
