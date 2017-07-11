import pytest
import redis


def pytest_addoption(parser):
    parser.addoption(
        '--test-redis-uri',
        action='store',
        dest='TEST_REDIS_URI',
        default='redis://localhost:6379/11',
        help='Redis uri for testing (e.g. "redis://localhost:6379/11")')


@pytest.fixture
def redis_(request):
    client = redis.StrictRedis.from_url(
        request.config.getoption('TEST_REDIS_URI'))
    yield client
    client.flushdb()
