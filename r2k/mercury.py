import sys
from contextlib import contextmanager
from time import sleep
from typing import Iterator, Optional

import docker
import requests
from docker.errors import APIError as DockerAPIError
from docker.models.containers import Container
from requests.exceptions import ConnectionError

from r2k.cli import logger

CONTAINER_NAME = "mercury-parser-api"
MERCURY_PORT = 3000
BASE_MERCURY_URL = f"http://localhost:{MERCURY_PORT}/parser"
CONNECTION_ATTEMPTS = 10


def _validate_container_is_up() -> None:
    """Try to connect to the mercury parser service several times. Quit app if not successful"""
    errors = set()
    logger.debug("Validating connection to container...")
    while retries := CONNECTION_ATTEMPTS:
        try:
            requests.get(BASE_MERCURY_URL)
            logger.debug("Connected!")
            return
        except ConnectionError as e:
            errors.add(e)
        sleep(1)
        retries -= 1

    logger.error("Could not connect to the mercury-parser Docker container")
    if errors:
        errors_str = "\n".join(str(error) for error in errors)
        logger.error(f"Error info:{errors_str}")
    sys.exit(1)


def clean_existing_containers(client: docker.DockerClient) -> None:
    all_containers = client.containers.list(all=True, sparse=True)
    for container in all_containers:
        if container.attrs["Names"] == [f"/{CONTAINER_NAME}"]:
            logger.debug("Found an existing container with the same name")
            remove_container(container)


def remove_container(container: Optional[Container]) -> None:
    if container:
        logger.debug("Stopping container...")
        container.stop()
        logger.debug("Removing container...")
        container.remove()


def run_mercury_container(client: docker.DockerClient) -> Container:
    """Launch a new mercury-parser docker container"""
    return client.containers.run(
        "wangqiru/mercury-parser-api:latest",
        detach=True,
        ports={f"{MERCURY_PORT}/tcp": MERCURY_PORT},
        name=CONTAINER_NAME,
    )


@contextmanager
def mercury_parser() -> Iterator[None]:
    """
    Spin a local, dockerized version of the mercury parser API

    Relies on https://hub.docker.com/r/wangqiru/mercury-parser-api
    """
    client = docker.from_env()
    container = None
    try:
        logger.debug("Removing any existing mercury-parser containers...")
        clean_existing_containers(client)
        logger.debug("Launching a new mercury-parser Docker container...")
        container = run_mercury_container(client)
        logger.debug(f"Launched container at {BASE_MERCURY_URL}. Validating it's up...")
        _validate_container_is_up()
        yield
    except (ConnectionError, DockerAPIError) as e:
        logger.error("Could not connect to Docker. Is it running?")
        logger.debug(f"Error info:\n{e}")
        sys.exit(1)
    finally:
        remove_container(container)


def get_clean_article(url: str) -> dict:
    """
    Create a temporary container running the mercury parser and try to parse the URL with it

    :return: the JSON encoded parsed document
    """
    with mercury_parser():
        full_url = f"{BASE_MERCURY_URL}?url={url}"
        logger.info("Parsing article with Mercury Parser...")
        logger.debug(f"Sending request to {full_url}")
        result = requests.get(full_url).json()
        logger.info("Finished parsing")
        if result.get("error"):
            error_msg = result.get("message", "Unknown")
            logger.error(f"Failed to parse {url}\nError: {error_msg}")
        return result
