from os import listdir, makedirs, walk
from os.path import join
from shutil import copyfile, rmtree
from string import Template
from tempfile import mkdtemp
from typing import Any, List, Optional, Type
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import arrow
from bs4 import BeautifulSoup

from r2k.cli import logger
from r2k.config import config
from r2k.constants import TEMPLATES_DIR, Parser
from r2k.feeds import Article
from r2k.unicode import normalize_str, strip_common_unicode_chars

from . import images
from .base_parser import ParserBase

META_INF = "META-INF"
OEBPS = "OEBPS"
MIMETYPE = "mimetype"
IMAGES = "images"
CONTENT = "content"
_R2K = "_r2k"

# The number of elements in toc.ncx that appear before the articles (the initial 1 is because toc starts from 1, not 0)
NAVPOINT_OFFSET = 1 + 2

EPUB_DIR = join(TEMPLATES_DIR, "epub")


def create_epub(raw_articles: List[Article], title: str) -> str:
    """
    Create an EPUB book from multiple articles.

    :returns temp path to created ebook
    """
    epub_path = mkdtemp()
    logger.debug(f"Creating epub folder in {epub_path}")

    articles = [EPUBArticle(raw_article, epub_path) for raw_article in raw_articles]
    book = EPUB(articles, title, epub_path)
    return book.build()


class EPUBArticle:
    """
    Represents a single article, with rendering and parsing options for transforming it into EPUB content
    """

    def __init__(self, raw_article: Article, epub_path: str):
        """
        Constructor
        """
        self.url = raw_article.link
        self.title = raw_article.title
        self.id = normalize_str(self.title)
        self.author = raw_article.get("author", "")
        self.date = raw_article.get_str_date()
        self.images_path = join(epub_path, OEBPS, IMAGES)

        self.content: Optional[str] = None
        self.images: List[str] = []

    def parse(self, parser: ParserBase) -> bool:
        """
        Prepare the content of the article for EPUB

        Performs these tasks:
            1. Parse the article with the Mercury parser
            2. Download all the images mentioned in the article (EPUB format only supports embedded local images)
            3. Replace all the <img "src"> tags with the local paths of the downloaded images
        :return: True iff the parsing succeeded
        """
        logger.info(f"Parsing `{self.title}`...")
        parsed_article = parser.parse(self.url)
        raw_content = parsed_article.get("content")
        if not raw_content:
            return False

        # When some blogs (like xkcd.com) are parsed,
        # their content doesn't include the actual image, so we're adding it here
        if lead_image_url := parsed_article.get("lead_image_url"):
            raw_content = f'<img src="{lead_image_url}"/>\n{raw_content}'
        clean_html = strip_common_unicode_chars(raw_content)
        self.content = self.parse_images(clean_html)
        return True

    def parse_images(self, raw_content: str) -> str:
        """
        Parse and download images in the article

        Go over the content of the article and:
            1. Find all the `img` tags in the HTML
            2. Download all the images to the `images` folder in the EPUB dir
            3. Set the relative paths to those images in the HTML content
            4. Update the `content` attribute with the new HTML content
        """
        soup = BeautifulSoup(raw_content, "html.parser")
        logger.debug("Looking for images...")
        for img in soup.find_all("img"):
            img_url = images.get_img_url(self.url, img)
            if not img_url:
                continue

            image_name = self.download_image(img_url)
            # Ad the articles live in the `content` folder, we need to go one level up
            image_path = join("..", IMAGES, image_name)
            img["src"] = image_path

        return soup.decode(pretty_print=True)

    def download_image(self, url: str) -> str:
        """
        Download an image from a URL into the images folder
        """
        logger.debug(f"Downloading image {url}...")
        image_name = images.get_image_filename(url)
        image_path = join(self.images_path, image_name)
        images.download_image(url, image_path)
        return image_name

    def get_kwargs(self) -> dict:
        """
        Return a dict of the values necessary for rendering an article
        """
        return dict(title=self.title, author=self.author, date=self.date, content=self.content)


class EPUB:
    """
    Represents the whole EPUB book
    """

    def __init__(self, articles: List[EPUBArticle], title: str, epub_path: str):
        """
        Constructor
        """
        self.articles = articles
        self.title = title
        self.id = normalize_str(self.title)
        self.uuid = uuid4()
        # The date must be in the ISO 8601 format: https://www.w3.org/TR/NOTE-datetime
        self.date = arrow.now().isoformat()
        self._dst_path = epub_path

    def prepare_epub_dirs(self) -> None:
        """
        Create all the basic folders in the EPUB archive
        """
        logger.debug("Creating EPUB folders...")
        makedirs(join(self._dst_path, META_INF))
        makedirs(join(self._dst_path, OEBPS, CONTENT))
        makedirs(join(self._dst_path, OEBPS, IMAGES))

    def build(self) -> str:
        """
        Create an EPUB file from articles and templates

        :return: Path to the created epub archive
        """
        logger.info(f"Creating an EPUB book for `{self.title}`...")
        try:
            self.prepare_epub_dirs()
            self.copy_fixed_files()

            self.render_title()
            self.render_ncx_toc()
            self.render_html_toc()
            self.render_articles()
            self.render_opf()

            epub_path = self.compress_epub()
            logger.info("Successfully created an EPUB archive!")
            return epub_path
        finally:
            rmtree(self._dst_path)

    def compress_epub(self) -> str:
        """
        Create the EPUB ZIP archive

        First add the `mimetype` file - EPUB specs say it must be first and uncompressed.
        Then, recursively add all the files and folders under META-INF and OEBPS
        """
        logger.debug("Creating an epub archive...")

        epub_name = f"{self.id}.epub"
        epub_path = join(mkdtemp(prefix="epub"), epub_name)

        # The EPUB must contain the META-INF and mimetype files at the root, so
        with ZipFile(epub_path, "w") as epub:
            # Add the mimetype file first (as is required by EPUB format) and set it to be uncompressed
            epub.write(join(self._dst_path, MIMETYPE), arcname=MIMETYPE, compress_type=ZIP_STORED)
            self.recursively_add_files_to_epub_archive(epub)
        return epub_path

    def recursively_add_files_to_epub_archive(self, epub: ZipFile) -> None:
        """
        Recursively add all the files in the EPUB dest folder to the epub archive
        """
        for dirname, subdirs, files in walk(self._dst_path):
            # Skip the root folder, as the only file (as opposed to folder) there is the mimefile
            if dirname == self._dst_path:
                continue
            # This will be the file/folder name relative to the archive root
            relative_dirname = dirname.replace(self._dst_path, ".")

            # Add the folder itself to the archive, then add all the files in it
            epub.write(filename=dirname, arcname=relative_dirname)
            self.add_files_to_zip(epub, files, dirname, relative_dirname)

    @staticmethod
    def add_files_to_zip(epub: ZipFile, files: List[str], dirname: str, relative_dirname: str) -> None:
        """
        Recursively add all the files in a list to the epub archive
        """
        for filename in files:
            epub.write(
                filename=join(dirname, filename),
                arcname=join(relative_dirname, filename),
                compress_type=ZIP_DEFLATED,
                compresslevel=9,
            )

    def render_articles(self) -> None:
        """
        Go over all the articles and write their formatted content to disk

        For each article:
            1. Parse its content (also downloads images)
            2. If the parse did not succeed do nothing
            3. If the article was parsed successfully, use the `article.xhtml` template to create the final article
        """
        logger.debug("Rendering articles...")
        parser_cls = self._get_parser_class()
        with parser_cls() as parser:
            for article in self.articles:
                if not article.parse(parser):
                    continue
                kwargs = dict(title=article.title, author=article.author, date=article.date, content=article.content)
                article_path = join(OEBPS, CONTENT, f"{article.id}.xhtml")
                article_html = self.render_template(join(OEBPS, CONTENT, "article.xhtml"), **kwargs)
                self.write_file(article_html, article_path)

    @staticmethod
    def _get_parser_class() -> Type[ParserBase]:
        """Importing the classes here to avoid issues with optional packages (e.g. docker)"""
        parser_type = Parser(config.parser)

        if parser_type == Parser.MERCURY:
            from .mercury_parser import MercuryParser

            return MercuryParser
        elif parser_type == Parser.READABILITY:
            from .readability_parser import ReadabilityParser

            return ReadabilityParser
        else:
            raise ValueError(f"Parser must be one of: {Parser.__values__}")

    def render_opf(self) -> None:
        """
        Render the content.opf XML file

        content.opf requires the following:
            1. <item> elements for all the articles in the <manifest> section
            2. <item> elements for all the images in the <manifest> section
            3. <itemref> elements for all the articles in the <spine> section
        """
        logger.debug("Generating content.opf...")
        manifest_articles = self.generate_manifest_articles()
        manifest_images = self.generate_manifest_images()
        spine_articles = self.generate_spine_articles()
        kwargs = dict(
            title=self.title,
            date=self.date,
            uuid=self.uuid,
            manifest_articles=manifest_articles,
            manifest_images=manifest_images,
            spine_articles=spine_articles,
        )
        self.render_and_write(join(OEBPS, "content.opf"), **kwargs)

    def generate_manifest_images(self) -> str:
        """
        Create <item> elements for all the images in the <manifest> section
        """
        logger.debug("Generating manifest images...")
        manifest_image_template = Template('<item id="${id}" href="images/${id}" media-type="image/${ext}"/>')
        manifest_images: List[dict] = [
            dict(id=image_name, ext=images.get_img_extension(image_name))
            for image_name in listdir(join(self._dst_path, OEBPS, IMAGES))
            if image_name != "cover.png"
        ]
        return "\n\t".join([manifest_image_template.substitute(**image) for image in manifest_images])

    def generate_manifest_articles(self) -> str:
        """
        Create <item> elements for all the articles in the <manifest> section
        """
        logger.debug("Generating manifest articles...")
        manifest_article_template = Template(
            '<item id="${id}" href="content/${id}.xhtml" media-type="application/xhtml+xml"/>'
        )
        return "\n\t".join([manifest_article_template.substitute(id=article.id) for article in self.articles])

    def generate_spine_articles(self) -> str:
        """
        Create <itemref> elements for all the articles in the <spine> section
        """
        logger.debug("Generating spine articles...")
        spine_article_template = Template('<itemref idref="${id}"/>')
        return "\n\t".join([spine_article_template.substitute(id=article.id) for article in self.articles])

    def render_and_write(self, relative_path: str, **kwargs: Any) -> None:
        """
        Render a template and write it to the destination path
        """
        content = self.render_template(relative_path, **kwargs)
        self.write_file(content=content, path=relative_path)

    def render_title(self) -> None:
        """
        Render and write the title.xhtml file (title page of the book)
        """
        logger.debug("Rendering title.xhtml...")
        self.render_and_write(join(OEBPS, "title.xhtml"), **dict(title=self.title))

    def render_ncx_toc(self) -> None:
        """
        Generate, render and write the toc.ncx file (Table of Contents)
        """
        logger.debug("Rendering toc.ncx...")
        navpoints = self.generate_navpoints()
        kwargs = dict(title=self.title, uuid=self.uuid, navpoints=navpoints)
        self.render_and_write(join(OEBPS, "toc.ncx"), **kwargs)

    def render_html_toc(self) -> None:
        """
        Generate, render and write the toc.xhtml file (Table of Contents)
        """
        logger.debug("Rendering toc.xhtml...")
        toc = self.generate_html_toc()
        kwargs = dict(toc=toc, title=self.title)
        self.render_and_write(join(OEBPS, "toc.xhtml"), **kwargs)

    def generate_html_toc(self) -> str:
        """
        Create an HTML <li> element per article
        """
        template = Template('<li><a href="content/${id}.xhtml">${title}</a></li>')
        toc = [dict(id=article.id, title=article.title) for i, article in enumerate(self.articles)]
        return "\n\t".join([template.substitute(**elem) for elem in toc])

    def generate_navpoints(self) -> str:
        """
        Create a navpoint per article for use in the toc.ncx file
        """
        logger.debug("Generating navpoints...")
        template = self.get_template(join(_R2K, "navpoint.xml"))
        navpoints = [
            dict(id=article.id, title=article.title, order=i + NAVPOINT_OFFSET)
            for i, article in enumerate(self.articles)
        ]
        return "\n\t\t".join([template.substitute(**navpoint) for navpoint in navpoints])

    def copy_fixed_files(self) -> None:
        """
        Copy to the destination folder all the files that don't require rendering and can be copied as is
        """
        logger.debug("Copying fixed files...")
        self.copy_file("mimetype")
        self.copy_file(join(META_INF, "container.xml"))
        self.copy_file(join(OEBPS, IMAGES, "cover.png"))
        self.copy_file(join(OEBPS, "stylesheet.css"))

    def render_template(self, template_path: str, **kwargs: Any) -> str:
        """
        Return a rendered template
        """
        template = self.get_template(template_path)
        return template.substitute(**kwargs)

    @staticmethod
    def get_template(template_path: str) -> Template:
        """
        Return a Template object from the templates EPUB dir
        """
        with open(join(EPUB_DIR, template_path)) as f:
            return Template(f.read())

    def write_file(self, content: str, path: str) -> None:
        """
        Write a text file (not a binary one) to the EPUB destination path
        """
        with open(join(self._dst_path, path), "w") as f:
            f.write(content)

    def copy_file(self, template_path: str) -> None:
        """
        Copy a file from the template folder to the destination path
        """
        src_path = join(EPUB_DIR, template_path)
        dst_path = join(self._dst_path, template_path)
        copyfile(src_path, dst_path)
