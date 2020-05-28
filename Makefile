.PHONY: test

test:
	poetry run flake8 && \
		poetry run coverage run --source=jsonrpcbase -m pytest test && \
		poetry run coverage report

# For running tests while debugging your code; more verbose, inline logging
test-debug:
	poetry run flake8 && \
		poetry run coverage run --source=jsonrpcbase -vv -x -s -m pytest test && \
		poetry run coverage report && \
		poetry run coverage html
