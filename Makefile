# Diff against the empty tree so whitespace checks cover all tracked files.
EMPTY_TREE := $(shell git hash-object -t tree /dev/null)

.PHONY: check test run-scenario scenario-index run-queue queue

check: test
	python3 scripts/check.py
	python3 scripts/scenario_index.py --check
	git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab diff --check $(EMPTY_TREE)

test:
	python3 -m unittest discover -s cli
	python3 -m unittest discover -s scripts

run-scenario:
	python3 scripts/run_scenario.py $(ARGS)

scenario-index:
	python3 scripts/scenario_index.py

run-queue:
	python3 scripts/run_queue.py $(ARGS)

queue: run-queue
