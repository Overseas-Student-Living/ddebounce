import eventlet
from eventlet.event import Event
from mock import call, Mock
import operator
import pytest

from ddebounce import debouncemethod


def test_debounce(redis_):

    tracker = Mock()
    release = Event()

    class SomeClass:

        redis = redis_

        @debouncemethod(operator.attrgetter('redis'))
        def meth(self, *args, **kwargs):
            tracker(*args, **kwargs)
            release.wait()
            return tracker

    def coroutine():
        return SomeClass().meth('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:meth(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:meth(egg)')

    assert tracker == thread.wait()

    assert 1 == tracker.call_count
    assert call('egg', spam='ham') == tracker.call_args


def test_debounce_with_custom_key(redis_):

    tracker = Mock()
    release = Event()

    class SomeClass:

        redis = redis_

        @debouncemethod(
            operator.attrgetter('redis'),
            key=lambda _, spam: 'yo:{}'.format(spam.upper())
        )
        def meth(self, *args, **kwargs):
            tracker(*args, **kwargs)
            release.wait()
            return tracker

    def coroutine():
        return SomeClass().meth('egg', spam='ham')

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

    class SomeClass:

        redis = redis_

        @debouncemethod(operator.attrgetter('redis'), repeat=True)
        def meth(self, *args, **kwargs):
            tracker(*args, **kwargs)
            release.wait()
            return tracker

    def coroutine():
        return SomeClass().meth('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:meth(egg)')

    # simulate locking attempt
    redis_.incr('lock:meth(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:meth(egg)')

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

    class SomeClass:

        redis = redis_

        @debouncemethod(operator.attrgetter('redis'), callback=callback)
        def meth(self, *args, **kwargs):
            tracker(*args, **kwargs)
            release.wait()
            return tracker

    def coroutine():
        return SomeClass().meth('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:meth(egg)')

    # simulate locking attempt
    redis_.incr('lock:meth(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:meth(egg)')

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

    class SomeClass:

        redis = redis_

        @debouncemethod(operator.attrgetter('redis'))
        def meth(self, *args, **kwargs):
            release.wait()
            tracker(*args, **kwargs)
            return tracker

    def coroutine():
        with pytest.raises(Whoops):
            return SomeClass().meth('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:meth(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:meth(egg)')

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

    class SomeClass:

        redis = redis_

        @debouncemethod(operator.attrgetter('redis'), repeat=True)
        def meth(self, *args, **kwargs):
            release.wait()
            tracker(*args, **kwargs)
            return tracker

    def coroutine():
        with pytest.raises(Whoops):
            return SomeClass().meth('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:meth(egg)')

    # simulate locking attempt
    redis_.incr('lock:meth(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:meth(egg)')

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

    class SomeClass:

        redis = redis_

        @debouncemethod(operator.attrgetter('redis'), callback=callback)
        def meth(self, *args, **kwargs):
            release.wait()
            tracker(*args, **kwargs)
            return tracker

    def coroutine():
        with pytest.raises(Whoops):
            return SomeClass().meth('egg', spam='ham')

    thread = eventlet.spawn(coroutine)
    eventlet.sleep(0.1)

    assert b'1' == redis_.get('lock:meth(egg)')

    # simulate locking attempt
    redis_.incr('lock:meth(egg)')

    release.send()
    eventlet.sleep(0.1)

    assert b'0' == redis_.get('lock:meth(egg)')

    thread.wait()

    assert 1 == tracker.call_count
    assert call('egg', spam='ham') == tracker.call_args

    # test callback call
    assert 1 == callback_tracker.call_count
    assert call('egg', spam='ham') == callback_tracker.call_args
