import smtplib
from email.message import EmailMessage
from typing import Optional

from r2k.cli import logger

from .config import config
from .unicode import strip_common_unicode_chars


def build_basic_message(title: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = title
    msg["To"] = config.send_to
    msg["From"] = config.send_from
    return msg


def send_email_message(msg: EmailMessage) -> bool:
    """Send an email"""
    # TODO: Consider making smtp server configurable
    try:
        logger.debug("Connecting to SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.ehlo()
            logger.debug("Logging into the SMTP server...")
            server.login(config.send_from, config.password)
            logger.debug("Sending the email...")
            server.send_message(msg)
            logger.info("Email sent successfully!")
    except smtplib.SMTPException as e:
        logger.error(f"Caught an exception while trying to send an email.\nError: {e}")
        return False
    return True


def set_content(msg: EmailMessage, title: str, url: str, content: Optional[str]) -> None:
    """Either set the text content of the email message, or attach an attachment, based on the current parser"""
    if content:
        filename = f"{title}.html"
        logger.debug(f"Setting attachment for {filename}")
        msg.add_attachment(
            content.encode("utf-8"),
            maintype="text",
            subtype=f'html; charset=utf-8; name="{filename}"',
            filename=filename,
        )
    else:
        logger.debug(f"Setting email content to {url}")
        msg.set_content(url)


def send_webpage_to_kindle(title: str, url: str, content: Optional[str]) -> bool:
    """Send a webpage to Kindle"""
    title = strip_common_unicode_chars(title)
    msg = build_basic_message(title)
    set_content(msg, title, url, content)
    return send_email_message(msg)
