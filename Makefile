.PHONY: run test

run:
	python3 -m src.reconcile

test:
	python3 -m unittest discover -s tests -v
