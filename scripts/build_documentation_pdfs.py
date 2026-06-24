"""Build PDF copies of README.md and FEATURES.md with embedded screenshots."""

import argparse
import logging
import os
import sys

import markdown
import weasyprint

_LOGGER = logging.getLogger(__name__)

_DOCUMENTATION_MARKDOWN_FILES = [
  ("README.md", os.path.join("asset", "documentation", "README.pdf")),
  ("FEATURES.md", os.path.join("asset", "documentation", "FEATURES.pdf")),
]

_PDF_STYLESHEET = """
@page {
  size: letter;
  margin: 0.85in;
}

body {
  font-family: sans-serif;
  font-size: 11pt;
  line-height: 1.45;
  color: #111111;
}

h1 {
  font-size: 22pt;
  margin-top: 0;
  margin-bottom: 0.35em;
}

h2 {
  font-size: 15pt;
  margin-top: 1.2em;
  margin-bottom: 0.35em;
  page-break-after: avoid;
}

h3 {
  font-size: 12pt;
  margin-top: 1em;
  page-break-after: avoid;
}

p, li {
  orphans: 3;
  widows: 3;
}

code, pre {
  font-family: monospace;
  font-size: 9.5pt;
}

pre {
  background: #f4f4f4;
  border: 1px solid #dddddd;
  padding: 0.6em;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
  font-size: 10pt;
}

th, td {
  border: 1px solid #cccccc;
  padding: 0.35em 0.55em;
  text-align: left;
  vertical-align: top;
}

th {
  background: #f0f0f0;
}

img {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 0.8em auto;
  border: 1px solid #dddddd;
}

a {
  color: #004488;
  text-decoration: none;
}

ul, ol {
  padding-left: 1.4em;
}
"""


def _resolve_repository_root():
  """Return the repository root containing pyproject.toml."""

  script_directory = os.path.dirname(os.path.abspath(__file__))
  repository_root = os.path.dirname(script_directory)

  return repository_root


def _build_html_document(markdown_text, document_title):
  """Wrap rendered markdown body HTML in a printable document shell."""

  markdown_converter = markdown.Markdown(
    extensions=[
      "tables",
      "fenced_code",
      "sane_lists",
    ],
  )
  body_html = markdown_converter.convert(markdown_text)
  html_document = \
    "<!DOCTYPE html>\n" \
    "<html lang=\"en\">\n" \
    "<head>\n" \
    "<meta charset=\"utf-8\">\n" \
    "<title>{document_title}</title>\n" \
    "</head>\n" \
    "<body>\n" \
    "{body_html}\n" \
    "</body>\n" \
    "</html>".format(
      document_title=document_title,
      body_html=body_html,
    )

  return html_document


def _build_pdf_from_markdown(markdown_path, pdf_path, base_url):
  """Render markdown_path to pdf_path using WeasyPrint."""

  with open(markdown_path, encoding="utf-8") as markdown_file:
    markdown_text = markdown_file.read()

  document_title = os.path.splitext(os.path.basename(markdown_path))[0]
  html_document = _build_html_document(markdown_text, document_title)
  stylesheet = weasyprint.CSS(string=_PDF_STYLESHEET)
  html = weasyprint.HTML(string=html_document, base_url=base_url)

  os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
  html.write_pdf(pdf_path, stylesheets=[stylesheet])
  _LOGGER.info("Wrote %s", pdf_path)


def main(argv=None):
  """Convert README.md and FEATURES.md to PDF under asset/documentation/."""

  logging.basicConfig(level=logging.INFO)

  argument_parser = argparse.ArgumentParser(
    description="Build PDF documentation from README.md and FEATURES.md.",
  )
  argument_parser.add_argument(
    "--output-directory",
    metavar="DIR",
    default=os.path.join("asset", "documentation"),
    help="Directory for PDF output (default: asset/documentation).",
  )

  if argv is None:
    arguments = argument_parser.parse_args()
  else:
    arguments = argument_parser.parse_args(argv)

  repository_root = _resolve_repository_root()
  output_directory = arguments.output_directory

  if not os.path.isabs(output_directory):
    output_directory = os.path.join(repository_root, output_directory)

  for markdown_filename, pdf_relative_path in _DOCUMENTATION_MARKDOWN_FILES:
    markdown_path = os.path.join(repository_root, markdown_filename)
    pdf_filename = os.path.basename(pdf_relative_path)
    pdf_path = os.path.join(output_directory, pdf_filename)
    _build_pdf_from_markdown(markdown_path, pdf_path, repository_root)

  return 0


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
