import smtplib

from r2k.config import config
from r2k.unicode import strip_common_unicode_chars


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
    title = strip_common_unicode_chars(title)
    body = create_message(title, url)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.ehlo()
        server.login(config.send_from, config.password)
        server.sendmail(config.send_from, config.send_to, body)
