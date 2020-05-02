from datetime import datetime
from os import listdir, makedirs, walk
from os.path import join
from shutil import copyfile, rmtree
from string import Template
from tempfile import mkdtemp
from typing import Any, List, Optional
from urllib.parse import urljoin, urlparse
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import requests
from bs4 import BeautifulSoup, element

from ebook import mercury
from r2k.cli import logger
from r2k.constants import HTML_HEADERS, TEMPLATES_DIR
from r2k.feeds import Article
from r2k.unicode import normalize_str, strip_common_unicode_chars

META_INF = "META-INF"
OEBPS = "OEBPS"
MIMETYPE = "mimetype"
IMAGES = "images"
CONTENT = "content"
_R2K = "_r2k"

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

    def parse(self) -> bool:
        """
        Prepare the content of the article for EPUB

        Performs these tasks:
            1. Parse the article with the Mercury parser
            2. Download all the images mentioned in the article (EPUB format only supports embedded local images)
            3. Replace all the <img "src"> tags with the local paths of the downloaded images
        :return: True iff the mercury parsing succeeded
        """
        parsed_article = mercury.parse(self.url)
        raw_content = parsed_article.get("content")
        if not raw_content:
            return False
        clean_html = strip_common_unicode_chars(raw_content)
        self.content = self.parse_images(clean_html)
        return True

    @staticmethod
    def is_valid(url: str) -> bool:
        """
        Checks whether `url` is a valid URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_img_url(self, img: element.Tag) -> Optional[str]:
        """
        Get an absolute img URL from an img HTML element (with some checks and verifications first)
        """
        img_url = img.attrs.get("src")
        if not img_url:
            # if img does not contain src attribute, just skip
            return None

        # In case img_url is relative, append it to the root url (urljoin will return img_url if it's an absolute URL)
        img_url = urljoin(self.url, img_url)

        # remove URLs like '/hsts-pixel.gif?c=3.2.5'
        try:
            pos = img_url.index("?")
            img_url = img_url[:pos]
        except ValueError:
            pass

        if self.is_valid(img_url):
            return img_url
        return None

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
            img_url = self.get_img_url(img)
            if not img_url:
                continue

            image_name = self.download_image(img_url)
            # Ad the articles live in the `content` folder, we need to go one level up
            image_path = join("..", IMAGES, image_name)
            img["src"] = image_path

        return soup.decode(pretty_print=True)

    @staticmethod
    def get_image_filename(url: str) -> str:
        """
        Get image name from its URL with a unique prefix to avoid collisions
        """
        image_basename = url.split("/")[-1]
        prefix = str(uuid4())[:8]
        # We start with img because XML IDs cannot start with numbers
        return f"img-{prefix}-{image_basename}"

    def download_image(self, url: str) -> str:
        """
        Download an image from a URL into the images folder
        """
        logger.debug(f"Downloading image {url}...")
        image_name = self.get_image_filename(url)
        image_path = join(self.images_path, image_name)

        # download the body of response by chunk, not immediately
        response = requests.get(url, headers=HTML_HEADERS, stream=True)
        with open(image_path, "wb") as f:
            for data in response.iter_content(1024):
                # write data read to the file
                f.write(data)
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
        self.date = datetime.utcnow().strftime("%Y-%m-%d")
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
        try:
            self.prepare_epub_dirs()
            self.copy_fixed_files()

            self.render_title()
            self.render_toc()
            self.render_articles()
            self.render_opf()

            return self.compress_epub()
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
                filename=join(dirname, filename), arcname=join(relative_dirname, filename), compress_type=ZIP_DEFLATED,
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
        for article in self.articles:
            if not article.parse():
                continue
            kwargs = dict(title=article.title, author=article.author, date=article.date, content=article.content)
            article_path = join(OEBPS, CONTENT, f"{article.id}.xhtml")
            article_html = self.render_template(join(OEBPS, CONTENT, "article.xhtml"), **kwargs)
            self.write_file(article_html, article_path)

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
            dict(id=image_name, ext=image_name.rsplit(".", 1)[1])
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

    def render_toc(self) -> None:
        """
        Generate, render and write the toc.ncx file (Table of Contents)
        """
        logger.debug("Rendering toc.ncx...")
        navpoints = self.generate_navpoints()
        kwargs = dict(title=self.title, uuid=self.uuid, navpoints=navpoints)
        self.render_and_write(join(OEBPS, "toc.ncx"), **kwargs)

    def generate_navpoints(self) -> str:
        """
        Create a navpoint per article for use in the toc.ncx file
        """
        logger.debug("Generating navpoints...")
        template = self.get_template(join(_R2K, "navpoint.xml"))
        navpoints = [dict(id=article.id, title=article.title, order=i + 2) for i, article in enumerate(self.articles)]
        return "\n".join([template.substitute(**navpoint) for navpoint in navpoints])

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
