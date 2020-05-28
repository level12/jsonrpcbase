.PHONY: test

test:
	poetry run flake8 && \
		poetry run pytest --cov=./jsonrpcbase --cov-report=xml test && \
		poetry run coverage report

# For running tests while debugging your code; more verbose, inline logging
test-debug:
	poetry run flake8 && \
		poetry run pytest --cov=./jsonrpcbase --cov-report=xml -vv -x -s test && \
		poetry run coverage report && \
		poetry run coverage html
