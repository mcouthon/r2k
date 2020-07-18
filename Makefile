POETRY_BIN 		:= $(shell which poetry)
PIPX_BIN 		:= $(shell which pipx)
PYTHON_BIN		:= $(shell which python)

R2K_DIST_PATH 		:= dist
R2K_PACKAGE_NAME 	:= r2k

READABILITY_DIR				:= python-readability
READABILITY_DIST_PATH		:= $(READABILITY_DIR)/dist
READABILITY_PACKAGE_NAME 	:= readability-lxml


R2K_PACKAGE_VERSION := $(shell $(POETRY_BIN) version | cut -d' ' -f2)

READABILITY_PACKAGE_VERSION := $(shell cd $(READABILITY_DIR); $(PYTHON_BIN) setup.py --version)

R2K_DIST_PACKAGE := $(R2K_DIST_PATH)/$(R2K_PACKAGE_NAME)-$(R2K_PACKAGE_VERSION).tar.gz
R2K_SRC_FILES := $(shell find r2k -iname "*.py" -type f)

READABILITY_DIST_PACKAGE := $(READABILITY_DIST_PATH)/$(READABILITY_PACKAGE_NAME)-$(READABILITY_PACKAGE_VERSION).tar.gz
READABILITY_SRC_FILES := $(shell find $(READABILITY_DIR)/readability -iname "*.py" -type f)

POETRY_FILES := pyproject.toml poetry.lock

# CI required variables
GIT_REMOTE_URL ?= $(shell git remote get-url origin)
REPO_NAME ?= $(shell basename $(GIT_REMOTE_URL) .git)
COMMIT := $(shell git --no-pager rev-parse HEAD)
GIT_COMMIT ?= $(shell git --no-pager log -1 --pretty=format:%H)
LOCAL_IMAGE_TAG := $(REPO_NAME):$(GIT_COMMIT)
FULL_CONTAINER_NAME := $(ECR_URL)/$(LOCAL_IMAGE_TAG)

clean:
	rm -rf build $(R2K_DIST_PATH) .eggs *.egg-info
	rm -rf $(READABILITY_DIR)/build $(READABILITY_DIST_PATH) $(READABILITY_DIR)/.eggs $(READABILITY_DIR)/*.egg-info
	rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	find . -type f -name "*.py[co]" -exec rm -rf {} +

version: $(POETRY_FILES)
	$(POETRY_BIN) version

flake8:
	$(POETRY_BIN) run flake8 $(PACKAGE_NAME)/ tests/

mypy:
	$(POETRY_BIN) run mypy $(PACKAGE_NAME)

pydocstyle:
	$(POETRY_BIN) run pydocstyle $(PACKAGE_NAME)/

lint: mypy flake8 pydocstyle

format:
	$(POETRY_BIN) run isort --recursive $(R2K_PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run black $(R2K_PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run pyupgrade --py3-plus --py36-plus --py37-plus --exit-zero-even-if-changed $(R2K_SRC_FILES)

format-check:
	$(POETRY_BIN) run isort --recursive --check-only $(R2K_PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run black --check $(R2K_PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run pyupgrade --py3-plus --py36-plus --py37-plus $(R2K_SRC_FILES)

prepare: format lint test

validate: format-check lint test

pre-commit-install:
	$(POETRY_BIN) run pre-commit install

test: $(POETRY_FILES) tests
	$(POETRY_BIN) run pytest tests/

install: pyproject.toml
	$(POETRY_BIN) install

pipx-install: $(DIST_PACKAGE)
	$(PIPX_BIN) install $<

$(READABILITY_DIST_PACKAGE):
	cd $(READABILITY_DIR); $(PYTHON_BIN) setup.py sdist

$(R2K_DIST_PACKAGE): $(READABILITY_DIST_PACKAGE)
	$(POETRY_BIN) build

build: $(R2K_DIST_PACKAGE)

setup: clean install build pipx-install

uninstall: clean
	$(PIPX_BIN) uninstall $(R2K_PACKAGE_NAME)

docker-build: Dockerfile .dockerignore
	docker build -t $(FULL_CONTAINER_NAME) -t $(LOCAL_IMAGE_TAG) .

bump-version:
	$(POETRY_BIN) version patch

publish-to-pypi:
	$(POETRY_BIN) publish

commit-bump-version:
	git add .
	git commit --all --message "Bump Version"

push:
	git push

.PHONY: publish
publish: $(READABILITY_DIST_PACKAGE) $(SRC_FILES) build publish-to-pypi commit-bump-version push
