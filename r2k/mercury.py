import sys
from contextlib import contextmanager
from http.client import RemoteDisconnected
from time import sleep
from typing import Iterator

import docker
import requests
from docker.errors import APIError as DockerAPIError
from requests.exceptions import ConnectionError

from r2k.cli import logger

CONTAINER_NAME = "mercury-parser-api"
MERCURY_PORT = 3000
CONNECTION_ATTEMPTS = 10


def _validate_container_is_up(base_url: str) -> None:
    """Try to connect to the mercury parser service several times. Quit app if not successful"""
    errors = []
    while retries := CONNECTION_ATTEMPTS:
        try:
            requests.get(base_url)
            return
        except ConnectionError as e:
            errors.append(e)
            errors.append(e.args[0])
            if len(e.args[0].args) != 2:
                break
            errors.append(e.args[0].args[1])
            if not isinstance(errors[-1], RemoteDisconnected):
                break
        sleep(1)
        retries -= 1

    logger.error("Could not connect to the mercury-parser Docker container")
    if errors:
        errors_str = "\n".join(str(error) for error in errors)
        logger.error(f"Error info:{errors_str}")
    sys.exit(1)


@contextmanager
def mercury_parser() -> Iterator[str]:
    """
    Spin a local, dockerized version of the mercury parser API

    Relying on https://hub.docker.com/r/wangqiru/mercury-parser-api
    """
    client = docker.from_env()
    container = None
    try:
        container = client.containers.run(
            "wangqiru/mercury-parser-api:latest",
            detach=True,
            ports={f"{MERCURY_PORT}/tcp": MERCURY_PORT},
            name=CONTAINER_NAME,
        )
        base_url = f"http://localhost:{MERCURY_PORT}/parser"
        _validate_container_is_up(base_url)
        yield base_url
    except (ConnectionError, DockerAPIError) as e:
        logger.error("Could not connect to Docker. Is it running?")
        logger.debug(f"Error info:\n{e}")
        sys.exit(1)
    finally:
        if container:
            container.stop()
            container.remove()


def get_clean_article(url: str) -> dict:
    """
    Create a temporary container running the mercury parser and try to parse the URL with it

    :return: the JSON encoded parsed document
    """
    with mercury_parser() as base_url:
        full_url = f"{base_url}?url={url}"
        result = requests.get(full_url)
        return result.json()
