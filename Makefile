DIST_PATH 		:= dist
PACKAGE_NAME 	:= rss-to-kindle
PACKAGE_DIR		:= rss_to_kindle

POETRY_BIN 		:= $(shell which poetry)
PIPX_BIN 		:= $(shell which pipx)

PACKAGE_VERSION := $(shell $(POETRY_BIN) version | cut -d' ' -f2)

DIST_PACKAGE := $(DIST_PATH)/$(PACKAGE_NAME)-$(PACKAGE_VERSION).tar.gz
SRC_FILES := $(shell find rss_to_kindle -iname "*.py" -type f)

POETRY_FILES := pyproject.toml poetry.lock

# CI required variables
GIT_REMOTE_URL ?= $(shell git remote get-url origin)
REPO_NAME ?= $(shell basename $(GIT_REMOTE_URL) .git)
COMMIT := $(shell git --no-pager rev-parse HEAD)
GIT_COMMIT ?= $(shell git --no-pager log -1 --pretty=format:%H)
LOCAL_IMAGE_TAG := $(REPO_NAME):$(GIT_COMMIT)
FULL_CONTAINER_NAME := $(ECR_URL)/$(LOCAL_IMAGE_TAG)

.PHONY: clean
clean:
	rm -rf build $(DIST_PATH) .eggs *.egg-info
	rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	find . -type f -name "*.py[co]" -exec rm -rf {} +

.PHONY: version
version: $(POETRY_FILES)
	$(POETRY_BIN) version

.PHONY: echo-version
echo-version: $(POETRY_FILES)
	@echo $(PACKAGE_VERSION)

.PHONY: flake8
flake8:
	$(POETRY_BIN) run flake8 $(PACKAGE_DIR)/ tests/

.PHONY: mypy
mypy:
	$(POETRY_BIN) run mypy $(PACKAGE_DIR)

.PHONY: pydocstyle
pydocstyle:
	$(POETRY_BIN) run pydocstyle $(PACKAGE_DIR)/

.PHONY: lint
lint: mypy flake8 pydocstyle

.PHONY: format
format:
	$(POETRY_BIN) run isort --recursive $(PACKAGE_DIR)/ tests/
	$(POETRY_BIN) run black $(PACKAGE_DIR)/ tests/
	$(POETRY_BIN) run pyupgrade --py3-plus --py36-plus --py37-plus --exit-zero-even-if-changed $(SRC_FILES)

.PHONY: format-check
format-check:
	$(POETRY_BIN) run isort --recursive --check-only $(PACKAGE_DIR)/ tests/
	$(POETRY_BIN) run black --check $(PACKAGE_DIR)/ tests/
	$(POETRY_BIN) run pyupgrade --py3-plus --py36-plus --py37-plus $(SRC_FILES)

.PHONY: prepare
prepare: format lint test

.PHONY: validate
validate: format-check lint test

.PHONY: pre-commit-install
pre-commit-install:
	$(POETRY_BIN) run pre-commit install

.PHONY: test
test: $(POETRY_FILES) tests
	$(POETRY_BIN) run pytest tests/

.PHONY: install
install: pyproject.toml
	$(POETRY_BIN) install

.PHONY: pipx-install
pipx-install: $(DIST_PACKAGE)
	$(PIPX_BIN) install $<

.PHONY: update
update: $(POETRY_FILES)
	$(POETRY_BIN) update

$(DIST_PACKAGE): $(POETRY_FILES) $(SRC_FILES)
	$(POETRY_BIN) build --format sdist

.PHONY: build
build: $(DIST_PACKAGE)

.PHONY: setup
setup: clean install build pipx-install

.PHONY: uninstall
uninstall: clean
	$(PIPX_BIN) uninstall $(PACKAGE_NAME)

.PHONY: docker-build
docker-build: Dockerfile .dockerignore
	docker build -t $(FULL_CONTAINER_NAME) -t $(LOCAL_IMAGE_TAG) .
