# Development tasks. Everything here also runs in CI, so a green `make
# check` locally means a green pipeline.

PACKAGES := parapet-record parapet-triage parapet-scope parapet-attrib parapet-cli
PYTHON ?= python

.PHONY: help install test coverage example lint build clean check facts

help:
	@echo "make install    editable installs of all $(words $(PACKAGES)) packages"
	@echo "make test       run the test suite"
	@echo "make coverage   run tests with coverage, write docs/coverage.md"
	@echo "make example    run the bundled Java example end to end"
	@echo "make build      build wheels and sdists into dist/"
	@echo "make check      test + example + build, what CI runs"
	@echo "make facts      print the numbers PROPOSAL_FACTS.md asks for"

install:
	$(PYTHON) -m pip install --upgrade pip
	@for pkg in $(PACKAGES); do \
		$(PYTHON) -m pip install -e packages/$$pkg || exit 1; \
	done
	$(PYTHON) -m pip install pytest pytest-cov build twine

test:
	$(PYTHON) -m pytest packages -q

coverage:
	$(PYTHON) -m pytest packages -q \
		--cov=parapet_record --cov=parapet_triage --cov=parapet_scope \
		--cov=parapet_attrib --cov=parapet_cli \
		--cov-report=term-missing --cov-report=json:coverage.json
	@$(PYTHON) -c "import json; \
d = json.load(open('coverage.json')); \
t = d['totals']; \
open('docs/coverage.md','w').write( \
  '# Test coverage\n\n' \
  'Statement coverage across the five packages, from `make coverage`.\n\n' \
  '| metric | value |\n| --- | ---: |\n' \
  '| statements | %d |\n' % t['num_statements'] + \
  '| covered | %d |\n' % t['covered_lines'] + \
  '| coverage | %.1f%% |\n\n' % t['percent_covered'] + \
  'Regenerate with `make coverage`.\n'); \
print('coverage %.1f%% -> docs/coverage.md' % t['percent_covered'])"

example:
	bash examples/java-demo/run.sh

lint:
	@$(PYTHON) -m pyflakes packages 2>/dev/null || \
		echo "pyflakes not installed; skipping (pip install pyflakes)"

build:
	rm -rf dist
	@for pkg in $(PACKAGES); do \
		$(PYTHON) -m build --outdir dist packages/$$pkg || exit 1; \
	done
	$(PYTHON) -m twine check dist/*

check: test example build

facts:
	@echo "--- packages"
	@echo "$(PACKAGES)" | tr ' ' '\n' | sed 's/^/  /'
	@echo "--- pattern sets"
	@parapet-triage patterns 2>/dev/null | head -4 || echo "  (install first)"
	@parapet-triage patterns --patterns security 2>/dev/null | head -2 || true
	@echo "--- ingest formats"
	@echo "  issues: csv, json, osv, github, text"
	@echo "  profiles: csv, json, jfr, jmh"
	@echo "  call graphs: java source, java-callgraph, understand, csv, json"
	@echo "--- run 'make coverage' for the coverage number"

clean:
	rm -rf dist coverage.json .pytest_cache examples/java-demo/out
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
