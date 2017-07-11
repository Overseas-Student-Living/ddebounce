import eventlet
from eventlet.event import Event
from mock import call, Mock
import operator
import pytest

from ddebounce import debounce


def test_debounce(redis_):

    tracker = Mock()
    release = Event()

    @debounce(redis_)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()
        return tracker

    def coroutine():
        return func('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:func(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:func(egg)')

    assert tracker == thread.wait()

    assert 1 == tracker.call_count
    assert call('egg', spam='ham') == tracker.call_args


def test_debounce_with_custom_key(redis_):

    tracker = Mock()
    release = Event()

    @debounce(redis_, key=lambda _, spam: 'yo:{}'.format(spam.upper()))
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()
        return tracker

    def coroutine():
        return func('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:yo:HAM')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:yo:HAM')

    assert tracker == thread.wait()

    assert 1 == tracker.call_count
    assert call('egg', spam='ham') == tracker.call_args


def test_debounce_with_repeat(redis_):

    tracker = Mock()
    release = Event()

    @debounce(redis_, repeat=True)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()
        return tracker

    def coroutine():
        return func('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:func(egg)')

    # simulate locking attempt
    redis_.incr('lock:func(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:func(egg)')

    assert tracker == thread.wait()

    # must be called twice with the same args
    assert 2 == tracker.call_count
    assert (
        [call('egg', spam='ham'), call('egg', spam='ham')] ==
        tracker.call_args_list)


def test_debounce_with_callback(redis_):

    tracker, callback_tracker = Mock(), Mock()
    release = Event()

    def callback(*args, **kwargs):
        callback_tracker(*args, **kwargs)

    @debounce(redis_, callback=callback)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()
        return tracker

    def coroutine():
        return func('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:func(egg)')

    # simulate locking attempt
    redis_.incr('lock:func(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:func(egg)')

    assert tracker == thread.wait()

    assert 1 == tracker.call_count
    assert call('egg', spam='ham') == tracker.call_args

    # test callback call
    assert 1 == callback_tracker.call_count
    assert call('egg', spam='ham') == callback_tracker.call_args


def test_debounce_failing_on_execution(redis_):

    tracker = Mock()
    release = Event()

    class Whoops(Exception):
        pass

    tracker.side_effect = Whoops('Yo!')

    @debounce(redis_)
    def func(*args, **kwargs):
        release.wait()
        tracker(*args, **kwargs)

    def coroutine():
        with pytest.raises(Whoops):
            func('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:func(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:func(egg)')

    thread.wait()

    assert 1 == tracker.call_count
    assert call('egg', spam='ham') == tracker.call_args


def test_debounce_failing_on_repeat_execution(redis_):

    tracker = Mock()
    release = Event()

    class Whoops(Exception):
        pass

    tracker.side_effect = [
        None,
        Whoops('Yo!')
    ]

    @debounce(redis_, repeat=True)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()

    def coroutine():
        with pytest.raises(Whoops):
            func('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:func(egg)')

    # simulate locking attempt
    redis_.incr('lock:func(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:func(egg)')

    thread.wait()

    # must be called twice with the same args
    assert 2 == tracker.call_count
    assert (
        [call('egg', spam='ham'), call('egg', spam='ham')] ==
        tracker.call_args_list)


def test_debounce_failing_on_callback_execution(redis_):

    tracker, callback_tracker = Mock(), Mock()
    release = Event()

    class Whoops(Exception):
        pass

    callback_tracker.side_effect = Whoops('Yo!')

    def callback(*args, **kwargs):
        callback_tracker(*args, **kwargs)

    @debounce(redis_, callback=callback)
    def func(*args, **kwargs):
        tracker(*args, **kwargs)
        release.wait()

    def coroutine():
        with pytest.raises(Whoops):
            func('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:func(egg)')

    # simulate locking attempt
    redis_.incr('lock:func(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:func(egg)')

    thread.wait()

    assert 1 == tracker.call_count
    assert call('egg', spam='ham') == tracker.call_args

    # test callback call
    assert 1 == callback_tracker.call_count
    assert call('egg', spam='ham') == callback_tracker.call_args
