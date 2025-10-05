from pathlib import Path
import markdown
from bs4 import BeautifulSoup
import base64
import mimetypes


def image_to_base64_uri(
        image_path: Path
) -> str:
    
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f'Could not find file {image_path}')
    
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        raise ValueError(f'Could not determine mime type of file {image_path}')
    
    base64_data = base64.b64encode(image_path.read_bytes()).decode('ascii')
    return f'data:{mime_type};base64,{base64_data}'


def insert_markdown_into_html_template(
        markdown_path: Path,
        template_html_path: Path,
        output_html_path: Path,
        insert_at_id: str,
        embed_images: bool = True,
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
        raise ValueError(f'Could not find HTML tag with id {insert_at_id} in file {template_html_path}')
    content_tag.append(fragment)

    # Replace <img> sources with base64 data URIs
    if embed_images:
        for img_tag in soup.find_all('img'):
            relative_path = img_tag.get('src')
            if not relative_path:
                continue
            img_tag['src'] = image_to_base64_uri(markdown_path.parent/str(relative_path))
            
    # Save output HTML file
    output_html_path.write_text(soup.prettify(), encoding='utf-8')


def set_html_page_title(
        html_path: Path,
        page_title: str
) -> None:
    
    html_text = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_text, 'html.parser')
    
    title_tag = soup.find('title')
    if not title_tag:
        raise ValueError(f'Tag <title> not found in file {html_path}')
    title_tag.string = page_title

    # Overwrite file
    html_path.write_text(soup.prettify(), encoding='utf-8')


def main() -> None:

    root_directory = Path(__file__).parent.parent

    unencrypted_template_path = root_directory / 'tools' / 'template_unencrypted.html'
    unencrypted_website_path = root_directory / 'secret' / 'website_unencrypted.html'
    markdown_path = root_directory / 'secret' / 'content.md'

    insert_markdown_into_html_template(
        markdown_path=markdown_path,
        template_html_path=unencrypted_template_path,
        output_html_path=unencrypted_website_path,
        insert_at_id='content-container'
    )

    set_html_page_title(unencrypted_website_path, 'Test page title')


if __name__ == '__main__':
    main()