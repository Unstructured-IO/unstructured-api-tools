PACKAGE_NAME := unstructured_api_tools
PIP_VERSION := 22.2.1


.PHONY: help
help: Makefile
	@sed -n 's/^\(## \)\([a-zA-Z]\)/\2/p' $<


###########
# Install #
###########

## install:                    installs all base and test requirements
.PHONY: install
install: install-base install-test

.PHONY: install-ci
install-ci: install

.PHONY: install-base
install-base:
	python3 -m pip install pip==${PIP_VERSION}
	pip install -r requirements/base.txt

.PHONY: install-test
install-test:
	pip install -r requirements/test.txt

## pip-compile:                compiles all base and test requirements
.PHONY: pip-compile
pip-compile:
	# NOTE(crag): you have to manually install pip-tools for now to run this.
	# There is a better way to do this with a pinned pip-compile version and a venv.
	bash -c "pip-compile -h >/dev/null  || { echo please run \'pip install pip-tools\' and then rerun this command; exit 1; }"
	pip-compile --upgrade -o requirements/base.txt
	pip-compile --upgrade -o requirements/test.txt requirements/base.txt requirements/test.in

## install-project-local:      install unstructured_api_tools into your local python environment
.PHONY: install-project-local
install-project-local: install
	# MAYBE TODO: fail if already exists?
	pip install -e .

## uninstall-project-local:    uninstall unstructured_api_tools from your local python environment
.PHONY: uninstall-project-local
uninstall-project-local:
	pip uninstall ${PACKAGE_NAME}

#################
# Test and Lint #
#################

## run-jupyter-test-notebooks: starts jupyter, allows execution of test notebooks
.PHONY: run-jupyter-test-notebooks
run-jupyter-test-notebooks:
	PYTHONPATH=$(realpath .)/test_unstructured_api_tools/pipeline-test-project/ JUPYTER_PATH=$(realpath .)/test_unstructured_api_tools/pipeline-test-project/ jupyter-notebook --NotebookApp.token='' --NotebookApp.password=''

## tidy-test-notebooks:        execute notebooks and remove metadata
.PHONY: tidy-test-notebooks
tidy-test-notebooks:
	PYTHONPATH=. ./test_unstructured_api_tools/pipeline-test-project/scripts/check-and-format-notebooks.py

## generate-test-api:          generates FastAPIs under ./test_unstructured_api_tools/pipeline-test-project
.PHONY: generate-test-api
generate-test-api:
	# generates FastAPI API's from notebooks in the test project ./test_unstructured_api_tools/pipeline-test-project
	PYTHONPATH=. PIPELINE_FAMILY_CONFIG=test_unstructured_api_tools/pipeline-test-project/preprocessing-pipeline-family.yaml \
		python3 ./unstructured_api_tools/cli.py convert-pipeline-notebooks \
		--input-directory ./test_unstructured_api_tools/pipeline-test-project/pipeline-notebooks \
		--output-directory ./test_unstructured_api_tools/pipeline-test-project/prepline_test_project/api


## api-check-test:             verifies auto-generated pipeline APIs match the existing ones
.PHONY: api-check-test
api-check-test:
	PYTHONPATH=. PACKAGE_NAME=prepline_test_project ./test_unstructured_api_tools/pipeline-test-project/scripts/test-doc-pipeline-apis-consistent.sh


## test:                       runs all unittests
.PHONY: test
test:
	PYTHONPATH=.:./test_unstructured_api_tools/pipeline-test-project pytest test_${PACKAGE_NAME} --cov=${PACKAGE_NAME} --cov=prepline_test_project --cov-report term-missing -vvv

## check:                      runs linters (includes tests)
.PHONY: check
check: check-src check-tests check-version

## check-src:                  runs linters (source only, no tests)
.PHONY: check-src
check-src:
	black --line-length 100 ${PACKAGE_NAME} --check
	flake8 ${PACKAGE_NAME}
	mypy ${PACKAGE_NAME} --ignore-missing-imports --install-types --non-interactive

.PHONY: check-tests
check-tests:
	black --line-length 100 test_${PACKAGE_NAME} --check --exclude test_${PACKAGE_NAME}/pipeline-test-project
	flake8 test_${PACKAGE_NAME} --exclude test_${PACKAGE_NAME}/pipeline-test-project/prepline_test_project/api

## check-scripts:              run shellcheck
.PHONY: check-scripts
check-scripts:
    # Fail if any of these files have warnings
	scripts/shellcheck.sh

## check-version:              run check to ensure version in CHANGELOG.md matches version in package
.PHONY: check-version
check-version:
    # Fail if syncing version would produce changes
	scripts/version-sync.sh -c \
		-f ${PACKAGE_NAME}/__version__.py semver

## tidy:                       run black
.PHONY: tidy
tidy:
	black --line-length 100 ${PACKAGE_NAME}
	black --line-length 100 test_${PACKAGE_NAME} --exclude test_${PACKAGE_NAME}/pipeline-test-project

## version-sync:               update __version__.py with most recent version from CHANGELOG.md
.PHONY: version-sync
version-sync:
	scripts/version-sync.sh \
		-f ${PACKAGE_NAME}/__version__.py semver

.PHONY: check-coverage
check-coverage:
	# TODO(crag): add coverage check for test_unstructured_api_tools/pipeline-test-project/prepline_test_project/api/
	coverage report --fail-under=95
