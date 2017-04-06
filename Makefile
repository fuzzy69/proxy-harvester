.PHONY: tests

DIR := ${CURDIR}

help:
	@echo "clean - remove Python file artifacts"
	@echo "lint  - check style with flake8"
	@echo "tests - run unittests"
	@echo "setup - setup virtualenv"

setup:
	virtualenv -p python3 env
	. env/bin/activate && pip install -r requirements.txt

repos:
	git remote add local http://fuzzy:12345@localhost:3000/fuzzy69/proxy-harvester.git
	git remove add github git@github.com:fuzzy69/proxy-harvester.git

clean:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

tests:
	python -m unittest discover -v

migrate:
	ls