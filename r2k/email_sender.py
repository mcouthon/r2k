import smtplib
from email.message import EmailMessage
from typing import Optional

from r2k.cli import logger

from .config import config
from .constants import Parser
from .mercury import get_clean_article
from .unicode import strip_common_unicode_chars


def get_mercury_attachment(url: str) -> Optional[str]:
    article = get_clean_article(url)
    return article.get("content")


def build_basic_message(title: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = title
    msg["To"] = config.send_to
    msg["From"] = config.send_from
    return msg


def send_email_message(msg: EmailMessage) -> bool:
    """Send an email"""
    # TODO: Consider making smtp server configurable
    logger.debug("Connecting to SMTP...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.ehlo()
        logger.debug("Logging into the SMTP server...")
        server.login(config.send_from, config.password)
        logger.debug("Sending the email...")
        server.send_message(msg)
        logger.debug("Email sent successfully!")
    return True


def add_content(msg: EmailMessage, url: str) -> bool:
    if config.parser == Parser.PUSH_TO_KINDLE:
        msg.set_content(url)
    elif config.parser == Parser.MERCURY:
        attachment = get_mercury_attachment(url)
        if not attachment:
            return False
        msg.add_attachment(
            attachment.encode("utf-8"),
            maintype="multipart",
            subtype="mixed; name=attachment.html",
            filename="attachment.html",
        )
    return True


def send_webpage_to_kindle(title: str, url: str) -> bool:
    """Send a webpage to Kindle"""
    title = strip_common_unicode_chars(title)
    msg = build_basic_message(title)
    added_content = add_content(msg, url)
    if added_content:
        return send_email_message(msg)
    else:
        return False
