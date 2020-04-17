import smtplib

import click

from .config import Config


def create_message(config: Config, title: str, url: str) -> str:
    """Generate an SMTP message"""
    return f"""\
From: {config.send_from}
To: {", ".join([config.send_to, config.send_to])}
Subject: {title}

{url}
"""


def send_email(config: Config, title: str, url: str) -> None:
    """Send an email"""
    body = create_message(config, title, url)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.ehlo()
        server.login(config.send_from, config.password)
        server.sendmail(config.send_from, config.sent_to, body)

    click.echo("Email sent!")
