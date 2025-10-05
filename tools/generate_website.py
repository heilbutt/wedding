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
        markdown_path: Path,
        output_html_path: Path,
        template_html_path: Path,
        insert_at_id: str
) -> None:
    
    # load markdown and convert to bs4 HTML fragment
    markdown_text = markdown_path.read_text(encoding='utf-8')
    html_text = markdown.markdown(markdown_text, output_format='html')
    fragment = BeautifulSoup(html_text, 'html.parser')

    # parse template HTML using bs4
    soup = BeautifulSoup(template_html_path.read_text(encoding='utf-8'), 'html.parser')

    # insert fragment at specified id
    content_tag = soup.find(id=insert_at_id)
    if not content_tag:
        raise ValueError(f'Could not find HTML tag with id "{insert_at_id}" in file "{template_html_path}"')
    content_tag.append(fragment)

    # Replace <img> sources with base64 data URIs
    N_embedded = 0
    for img_tag in soup.find_all('img'):
        relative_path = img_tag.get('src')
        if not relative_path:
            continue
        img_tag['src'] = image_to_base64_uri(markdown_path.parent/str(relative_path))
        N_embedded += 1
            
    # Save output HTML file
    output_html_path.write_text(soup.prettify(), encoding='utf-8')
    
    print(f'Markdown embedded from "{markdown_path}" into "{output_html_path}"')
    print(f'Embedded {N_embedded} images as data URIs')


def set_html_page_title(
        html_path: Path,
        page_title: str
) -> None:
    
    html_text = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_text, 'html.parser')
    
    title_tag = soup.find('title')
    if not title_tag:
        raise ValueError(f'Title tag not found in file "{html_path}"')
    title_tag.string = page_title

    # Overwrite file
    html_path.write_text(soup.prettify(), encoding='utf-8')
    
    print(f'HTML page title in "{html_path}" changed to "{page_title}"')


def set_html_link_to_stylesheet(
        html_path: Path,
        relative_stylesheet_url: str,
) -> None:
    
    html_text = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_text, 'html.parser')
    
    link_tag = soup.find('link', rel='stylesheet')
    if not link_tag:
        raise ValueError(f'Stylesheet link tag not found in file "{html_path}"')
    link_tag['href'] = relative_stylesheet_url

    # Overwrite file
    html_path.write_text(soup.prettify(), encoding='utf-8')

    print(f'Stylesheet linked as "{relative_stylesheet_url}" in file "{html_path}"')


def set_external_links_new_tab(
        html_path: Path
) -> None:
    
    html_text = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_text, 'html.parser')

    N_links = 0
    for link_tag in soup.find_all('a', href=True):
        href = str(link_tag['href'])
        # Only modify external links
        if href.startswith('http') or href.startswith('//'):
            link_tag['target'] = '_blank'
            N_links += 1

    # Overwrite file
    html_path.write_text(soup.prettify(), encoding='utf-8')

    print(f'Modified {N_links} links in "{html_path}" to open in new tab')


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
    shutil.move(
        unencrypted_html_path.with_stem(unencrypted_html_path.stem + '-protected'),
        encrypted_html_path
        )
    
    print(f'PageCrypt successful: "{unencrypted_html_path}" encrypted to "{encrypted_html_path}"')


def main() -> None:

    # paths
    root = Path(__file__).parent.parent
    content_md_path = root/'secret'/'content.md'
    template_path = root/'tools'/'template.html'
    stylesheet_path = root/'style.css'
    pagecrypt_path = root/'tools'/'PageCrypt'
    unencrypted_website_path = root/'secret'/'website-unencrypted.html'
    encrypted_website_path = root/'index.html'
    config_path = root/'secret'/'website-config.toml'
    
    # read secret configuration from TOML
    config = tomllib.loads(config_path.read_text(encoding='utf-8'))

    # embed markdown as HTML and images as data URIs
    embed_markdown_into_html(
        markdown_path=content_md_path,
        output_html_path=unencrypted_website_path,
        template_html_path=template_path,
        insert_at_id='content-container'
        )
    
    # set page title
    set_html_page_title(
        html_path=unencrypted_website_path,
        page_title=config['page_title']
        )
    
    # set link to stylesheet as relative URL
    set_html_link_to_stylesheet(
        html_path=unencrypted_website_path,
        relative_stylesheet_url=stylesheet_path.relative_to(encrypted_website_path.parent, walk_up=True).as_posix()
        )
    
    # make all external links open in new tab
    set_external_links_new_tab(unencrypted_website_path)
    
    # encrypt with pagecrypt
    encrypt_with_pagecrypt(
        unencrypted_html_path=unencrypted_website_path,
        encrypted_html_path=encrypted_website_path,
        pagecrypt_root=pagecrypt_path,
        password=config['password']
        )
    
    # set page title of encrypted file since it has been altered by PageCrypt
    set_html_page_title(
        html_path=encrypted_website_path,
        page_title=config['page_title']
        )
    
    # for preview only: retroactively modify stylesheet link in unencrypted file
    set_html_link_to_stylesheet(
        html_path=unencrypted_website_path,
        relative_stylesheet_url=stylesheet_path.relative_to(unencrypted_website_path.parent, walk_up=True).as_posix()
        )

if __name__ == '__main__':
    main()