import smtplib

from r2k.cli import logger
from r2k.config import config


def create_message(title: str, url: str) -> str:
    """Generate an SMTP message"""
    return f"""\
From: {config.send_from}
To: {", ".join([config.send_to, config.send_to])}
Subject: {title}

{url}
"""


def send_webpage_to_kindle(title: str, url: str) -> None:
    """Send a webpage to Kindle"""
    logger.debug(f"Sending `{title}`...")
    body = create_message(title, url)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.ehlo()
        server.login(config.send_from, config.password)
        server.sendmail(config.send_from, config.send_to, body)

    logger.debug("Email successfully sent!")
