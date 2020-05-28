.PHONY: test

test:
	poetry run flake8 && \
		poetry run coverage run --source=jsonrpcbase -m pytest -s test && \
		poetry run coverage report && \
		poetry run coverage html
