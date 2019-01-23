from mock import Mock
import pytest

from ddebounce import debounce, skip_duplicates


@pytest.fixture
def redis_():
    return Mock()


def test_debounce_not_applied(debounce_applied):

    def spam():
        pass

    assert not debounce_applied(spam)


def test_debounce_applied(debounce_applied, redis_):

    @debounce(redis_)
    def spam():
        pass

    assert debounce_applied(spam)


def test_debounce_applied_with_exact_attributes(debounce_applied, redis_):

    key, another_key = Mock(), Mock()
    callback = Mock()

    @debounce(redis_, key=key, repeat=True, callback=callback, ttl=60)
    def spam():
        pass

    assert not debounce_applied(spam)
    assert not debounce_applied(spam, key=key)
    assert not debounce_applied(spam, repeat=True)
    assert not debounce_applied(spam, callback=callback)
    assert not debounce_applied(spam, ttl=60)

    assert debounce_applied(
        spam, key=key, repeat=True, callback=callback, ttl=60
    )

    assert not debounce_applied(
        spam, key=another_key, repeat=True, callback=callback, ttl=60
    )


def test_skip_duplicates_not_applied(skip_duplicates_applied):

    def spam():
        pass

    assert not skip_duplicates_applied(spam)


def test_skip_duplicates_applied(skip_duplicates_applied, redis_):

    @skip_duplicates(redis_)
    def spam():
        pass

    assert skip_duplicates_applied(spam)


def test_skip_duplicates_applied_with_exact_attributes(
    skip_duplicates_applied, redis_
):
    key, another_key = Mock(), Mock()

    @skip_duplicates(redis_, key=key, ttl=60)
    def spam():
        pass

    assert not skip_duplicates_applied(spam)
    assert not skip_duplicates_applied(spam, key=another_key)

    assert skip_duplicates_applied(spam, key=key, ttl=60)
