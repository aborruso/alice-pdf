# Alice PDF

Alice PDF is a tool based on Mistral OCR, designed to transform PDFs with tables into machine-readable CSV tables.

## How it works

- Takes a PDF as input
- Creates a temporary raster copy of the PDF at 150 DPI
- Optionally allows the user to choose a page range or a list of pages via parameter
- Sends the PDF along with a YAML template describing the table structure (optional but highly recommended)
- Obtains one CSV per page and merges them into a single file

## Implementation

It will be a CLI installable from PyPI using uv
