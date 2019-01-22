test: flake8 pylint pytest

flake8:
	flake8 src tests

pylint:
	pylint src -E --disable=no-value-for-parameter

pytest:
	coverage run --concurrency=eventlet --source src --branch -m pytest tests
	coverage report --show-missing --fail-under=100
