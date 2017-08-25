import eventlet
from eventlet.event import Event
from mock import call, Mock
import operator
import pytest

from ddebounce import skip_duplicates


@pytest.fixture
def tracker():
    return Mock()


class TestSkipDuplicates:

    @pytest.fixture(params=('func', 'meth', 'meth_using_instance_client'))
    def decorated(self, request, redis_, tracker):

        @skip_duplicates(redis_)
        def spam(*args, **kwargs):
            tracker(*args, **kwargs)
            return tracker

        class Spam:

            @skip_duplicates(redis_)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                return tracker

        class SpamWithClientOnInstance:

            redis = redis_

            @skip_duplicates(operator.attrgetter('redis'))
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                return tracker

        samples = {
            'func': spam,
            'meth': Spam().spam,
            'meth_using_instance_client': SpamWithClientOnInstance().spam,
        }

        return samples[request.param]

    def test_skip_duplicates(self, decorated, redis_, tracker):

        decorated('egg', spam='ham')

        assert b'1' == redis_.get('lock:spam(egg)')

        decorated('egg', spam='ham')

        assert b'2' == redis_.get('lock:spam(egg)')

        assert 1 == tracker.call_count
        assert call('egg', spam='ham') == tracker.call_args


class TestSkipDuplicatesWithCustomKey:

    @pytest.fixture(params=('func', 'meth', 'meth_using_instance_client'))
    def decorated(self, request, redis_, tracker):

        def key(_, spam):
            return 'yo:{}'.format(spam.upper())

        @skip_duplicates(redis_, key=key)
        def spam(*args, **kwargs):
            tracker(*args, **kwargs)
            return tracker

        class Spam:

            @skip_duplicates(redis_, key=key)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                return tracker

        class SpamWithClientOnInstance:

            redis = redis_

            @skip_duplicates(operator.attrgetter('redis'), key=key)
            def spam(self, *args, **kwargs):
                tracker(*args, **kwargs)
                return tracker

        samples = {
            'func': spam,
            'meth': Spam().spam,
            'meth_using_instance_client': SpamWithClientOnInstance().spam,
        }

        return samples[request.param]

    def test_skip_duplicates(self, decorated, redis_, tracker):

        decorated('egg', spam='ham')

        assert b'1' == redis_.get('lock:yo:HAM')

        decorated('egg', spam='ham')

        assert b'2' == redis_.get('lock:yo:HAM')

        assert 1 == tracker.call_count
        assert call('egg', spam='ham') == tracker.call_args
