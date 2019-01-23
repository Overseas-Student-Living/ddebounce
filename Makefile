test: flake8 pylint pytest

flake8:
	flake8 ddebounce tests

pylint:
	pylint ddebounce -E --disable=no-value-for-parameter

pytest:
	coverage run --concurrency=eventlet --source ddebounce --branch -m pytest tests
	coverage report --show-missing --fail-under=100
