from pathlib import Path
import markdown
from bs4 import BeautifulSoup
import base64
import mimetypes
import os
import shutil
import tomllib

def image_to_base64_uri(
        image_path: Path
) -> str:
    
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f'Could not find file "{image_path}"')
    
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        raise ValueError(f'Could not determine mime type of file "{image_path}"')
    
    base64_data = base64.b64encode(image_path.read_bytes()).decode('ascii')
    return f'data:{mime_type};base64,{base64_data}'


def embed_markdown_into_html(
        soup: BeautifulSoup,
        markdown_path: Path,
        insert_at_id: str
) -> None:
    
    # load markdown and convert to bs4 HTML fragment
    markdown_text = markdown_path.read_text()
    html_text = markdown.markdown(markdown_text, output_format='html')

    # insert fragment at specified id
    content_tag = soup.find(id=insert_at_id)
    if not content_tag:
        raise ValueError(f'Could not find tag with id "{insert_at_id}" in HTML template')
    content_tag.append(BeautifulSoup(html_text, 'html.parser'))

    # Replace <img> sources with base64 data URIs
    N_embedded = 0
    for img_tag in soup.find_all('img'):
        relative_path = img_tag.get('src')
        if not relative_path:
            continue
        img_tag['src'] = image_to_base64_uri(markdown_path.parent/str(relative_path))
        N_embedded += 1
    
    print(f'Markdown embedded from "{markdown_path}"')
    print(f'Embedded {N_embedded} images as data URIs')


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
    
    link_tag = soup.find('link', rel='stylesheet')
    if not link_tag:
        raise ValueError(f'Stylesheet link tag not found')
    link_tag['href'] = relative_stylesheet_url

    print(f'Stylesheet linked as "{relative_stylesheet_url}"')


def set_external_links_new_tab(
        soup: BeautifulSoup
) -> None:

    N_links = 0
    for link_tag in soup.find_all('a', href=True):
        href = str(link_tag['href'])
        # Only modify external links
        if href.startswith('http') or href.startswith('//'):
            link_tag['target'] = '_blank'
            N_links += 1

    print(f'Modified {N_links} links to open in new tab')


def encrypt_with_pagecrypt(
        unencrypted_html_path: Path,
        encrypted_html_path: Path,
        pagecrypt_root: Path,
        password: str
) -> None:
    
    command = ' '.join([
        'python',
        (pagecrypt_root/'python'/'encrypt.py').as_posix(),
        unencrypted_html_path.as_posix(),
        password
        ]) 
    os.system(command)

    # PageCrypt created a file with suffix "-protected" in same directory as unencrypted file
    # move it to desired location
    pagecrypt_output: Path = unencrypted_html_path.with_stem(unencrypted_html_path.stem + '-protected')
    if not pagecrypt_output.exists():
        raise FileNotFoundError('PageCrypt output file "{pagecrypt_output}" expected, but nothing found. Are the paths correct?')
    shutil.move(pagecrypt_output, encrypted_html_path)
    
    print(f'PageCrypt successful: "{unencrypted_html_path}" encrypted to "{encrypted_html_path}"')


def main() -> None:

    root = Path(__file__).parent
    
    # read secret configuration

    config_path = root/'secret'/'website-config.toml'
    config = tomllib.loads(config_path.read_text())

    # load HTML template

    template_path = root/'template.html'
    soup = BeautifulSoup(template_path.read_text(), 'html.parser')

    # assemble unencrypted HTML

    content_markdown_path = root/'secret'/'content.md'
    stylesheet_path = root/'docs'/'style.css'
    pagecrypt_path = root/'PageCrypt'
    unencrypted_website_path = root/'secret'/'website-unencrypted.html'
    encrypted_website_path = root/'docs'/'index.html'
    
    embed_markdown_into_html(soup, content_markdown_path, 'content-container')
    set_html_page_title(soup, config['title'])
    set_html_link_to_stylesheet(soup, stylesheet_path.relative_to(encrypted_website_path.parent, walk_up=True).as_posix())
    set_external_links_new_tab(soup)

    # write unencrypted file to disk
    unencrypted_website_path.write_text(soup.prettify())
    
    encrypt_with_pagecrypt(
        unencrypted_website_path,
        encrypted_website_path,
        pagecrypt_path,
        config['password']
        )
    
    # set page title of encrypted file since it has been altered by PageCrypt
    soup = BeautifulSoup(encrypted_website_path.read_text(), 'html.parser')
    set_html_page_title(soup, config['title'])
    encrypted_website_path.write_text(soup.prettify())
    
    # for preview only: retroactively modify stylesheet link in unencrypted file
    soup = BeautifulSoup(unencrypted_website_path.read_text(), 'html.parser')
    set_html_link_to_stylesheet(soup, stylesheet_path.relative_to(unencrypted_website_path.parent, walk_up=True).as_posix())
    unencrypted_website_path.write_text(soup.prettify())

if __name__ == '__main__':
    main()