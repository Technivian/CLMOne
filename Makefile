PYTHON ?= .venv/bin/python
TEST_SETTINGS = config.settings_test

.PHONY: test test-fast check

## Run the full test suite hermetically (in-memory SQLite, no network).
test:
	DJANGO_SETTINGS_MODULE=$(TEST_SETTINGS) $(PYTHON) manage.py test

## Run a subset, e.g. `make test-fast APP=tests.test_approval_authorization`
test-fast:
	DJANGO_SETTINGS_MODULE=$(TEST_SETTINGS) $(PYTHON) manage.py test $(APP)

## Django system checks under the test settings.
check:
	DJANGO_SETTINGS_MODULE=$(TEST_SETTINGS) $(PYTHON) manage.py check
