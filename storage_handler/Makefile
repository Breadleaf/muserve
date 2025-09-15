SHELL:=$(shell which bash)

all: help

help:
	@echo "make targets:"
	@echo "    setup(venv, selfsign)"
	@echo "    venv"
	@echo "    clean"

setup: venv

venv:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

clean:
	rm -rf venv | true
	rm -rf __pycache__ | true
