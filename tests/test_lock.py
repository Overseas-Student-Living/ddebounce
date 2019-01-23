import eventlet
from eventlet.event import Event
from mock import call, Mock
import pytest

from ddebounce import Lock


def test_debounce(redis_):

    lock = Lock(redis_)

    tracker = Mock()
    release = Event()

    @lock.debounce
    def func(*args, **kwargs):
        release.wait()
        tracker(*args, **kwargs)
        return tracker

    def coroutine():
        return func("egg", spam="ham")

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b"1" == redis_.get("lock:func(egg)")

    another_thread = eventlet.spawn(coroutine)
    assert another_thread.wait() is None

    assert tracker.call_count == 0

    release.send()
    eventlet.sleep(0.1)

    assert b"0" == redis_.get("lock:func(egg)")

    assert tracker == thread.wait()

    assert 1 == tracker.call_count
    assert call("egg", spam="ham") == tracker.call_args


def test_debounce_with_custom_key(redis_):

    lock = Lock(redis_)

    tracker = Mock()
    release = Event()

    @lock.debounce(key=lambda _, spam: "yo:{}".format(spam.upper()))
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()
        return tracker

    def coroutine():
        return func("egg", spam="ham")

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b"1" == redis_.get("lock:yo:HAM")

    release.send()
    eventlet.sleep(0.1)

    assert b"0" == redis_.get("lock:yo:HAM")

    assert tracker == thread.wait()

    assert 1 == tracker.call_count
    assert call("egg", spam="ham") == tracker.call_args


def test_debounce_with_repeat(redis_):

    lock = Lock(redis_)

    tracker = Mock()
    release = Event()

    @lock.debounce(repeat=True)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()
        return tracker

    def coroutine():
        return func("egg", spam="ham")

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b"1" == redis_.get("lock:func(egg)")

    # simulate locking attempt
    redis_.incr("lock:func(egg)")

    release.send()
    eventlet.sleep(0.1)

    assert b"0" == redis_.get("lock:func(egg)")

    assert tracker == thread.wait()

    # must be called twice with the same args
    assert 2 == tracker.call_count
    assert [call("egg", spam="ham"), call("egg", spam="ham")] == tracker.call_args_list


def test_debounce_with_callback(redis_):

    lock = Lock(redis_)

    tracker, callback_tracker = Mock(), Mock()
    release = Event()

    def callback(*args, **kwargs):
        callback_tracker(*args, **kwargs)

    @lock.debounce(callback=callback)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()
        return tracker

    def coroutine():
        return func("egg", spam="ham")

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b"1" == redis_.get("lock:func(egg)")

    # simulate locking attempt
    redis_.incr("lock:func(egg)")

    release.send()
    eventlet.sleep(0.1)

    assert b"0" == redis_.get("lock:func(egg)")

    assert tracker == thread.wait()

    assert 1 == tracker.call_count
    assert call("egg", spam="ham") == tracker.call_args

    # test callback call
    assert 1 == callback_tracker.call_count
    assert call("egg", spam="ham") == callback_tracker.call_args


def test_debounce_failing_on_execution(redis_):

    lock = Lock(redis_)

    tracker = Mock()
    release = Event()

    class Whoops(Exception):
        pass

    tracker.side_effect = Whoops("Yo!")

    @lock.debounce()
    def func(*args, **kwargs):
        release.wait()
        tracker(*args, **kwargs)

    def coroutine():
        with pytest.raises(Whoops):
            func("egg", spam="ham")

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b"1" == redis_.get("lock:func(egg)")

    release.send()
    eventlet.sleep(0.1)

    assert b"0" == redis_.get("lock:func(egg)")

    thread.wait()

    assert 1 == tracker.call_count
    assert call("egg", spam="ham") == tracker.call_args


def test_debounce_failing_on_repeat_execution(redis_):

    lock = Lock(redis_)

    tracker = Mock()
    release = Event()

    class Whoops(Exception):
        pass

    tracker.side_effect = [None, Whoops("Yo!")]

    @lock.debounce(repeat=True)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()

    def coroutine():
        with pytest.raises(Whoops):
            func("egg", spam="ham")

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b"1" == redis_.get("lock:func(egg)")

    # simulate locking attempt
    redis_.incr("lock:func(egg)")

    release.send()
    eventlet.sleep(0.1)

    assert b"0" == redis_.get("lock:func(egg)")

    thread.wait()

    # must be called twice with the same args
    assert 2 == tracker.call_count
    assert [call("egg", spam="ham"), call("egg", spam="ham")] == tracker.call_args_list


def test_debounce_failing_on_callback_execution(redis_):

    lock = Lock(redis_)

    tracker, callback_tracker = Mock(), Mock()
    release = Event()

    class Whoops(Exception):
        pass

    callback_tracker.side_effect = Whoops("Yo!")

    def callback(*args, **kwargs):
        callback_tracker(*args, **kwargs)

    @lock.debounce(callback=callback)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()

    def coroutine():
        with pytest.raises(Whoops):
            func("egg", spam="ham")

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b"1" == redis_.get("lock:func(egg)")

    # simulate locking attempt
    redis_.incr("lock:func(egg)")

    release.send()
    eventlet.sleep(0.1)

    assert b"0" == redis_.get("lock:func(egg)")

    thread.wait()

    assert 1 == tracker.call_count
    assert call("egg", spam="ham") == tracker.call_args

    # test callback call
    assert 1 == callback_tracker.call_count
    assert call("egg", spam="ham") == callback_tracker.call_args


def test_skip_duplicates_success(redis_):

    lock = Lock(redis_)

    tracker = Mock()

    @lock.skip_duplicates
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        return tracker

    func("egg", spam="ham")

    assert b"1" == redis_.get("lock:func(egg)")

    func("egg", spam="ham")

    assert b"2" == redis_.get("lock:func(egg)")

    assert 1 == tracker.call_count
    assert call("egg", spam="ham") == tracker.call_args


def test_skip_duplicates_with_custom_key(redis_):

    lock = Lock(redis_)

    tracker = Mock()

    @lock.skip_duplicates(key=lambda _, spam: "yo:{}".format(spam.upper()))
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        return tracker

    func("egg", spam="ham")

    assert b"1" == redis_.get("lock:yo:HAM")

    func("egg", spam="ham")

    assert b"2" == redis_.get("lock:yo:HAM")

    assert 1 == tracker.call_count
    assert call("egg", spam="ham") == tracker.call_args


def test_simple_acquire_and_release(redis_):

    lock = Lock(redis_)

    assert lock.acquire("101") is True
    assert lock.acquire("101") is False
    assert lock.acquire("102") is True
    assert lock.acquire("101") is False
    assert lock.acquire("102") is False

    assert lock.acquire("100") is True

    assert lock.release("101") is True
    assert lock.release("102") is True

    assert lock.release("102") is False

    assert lock.release("wat") is False  # never acquired


def test_default_expiration(redis_):

    ttl = 1

    lock = Lock(redis_, ttl)

    key = "101"

    assert lock.acquire(key) is True
    assert lock.acquire(key) is False
    # wait for TTL plus 0.1 to avoid hitting it at the point it just
    # expired but still returns
    eventlet.sleep(ttl + 0.1)
    assert lock.acquire(key) is True


def test_key_expires_after_release(redis_):

    ttl = 1

    lock = Lock(redis_, ttl)

    key = "101"

    formatted_key = lock.format_key(key)

    assert lock.acquire(key) is True

    assert redis_.ttl(formatted_key) > 0

    lock.release(key)

    # expect a ttl to still be set on the released key
    assert redis_.ttl(formatted_key) > 0

    # sleep until released key expires
    eventlet.sleep(ttl + 0.1)

    # ttl = -2 means that the key has gone
    assert redis_.ttl(formatted_key) == -2


def test_complex_scenario(redis_):

    lock = Lock(redis_)

    key = "101"

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
