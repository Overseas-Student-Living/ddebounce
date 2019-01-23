import pytest


@pytest.fixture
def debounce_applied():
    def _debounce_applied(func, key=None, repeat=False, callback=None, ttl=None):
        try:
            return (key, repeat, callback, ttl) == getattr(func, 'debounce_applied')
        except AttributeError:
            return False
    return _debounce_applied



@pytest.fixture
def skip_duplicates_applied():
    def _skip_duplicates_applied(func, key=None, ttl=None):
        try:
            return (key, ttl) ==  getattr(func, 'skip_duplicates_applied')
        except AttributeError:
            return False
    return _skip_duplicates_applied
