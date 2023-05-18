.PHONY: all deps test-deps test deploy run reset

DEVICE ?= auto
DEPS = umqtt.simple
TEST_DEPS = unittest

mpremote = mpremote connect $(DEVICE)

all: deps deploy reset

deps: $(DEPS)

test-deps: $(TEST_DEPS)

$(DEPS) $(TEST_DEPS):
	$(mpremote) mip install $@

test: deploy
	$(mpremote) cp -r tests ":"
	$(mpremote) exec 'import unittest; unittest.main("tests")'

deploy:
	$(mpremote) cp *.py ":"
	@if test -f settings.json; then \
		$(mpremote) cp settings.json ":"; \
	fi

run:
	$(mpremote) run main.py

reset:
	$(mpremote) reset
