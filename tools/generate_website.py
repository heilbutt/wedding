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
        raise RuntimeError(f'Could not determine mime type of file {image_path}')
    
    base64_data = base64.b64encode(image_path.read_bytes()).decode('ascii')
    return f'data:{mime_type};base64,{base64_data}'


def markdown_to_html_with_embedded_images(
        markdown_path: Path,
        html_template_path: Path,
        html_output_path: Path,
        placeholder: str
) -> None:
    
    # load markdown
    markdown_text = markdown_path.read_text(encoding='utf-8')

    # convert markdown to HTML
    html_text = markdown.markdown(markdown_text, output_format='html')

    # insert into template
    html_template = html_template_path.read_text(encoding='utf-8')
    html_filled = html_template.replace(placeholder, html_text)

    # Parse HTML to replace <img> sources with base64 data URIs
    soup = BeautifulSoup(html_filled, 'html.parser')
    for img_tag in soup.find_all('img'):
        relative_path = img_tag.get('src')
        if not relative_path:
            continue
        img_tag['src'] = image_to_base64_uri(markdown_path.parent/str(relative_path))
            
    # Save output
    html_output_path.write_text(str(soup), encoding='utf-8')


def set_html_page_title(
        html_path: Path,
        page_title: str
) -> None:
    
    html_text = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_text, 'html.parser')
    
    title_tag = soup.find('title')
    if not title_tag:
        raise RuntimeError(f'Tag <title> not found in file {html_path}')

    title_tag.string = page_title


def main() -> None:

    root_directory = Path(__file__).parent.parent

    unencrypted_template_path = root_directory / 'tools' / 'template_unencrypted.html'
    unencrypted_website_path = root_directory / 'secret' / 'website_unencrypted.html'
    markdown_path = root_directory / 'secret' / 'content.md'

    markdown_to_html_with_embedded_images(
        markdown_path=markdown_path,
        html_template_path=unencrypted_template_path,
        html_output_path=unencrypted_website_path,
        placeholder='<!-- CONTENT -->'
    )

    set_html_page_title(unencrypted_website_path, 'Test page title')


if __name__ == '__main__':
    main()