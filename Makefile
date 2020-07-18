DIST_PATH 		:= dist
PACKAGE_NAME 	:= r2k

POETRY_BIN 		:= $(shell which poetry)
PIPX_BIN 		:= $(shell which pipx)

PACKAGE_VERSION := $(shell $(POETRY_BIN) version | cut -d' ' -f2)

DIST_PACKAGE := $(DIST_PATH)/$(PACKAGE_NAME)-$(PACKAGE_VERSION).tar.gz
SRC_FILES := $(shell find r2k -iname "*.py" -type f)

POETRY_FILES := pyproject.toml poetry.lock

# CI required variables
GIT_REMOTE_URL ?= $(shell git remote get-url origin)
REPO_NAME ?= $(shell basename $(GIT_REMOTE_URL) .git)
COMMIT := $(shell git --no-pager rev-parse HEAD)
GIT_COMMIT ?= $(shell git --no-pager log -1 --pretty=format:%H)
LOCAL_IMAGE_TAG := $(REPO_NAME):$(GIT_COMMIT)
FULL_CONTAINER_NAME := $(ECR_URL)/$(LOCAL_IMAGE_TAG)

clean:
	rm -rf build $(DIST_PATH) .eggs *.egg-info
	rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	find . -type f -name "*.py[co]" -exec rm -rf {} +

version: $(POETRY_FILES)
	$(POETRY_BIN) version

echo-version: $(POETRY_FILES)
	@echo $(PACKAGE_VERSION)

flake8:
	$(POETRY_BIN) run flake8 $(PACKAGE_NAME)/ tests/

mypy:
	$(POETRY_BIN) run mypy $(PACKAGE_NAME)

pydocstyle:
	$(POETRY_BIN) run pydocstyle $(PACKAGE_NAME)/

lint: mypy flake8 pydocstyle

format:
	$(POETRY_BIN) run isort --recursive $(PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run black $(PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run pyupgrade --py3-plus --py36-plus --py37-plus --exit-zero-even-if-changed $(SRC_FILES)

format-check:
	$(POETRY_BIN) run isort --recursive --check-only $(PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run black --check $(PACKAGE_NAME)/ tests/
	$(POETRY_BIN) run pyupgrade --py3-plus --py36-plus --py37-plus $(SRC_FILES)

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

build:
	$(POETRY_BIN) build --format=sdist

setup: clean install build pipx-install

uninstall: clean
	$(PIPX_BIN) uninstall $(PACKAGE_NAME)

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
publish: $(SRC_FILES) bump-version build publish-to-pypi commit-bump-version push
