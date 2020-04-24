import smtplib
from email.message import EmailMessage

from r2k.cli import logger

from .config import config
from .constants import Parser
from .mercury import get_clean_article
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
    logger.debug("Connecting to SMTP...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.ehlo()
        logger.debug("Logging into the SMTP server...")
        server.login(config.send_from, config.password)
        logger.debug("Sending the email...")
        server.send_message(msg)
        logger.info("Email sent successfully!")
    return True


def set_content(msg: EmailMessage, url: str) -> bool:
    """Either set the text content of the email message, or attach an attachment, based on the current parser"""
    if config.parser == Parser.PUSH_TO_KINDLE:
        msg.set_content(url)
    elif config.parser == Parser.MERCURY:
        article, title = get_clean_article(url)
        if not article:
            return False
        filename = f"{title}.html"
        msg.add_attachment(
            article.encode("utf-8"),
            maintype="text",
            subtype=f'html; charset=utf-8; name="{filename}"',
            filename=filename,
        )
    return True


def send_webpage_to_kindle(title: str, url: str) -> bool:
    """Send a webpage to Kindle"""
    title = strip_common_unicode_chars(title)
    msg = build_basic_message(title)
    added_content = set_content(msg, url)
    if added_content:
        return send_email_message(msg)
    else:
        return False
