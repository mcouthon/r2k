from typing import Optional
from urllib.parse import urljoin, urlparse
from uuid import uuid4

import requests
from bs4.element import Tag

from r2k.constants import HTML_HEADERS


def download_image(url: str, path: str) -> None:
    """
    Download an image from URL to path
    """
    # download the body of response by chunk, not immediately
    response = requests.get(url, headers=HTML_HEADERS, stream=True)
    with open(path, "wb") as f:
        for data in response.iter_content(1024):
            # write data read to the file
            f.write(data)


def get_image_filename(url: str) -> str:
    """
    Get image name from its URL with a unique prefix to avoid collisions
    """
    image_basename = url.split("/")[-1]
    prefix = str(uuid4())[:8]
    # We start with img because XML IDs cannot start with numbers
    return f"img-{prefix}-{image_basename}"


def is_valid_img_url(url: str) -> bool:
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_img_url(url: str, img: Tag) -> Optional[str]:
    """
    Get an absolute img URL from an img HTML element (with some checks and verifications first)
    """
    img_url = img.attrs.get("src")
    if not img_url:
        # if img does not contain src attribute, just skip
        return None

    # In case img_url is relative, append it to the root url (urljoin will return img_url if it's an absolute URL)
    img_url = urljoin(url, img_url)

    # remove URLs like '/hsts-pixel.gif?c=3.2.5'
    try:
        pos = img_url.index("?")
        img_url = img_url[:pos]
    except ValueError:
        pass

    if is_valid_img_url(img_url):
        return img_url
    return None


def get_img_extension(path: str) -> str:
    """
    Parse the path and return the image's extension (replacing jpg to jpeg with accordance with EPUB spec)
    """
    path_list = path.rsplit(".", 1)
    if len(path_list) == 2:
        ext = path_list[1]
    else:
        ext = "jpeg"
    if ext == "jpg":
        ext = "jpeg"
    return ext
