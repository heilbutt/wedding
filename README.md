# Website for the wedding of the Hermanas

This repository is both the website for our wedding, and the infrastructure to deploy it.

The website content is generated from Markdown source files and an HTML template. The website itself is private and therefore encrypted behind PageCrypt ([GitHub](https://github.com/lupine-dev/PageCrypt), [Website](https://pagecrypt.lupine.dev/)). This is automated with the script `build_website.py`. The website is deployed via [GitHub pages](https://docs.github.com/en/pages).

For using it for your own project (wedding?), refer to the instructions below.

## Installation

Preferable create a new virtual environment. I use Python 3.12.12 but many other versions should work. Install dependencies for website generation script and [lupine-dev/PageCrypt](https://github.com/lupine-dev/PageCrypt) submodule:

```sh
pip install -r requirements.txt -r PageCrypt/python/requirements.txt
```

## Usage

### Build a template

Start from the HTML template `template/template.html`. You can do basically whatever you want, but the following elements should be present:
- A link to the stylesheet `docs/style.css`
- A page `<title>`, this can be modified by the script
- Some container where the content generated from Markdown will be inserted. By default this is a `<div>` with the ID `content-container`.

Note that the template here refers to an image `banner.webp` that does not exist in the source directory on GitHub. Insert your own!

### Configure the website

A minimal TOML file configures the website password protection and languages, by default `source-secret/website-config.toml`. See `source-secret/website-config-example.toml` for an example.

You can add multiple languages here, for each of which a Markdown file must exist. This must not be real languages, they are just string identifiers.

### Write Markdown content

For each language listed in the TOML, create a `source-secret/content-$LANGUAGE.md` Markdown file. Fill it with content you desire. 

Each Markdown should have exactly one H1-level heading. The script will read this heading and insert it in the HTML `<title>` tag.

You may also add images. All images will be encoded as Base64 directly into the HTML file, so they will also by encrypted by PageCrypt.

Refer to `source-secret/content-english-example.md` (which includes `source-secret/image-example.webp`) as an example.

### Run the script

Execute the Python script `build_website.py`.

It should just work™️ if you followed the instructions and example files above. Feel free to comment/modify the `main` function if you don't need some features.

By default, the script
1. Reads the configuration `source-secret/website-config.toml`.
2. Creates *unencrypted* HTML files `docs-secret/$LANGUAGE.html` based on the template `template/template.html` and the source Markdown `source-secret/content-$LANGUAGE.md`. All referenced images will be embedded in Base64.
3. Encrypts the pages using PageCrypt, outputting to `docs/$LANGUAGE.html`
4. Ensures that page titles and link to stylesheet `docs/style.css` are consistent for intermediate and final output.
5. Makes external links open in a new tab.
6. Repeats steps 2-5 for all `$LANGUAGE`s.

## Deployed website structure

The website files is located under `docs/` and deployed via [GitHub pages](https://docs.github.com/en/pages).

One unencrypted index page links to the content site in different lanugages. The content pages are all behind PageCrypt password protection.

```
index.html
├──english.html
├──german.html
└──spanish.html
```