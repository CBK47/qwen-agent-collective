PYTHON ?= python

.PHONY: doctor test smoke probe post-task explorer

doctor:
	$(PYTHON) -m shared.dashscope doctor

test:
	$(PYTHON) -m unittest discover -s tests

smoke:
	$(PYTHON) shared/smoke_test.py

probe:
	$(PYTHON) shared/probe.py

post-task:
	$(PYTHON) -m shared.improvement

explorer:
	cd brain/explorer && npm start
