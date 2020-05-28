from __future__ import annotations

import sys
from time import sleep
from types import TracebackType
from typing import Optional, Type

import docker
import requests
from docker.errors import APIError as DockerAPIError
from docker.models.containers import Container
from requests.exceptions import ConnectionError

from r2k.cli import logger

from .base_parser import ParserBase

CONTAINER_NAME = "mercury-parser-api"
MERCURY_PORT = 3000
BASE_MERCURY_URL = f"http://localhost:{MERCURY_PORT}/parser"
CONNECTION_ATTEMPTS = 10


class MercuryParser(ParserBase):
    """
    Represents the gateway to the Mercury Parser API

    Relies on https://hub.docker.com/r/wangqiru/mercury-parser-api
    """

    def __init__(self) -> None:
        """Constructor"""
        self.container: Optional[Container] = None
        self.client: docker.DockerClient = docker.from_env()

    def run_mercury_container(self) -> Container:
        """Launch a new mercury-parser docker container"""
        logger.debug("Launching a new mercury-parser Docker container...")
        self.container = self.client.containers.run(
            "wangqiru/mercury-parser-api:latest",
            detach=True,
            ports={f"{MERCURY_PORT}/tcp": MERCURY_PORT},
            name=CONTAINER_NAME,
        )
        return self.container

    def clean_existing_containers(self) -> None:
        """Remove any existing mercury parser API containers"""
        all_containers = self.client.containers.list(all=True, sparse=True)
        for container in all_containers:
            if container.attrs["Names"] == [f"/{CONTAINER_NAME}"]:
                logger.debug("Found an existing container with the same name...")
                self.remove_container(container)

    def remove_container(self, container: Optional[Container] = None) -> None:
        """Stop and remove a docker container"""
        container = container or self.container
        if container:
            logger.debug("Stopping container...")
            container.stop()
            logger.debug("Removing container...")
            container.remove()

    def __enter__(self) -> MercuryParser:
        """
        Context manager __enter__ for MercuryParser

            1. Clean any existing containers
            2. Spin a local, dockerized version of the mercury parser API
            3. Validate it's up
            4. Return the MercuryParser instance
        """
        self.clean_existing_containers()
        self.run_mercury_container()
        self.validate_container_is_up()
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> bool:
        """
        Context manager __exit__ for MercuryParser

            1. Remove the container
            2. Stop the program for any expected errors
        """
        self.remove_container()

        if exc_val:
            if isinstance(exc_val, (DockerAPIError, ConnectionError)):
                logger.error("Could not connect to Docker. Run with -v to get more details")
                logger.debug(f"Error info:\n{exc_val}")
                sys.exit(1)
            else:
                raise exc_val
        return True

    @staticmethod
    def validate_container_is_up() -> None:
        """Try to connect to the mercury parser service several times. Quit app if not successful"""
        errors = set()
        logger.debug(f"Launched container at {BASE_MERCURY_URL}. Validating it's up...")
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

    def parse(self, url: str) -> dict:
        """
        Parse a single URL with the Mercury Parser and return the result
        """
        result = self.get_parsed_doc(url)
        if result.get("error"):
            error_msg = result.get("message", "Unknown")
            logger.error(f"Failed to parse {url}\nError: {error_msg}")
            return {}
        return result

    @staticmethod
    def get_parsed_doc(url: str) -> dict:
        """Make an HTTP call to the mercury API and get the parsed document"""
        full_url = f"{BASE_MERCURY_URL}?url={url}"
        logger.debug("Parsing article with Mercury Parser...")
        logger.debug(f"Sending request to {full_url}")
        result = requests.get(full_url).json()
        logger.debug("Finished parsing")
        return result
