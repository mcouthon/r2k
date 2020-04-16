import smtplib

import click

from .config import config


def create_message(title, url) -> str:
    return f"""\
From: {config.send_from}
To: {", ".join([config.send_to, config.send_to])}
Subject: {title}

{url}
"""


def send_email(title, url):
    body = create_message(title, url)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.ehlo()
        server.login(config.send_from, config.password)
        server.sendmail(config.send_from, config.sent_to, body)

    click.echo("Email sent!")
