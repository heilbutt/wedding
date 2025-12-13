"""Generate static wedding website pages from templates and Markdown.

This module builds encrypted and public HTML pages from Markdown sources,
embeds images as data URIs, and wraps the output with PageCrypt for password protection.
"""

__author__ = "Hermann Pommerenke"
__email__ = "dev@pommerenke.ch"
__copyright__ = "2025, Hermann Pommerenke"

from pathlib import Path
import base64
import mimetypes
import os
import shutil
import tomllib

import markdown
from bs4 import BeautifulSoup


def insert_markdown_into_html(
    soup: BeautifulSoup,
    markdown_path: Path,
    insert_at_id: str
) -> None:
    """Insert rendered Markdown into an HTML document at a specific element.

    Reads Markdown from ``markdown_path``, converts it to HTML using the
    ``markdown`` package, and replaces the contents of the element in
    ``soup`` whose ``id`` attribute matches ``insert_at_id`` with the
    generated HTML fragment. Modifies ``soup`` in-place.

    Parameters
    ----------
    soup: BeautifulSoup
        The parsed HTML document to modify.
    markdown_path: Path
        Path to the Markdown file to read and render.
    insert_at_id: str
        The id attribute of the element inside ``soup`` where the rendered
        Markdown should be inserted. The element's contents will be cleared
        and replaced.

    Raises
    ------
    ValueError
        If no element with the given ``insert_at_id`` exists in ``soup``.
    """

    # load markdown and convert to bs4 HTML fragment
    markdown_text = markdown_path.read_text()
    html_text = markdown.markdown(markdown_text, output_format='html')

    # insert fragment at specified id
    content_tag = soup.find(id=insert_at_id)
    if not content_tag:
        raise ValueError(f'Could not find tag with id "{insert_at_id}" in HTML template')
    content_tag.clear()
    content_tag.append(BeautifulSoup(html_text, 'html.parser'))
    
    print(f'Markdown embedded from "{markdown_path}"')


def _image_to_base64_uri(
    image_path: Path
) -> str:
    """Convert an image file to a base64 data URI string.

    Reads the bytes from ``image_path``, guesses the MIME type, encodes the
    content as base64, and returns a data URI suitable for use as an ``src``
    attribute on an ``<img>`` tag (for example ``data:image/png;base64,...``).

    Parameters
    ----------
    image_path: Path
        Path to the image file to encode.

    Returns
    -------
    str
        A data URI string containing the MIME type and base64-encoded image
        data.

    Raises
    ------
    FileNotFoundError
        If ``image_path`` does not point to an existing file.
    ValueError
        If the MIME type for the file cannot be determined.
    """
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f'Could not find file "{image_path}"')
    
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        raise ValueError(f'Could not determine mime type of file "{image_path}"')
    
    base64_data = base64.b64encode(image_path.read_bytes()).decode('ascii')
    return f'data:{mime_type};base64,{base64_data}'


def embed_images_into_html(
    soup: BeautifulSoup,
    root_path: Path
) -> None:
    """Embed referenced images in an HTML document as base64 data URIs.

    Scans all ``<img>`` tags in ``soup`` and replaces their ``src``
    attributes with base64 data URIs produced by :func:`_image_to_base64_uri`.
    The incoming ``src`` values are treated as paths relative to
    ``root_path``. Modifies ``soup`` in-place.

    Parameters
    ----------
    soup: BeautifulSoup
        Parsed HTML document to modify.
    root_path: Path
        Directory used as the base for resolving relative image paths.
    """

    # Replace <img> sources with base64 data URIs
    N_embedded = 0
    for img_tag in soup.find_all('img'):
        relative_path = img_tag.get('src')
        if not relative_path:
            continue
        img_tag['src'] = _image_to_base64_uri(root_path/str(relative_path))
        N_embedded += 1

    print(f'Embedded {N_embedded} images as data URIs')


def get_h1_heading_from_html(
    soup:BeautifulSoup
) -> str:

    h1_tag = soup.find('h1')

    if not h1_tag:
        raise ValueError('No <h1> tag found')
    
    if not h1_tag.string:
        return ''
    
    return h1_tag.string


def set_html_page_title(
    soup: BeautifulSoup,
    page_title: str
) -> None:

    title_tag = soup.find('title')
    
    if not title_tag:
        raise ValueError(f'Title tag not found')

    title_tag.string = page_title
    
    print(f'HTML page title changed to "{page_title}"')


def set_html_link_to_stylesheet(
    soup: BeautifulSoup,
    relative_stylesheet_url: str,
) -> None:
    """Point the document's stylesheet link to a new relative URL.

    Locates the first ``<link rel="stylesheet">`` tag in ``soup`` and
    updates its ``href`` attribute to ``relative_stylesheet_url``.

    Parameters
    ----------
    soup: BeautifulSoup
        Parsed HTML document to modify.
    relative_stylesheet_url: str
        The relative URL to set on the stylesheet link's ``href``.

    Raises
    ------
    ValueError
        If a stylesheet link tag cannot be found.
    """
    link_tag = soup.find('link', rel='stylesheet')
    if not link_tag:
        raise ValueError(f'Stylesheet link tag not found')
    link_tag['href'] = relative_stylesheet_url

    print(f'Stylesheet linked as "{relative_stylesheet_url}"')


def set_external_links_new_tab(
    soup: BeautifulSoup
) -> None:
    """Update external anchor links to open in a new browser tab.

    Iterates over all ``<a>`` tags with an ``href`` and sets ``target="_blank"``
    for links that appear to be external (those whose ``href`` starts with
    ``http`` or ``//``).

    Parameters
    ----------
    soup: BeautifulSoup
        Parsed HTML document to modify.
    """

    N_links = 0
    for link_tag in soup.find_all('a', href=True):
        href = str(link_tag['href'])
        # Only modify external links
        if href.startswith('http') or href.startswith('//'):
            link_tag['target'] = '_blank'
            N_links += 1

    print(f'Modified {N_links} links to open in new tab')


def encrypt_with_pagecrypt(
    secret_html_path: Path,
    public_html_path: Path,
    pagecrypt_root: Path,
    password: str
) -> None:
    """Encrypt an HTML file using the PageCrypt helper script.

    Invokes the helper script located under ``pagecrypt_root/python/encrypt.py``
    using ``os.system`` to create an encrypted version of
    ``unencrypted_html_path``. PageCrypt writes an output file with the
    suffix "-protected" in the same directory as the input; this function
    moves that generated file to ``encrypted_html_path``.

    Parameters
    ----------
    unencrypted_html_path: Path
        Path to input HTML file to encrypt.
    encrypted_html_path: Path
        Desired path for the final encrypted HTML file.
    pagecrypt_root: Path
        Root directory of the PageCrypt distribution in the repo.
    password: str
        Password to pass to the PageCrypt script for encryption.

    Raises
    ------
    FileNotFoundError
        If the PageCrypt output file with the expected "-protected" suffix
        is not created after running the script.
    """

    command = ' '.join([
        'python',
        (pagecrypt_root/'python'/'encrypt.py').as_posix(),
        secret_html_path.as_posix(),
        password
        ]) 
    os.system(command)

    # PageCrypt created a file with suffix "-protected" in same directory as unencrypted file
    # move it to desired location
    pagecrypt_output: Path = secret_html_path.with_stem(secret_html_path.stem + '-protected')
    if not pagecrypt_output.exists():
        raise FileNotFoundError(f'PageCrypt output file "{pagecrypt_output}" expected, but nothing found')
    shutil.move(pagecrypt_output, public_html_path)
    
    print(f'PageCrypt successful: "{secret_html_path}" encrypted to "{public_html_path}"')


def main() -> None:

    root = Path(__file__).parent
    
    # read secret configuration
    config: dict = tomllib.loads((root/'source-secret'/'website-config.toml').read_text())

    for language in config['languages']:

        template_path = root/'template'/'template.html'
        secret_source_path = root/'source-secret'/f'content-{language}.md'
        secret_output_path = root/'docs-secret'/f'{language}.html'
        public_output_path = root/'docs'/f'{language}.html'

        # load HTML template
        soup = BeautifulSoup(template_path.read_text(), 'html.parser')

        # assemble unencrypted HTML
        insert_markdown_into_html(soup, secret_source_path, 'content-container')
        embed_images_into_html(soup, secret_source_path.parent)
        page_title = get_h1_heading_from_html(soup)
        set_html_page_title(soup, page_title)
        set_external_links_new_tab(soup)

        # write unencrypted file to disk
        secret_output_path.write_text(str(soup))
    
        # create encrypted page
        encrypt_with_pagecrypt(
            secret_output_path, public_output_path,
            root/'PageCrypt', config['password']
        )
    
        # set page title of encrypted file since it has been altered by PageCrypt
        soup = BeautifulSoup(public_output_path.read_text(), 'html.parser')
        set_html_page_title(soup, page_title)
        public_output_path.write_text(str(soup))


if __name__ == '__main__':
    main()