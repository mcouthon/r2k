import os
from string import Template
from typing import Any, List

from r2k.cli import logger
from r2k.constants import TEMPLATES_DIR
from r2k.feeds import Article

from . import mercury


def build_html(articles: List[Article], title: str) -> str:
    """Create a composite HTML form multiple articles"""
    body = ""
    for raw_article in articles:
        logger.info(f"Parsing `{raw_article.title}`...")
        parsed_article = mercury.parse(raw_article.link)
        if parsed_article:
            formatted_string = get_formatted_article_string(raw_article, parsed_article)
            body = f"{body}\n{formatted_string}"
    toc = create_toc(articles)
    logger.info("Creating the composite HTML file...")
    return format_template("main.html", body=body, title=title, toc=toc)


def get_formatted_article_string(raw_article: Article, parsed_article: dict) -> str:
    """Create an HTML document from the parsed article, and the article.html Template"""
    kwargs = dict(
        date_published=raw_article.get_str_date(),
        heading=get_link_id(raw_article.title),
        site=parsed_article.get("domain", ""),
        content=parsed_article["content"],
        author=raw_article.author,
        title=raw_article.title,
    )
    logger.debug(f"Formatting article.html for `{raw_article.title}`")
    return format_template("article.html", **kwargs)


def format_template(template_name: str, **kwargs: Any) -> str:
    """Read and format a template with the passed kwargs"""
    with open(os.path.join(TEMPLATES_DIR, template_name)) as f:
        template = Template(f.read())

    return template.substitute(**kwargs)


def create_toc(articles: List[Article]) -> str:
    """Generate a string representing an HTML TOC"""
    template = '<li><a href="#{link}">{title}</a></li>'
    toc_list = []
    for article in articles:
        link = get_link_id(article.title)
        formatted_row = template.format(link=link, title=article.title)
        toc_list.append(formatted_row)
    toc = "\n".join(toc_list)
    return format_template("toc.html", toc=toc)


def get_link_id(title: str) -> str:
    """A simple method to create HTML link ids"""
    return title.replace(" ", "_")
