import eventlet
from eventlet.event import Event
from mock import call, Mock
import operator
import pytest

from ddebounce import debounce


@pytest.fixture
def tracker():
    return Mock()


@pytest.fixture
def release():
    return Event()


class TestDebounce:

    @pytest.fixture(params=('func', 'meth', 'meth_using_instance_client'))
    def debounced(self, request, redis_, release, tracker):

        @debounce(redis_)
        def spam(*args, **kwargs):
            release.wait()
            tracker(*args, **kwargs)
            return tracker

        class Spam:

            @debounce(redis_)
            def spam(self, *args, **kwargs):
                release.wait()
                tracker(*args, **kwargs)
                return tracker

        class SpamWithClientOnInstance:

            redis = redis_

            @debounce(operator.attrgetter('redis'))
            def spam(self, *args, **kwargs):
                release.wait()
                tracker(*args, **kwargs)
                return tracker

        samples = {
            'func': spam,
            'meth': Spam().spam,
            'meth_using_instance_client': SpamWithClientOnInstance().spam,
        }

        return samples[request.param]

    def test_debounce(self, debounced, redis_, release, tracker):

        def coroutine():
            return debounced('egg', spam='ham')

        thread = eventlet.spawn(coroutine)
        eventlet.sleep(0.1)

        assert b'1' == redis_.get('lock:spam(egg)')

        release.send()
        eventlet.sleep(0.1)

        assert b'0' == redis_.get('lock:spam(egg)')

        assert tracker == thread.wait()

        assert 1 == tracker.call_count
        assert call('egg', spam='ham') == tracker.call_args

    def test_debounce_failing_on_execution(
        self, debounced, redis_, release, tracker
    ):

        class Whoops(Exception):
            pass

        tracker.side_effect = Whoops('Yo!')

        def coroutine():
            with pytest.raises(Whoops):
                debounced('egg', spam='ham')

        thread = eventlet.spawn(coroutine)
        eventlet.sleep(0.1)

        assert b'1' == redis_.get('lock:spam(egg)')

        release.send()
        eventlet.sleep(0.1)

        assert b'0' == redis_.get('lock:spam(egg)')

        thread.wait()

        assert 1 == tracker.call_count
        assert call('egg', spam='ham') == tracker.call_args


class TestDebounceWithCustomKey:

    @pytest.fixture(params=('func', 'meth', 'meth_using_instance_client'))
    def debounced(self, request, redis_, release, tracker):

        def key(_, spam):
            return 'yo:{}'.format(spam.upper())

        @debounce(redis_, key=key)
        def spam(*args, **kwargs):
            tracker(*args, **kwargs)
            release.wait()
            return tracker

        class SomeClass:

            @debounce(redis_, key=key)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                release.wait()
                return tracker

        class SpamWithClientOnInstance:

            redis = redis_

            @debounce(operator.attrgetter('redis'), key=key)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                release.wait()
                return tracker

        samples = {
            'func': spam,
            'meth': SomeClass().spam,
            'meth_using_instance_client': SpamWithClientOnInstance().spam,
        }

        return samples[request.param]

    def test_debounce(self, debounced, redis_, release, tracker):

        def coroutine():
            return debounced('egg', spam='ham')

        thread = eventlet.spawn(coroutine)
        eventlet.sleep(0.1)

        assert b'1' == redis_.get('lock:yo:HAM')

        release.send()
        eventlet.sleep(0.1)

        assert b'0' == redis_.get('lock:yo:HAM')

        assert tracker == thread.wait()

        assert 1 == tracker.call_count
        assert call('egg', spam='ham') == tracker.call_args


class TestDebounceWithRepeat:

    @pytest.fixture(params=('func', 'meth', 'meth_using_instance_client'))
    def debounced(self, request, redis_, release, tracker):

        @debounce(redis_, repeat=True)
        def spam(*args, **kwargs):
            tracker(*args, **kwargs)
            release.wait()
            return tracker

        class SomeClass:

            @debounce(redis_, repeat=True)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                release.wait()
                return tracker

        class SpamWithClientOnInstance:

            redis = redis_

            @debounce(operator.attrgetter('redis'), repeat=True)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                release.wait()
                return tracker

        samples = {
            'func': spam,
            'meth': SomeClass().spam,
            'meth_using_instance_client': SpamWithClientOnInstance().spam,
        }

        return samples[request.param]

    def test_debounce(self, debounced, redis_, release, tracker):

        def coroutine():
            return debounced('egg', spam='ham')

        thread = eventlet.spawn(coroutine)
        eventlet.sleep(0.1)

        assert b'1' == redis_.get('lock:spam(egg)')

        # simulate locking attempt
        redis_.incr('lock:spam(egg)')

        release.send()
        eventlet.sleep(0.1)

        assert b'0' == redis_.get('lock:spam(egg)')

        assert tracker == thread.wait()

        # must be called twice with the same args
        assert 2 == tracker.call_count
        assert (
            [call('egg', spam='ham'), call('egg', spam='ham')] ==
            tracker.call_args_list)

    def test_debounce_failing_on_repeat_execution(
        self, debounced, redis_, release, tracker
    ):

        class Whoops(Exception):
            pass

        tracker.side_effect = [
            None,
            Whoops('Yo!')
        ]

        def coroutine():
            with pytest.raises(Whoops):
                debounced('egg', spam='ham')

        thread = eventlet.spawn(coroutine)
        eventlet.sleep(0.1)

        assert b'1' == redis_.get('lock:spam(egg)')

        # simulate locking attempt
        redis_.incr('lock:spam(egg)')

        release.send()
        eventlet.sleep(0.1)

        assert b'0' == redis_.get('lock:spam(egg)')

        thread.wait()

        # must be called twice with the same args
        assert 2 == tracker.call_count
        assert (
            [call('egg', spam='ham'), call('egg', spam='ham')] ==
            tracker.call_args_list)


class TestDebounceWithCallback:

    @pytest.fixture
    def callback_tracker(self):
        return Mock()

    @pytest.fixture(params=('func', 'meth', 'meth_using_instance_client'))
    def debounced(self, callback_tracker, request, redis_, release, tracker):

        def callback(*args, **kwargs):
            callback_tracker(*args, **kwargs)

        @debounce(redis_, callback=callback)
        def spam(*args, **kwargs):
            tracker(*args, **kwargs)
            release.wait()
            return tracker

        class SomeClass:

            @debounce(redis_, callback=callback)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                release.wait()
                return tracker

        class SpamWithClientOnInstance:

            redis = redis_

            @debounce(operator.attrgetter('redis'), callback=callback)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                release.wait()
                return tracker

        samples = {
            'func': spam,
            'meth': SomeClass().spam,
            'meth_using_instance_client': SpamWithClientOnInstance().spam,
        }

        return samples[request.param]

    def test_debounce(
        self, callback_tracker, debounced, redis_, release, tracker
    ):

        def coroutine():
            return debounced('egg', spam='ham')

        thread = eventlet.spawn(coroutine)
        eventlet.sleep(0.1)

        assert b'1' == redis_.get('lock:spam(egg)')

        # simulate locking attempt
        redis_.incr('lock:spam(egg)')

        release.send()
        eventlet.sleep(0.1)

        assert b'0' == redis_.get('lock:spam(egg)')

        assert tracker == thread.wait()

        assert 1 == tracker.call_count
        assert call('egg', spam='ham') == tracker.call_args

        # test callback call
        assert 1 == callback_tracker.call_count
        assert call('egg', spam='ham') == callback_tracker.call_args

    def test_debounce_failing_on_callback_execution(
        self, callback_tracker, debounced, redis_, release, tracker
    ):

        class Whoops(Exception):
            pass

        callback_tracker.side_effect = Whoops('Yo!')

        def callback(*args, **kwargs):
            callback_tracker(*args, **kwargs)

        def coroutine():
            with pytest.raises(Whoops):
                debounced('egg', spam='ham')

        thread = eventlet.spawn(coroutine)
        eventlet.sleep(0.1)

        assert b'1' == redis_.get('lock:spam(egg)')

        # simulate locking attempt
        redis_.incr('lock:spam(egg)')

        release.send()
        eventlet.sleep(0.1)

        assert b'0' == redis_.get('lock:spam(egg)')

        thread.wait()

        assert 1 == tracker.call_count
        assert call('egg', spam='ham') == tracker.call_args

        # test callback call
        assert 1 == callback_tracker.call_count
        assert call('egg', spam='ham') == callback_tracker.call_args
