#!/usr/bin/env python3
"""
Extract tables from PDF using Mistral OCR (Pixtral vision model).
Converts PDF pages to images and uses Mistral API for table extraction.
"""

import logging
import base64
from pathlib import Path
from io import BytesIO
import json
import time

import fitz  # PyMuPDF
from PIL import Image
from mistralai import Mistral
import pandas as pd

logger = logging.getLogger(__name__)


def pdf_page_to_base64(pdf_path, page_num, dpi=150):
    """
    Convert PDF page to base64-encoded image.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-based)
        dpi: Resolution for rendering

    Returns:
        Base64-encoded image string
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # Render page to pixmap
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Convert to PIL Image
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    doc.close()
    return img_base64


def extract_tables_with_mistral(
    client, image_base64, page_num, model="pixtral-12b-2409", custom_prompt=None
):
    """
    Extract tables from image using Mistral OCR.

    Args:
        client: Mistral client
        image_base64: Base64-encoded image
        page_num: Page number for reference
        model: Mistral model to use
        custom_prompt: Optional custom prompt describing table structure

    Returns:
        Extracted table data as dict
    """
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = """Extract all tables from this image.
For each table, return structured data in JSON format with:
- headers: list of column headers
- rows: list of rows, each row is a list of cell values

Return ONLY valid JSON in this format:
{
  "tables": [
    {
      "headers": ["col1", "col2", ...],
      "rows": [
        ["val1", "val2", ...],
        ["val1", "val2", ...]
      ]
    }
  ]
}

If no tables found, return: {"tables": []}
"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{image_base64}",
                },
            ],
        }
    ]

    logger.info(f"  Sending page {page_num + 1} to Mistral API...")

    # Rate limiting: 1 request per second + extra buffer
    time.sleep(1.2)

    try:
        response = client.chat.complete(model=model, messages=messages)
    except Exception as e:
        logger.error(f"  API request failed: {e}")
        return {"tables": []}

    result = response.choices[0].message.content
    logger.debug(f"  Raw response: {result}")

    # Try to parse JSON from response
    try:
        # Remove markdown code blocks if present
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        data = json.loads(result)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"  Failed to parse JSON: {e}")
        logger.error(f"  Response: {result}")
        return {"tables": []}


def extract_tables(
    pdf_path,
    output_dir,
    api_key,
    pages="all",
    model="pixtral-12b-2409",
    dpi=150,
    merge_output=False,
    custom_prompt=None,
):
    """
    Extract tables from PDF using Mistral OCR.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for CSV files
        api_key: Mistral API key
        pages: Pages to process ('all', '1', '1-3', '1,3,5')
        model: Mistral model to use
        dpi: Image resolution
        merge_output: If True, merge all tables into single CSV
        custom_prompt: Optional custom prompt describing table structure

    Returns:
        Number of tables extracted
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    # Clear output directory if it exists
    if output_dir.exists():
        import shutil

        shutil.rmtree(output_dir)
        logger.info(f"Cleared output directory: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Mistral client
    client = Mistral(api_key=api_key)

    # Open PDF
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Parse page range
    if pages == "all":
        page_list = list(range(total_pages))
    else:
        page_list = []
        for part in pages.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                page_list.extend(range(start - 1, end))
            else:
                page_list.append(int(part) - 1)

    logger.info(f"Processing {len(page_list)} pages from: {pdf_path}")
    logger.info(f"Model: {model}, DPI: {dpi}")

    all_dataframes = []
    table_count = 0

    # Process each page
    for idx, page_num in enumerate(page_list, start=1):
        if page_num >= total_pages:
            logger.warning(f"Page {page_num + 1} out of range, skipping")
            continue

        logger.info(f"Processing page {page_num + 1} ({idx}/{len(page_list)})")

        # Convert page to image
        image_base64 = pdf_page_to_base64(pdf_path, page_num, dpi=dpi)

        # Extract tables using Mistral
        result = extract_tables_with_mistral(
            client, image_base64, page_num, model=model, custom_prompt=custom_prompt
        )

        # Process tables
        for i, table_data in enumerate(result.get("tables", [])):
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])

            if not rows:
                logger.info(f"  Table {i}: empty, skipping")
                continue

            # Create DataFrame with headers if available
            if headers:
                df = pd.DataFrame(rows, columns=headers)
            else:
                df = pd.DataFrame(rows)

            # Add page column
            df.insert(0, "page", page_num + 1)

            logger.info(f"  Table {i}: {df.shape}")

            # Save individual CSV
            output_file = (
                output_dir / f"{pdf_path.stem}_page{page_num + 1}_table{i}.csv"
            )
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            logger.info(f"    Saved: {output_file}")

            if merge_output:
                all_dataframes.append(df)

            table_count += 1

    doc.close()

    # Merge all tables if requested
    if merge_output and all_dataframes:
        # Standardize column names before merge to handle variations
        # (e.g., "TOTALE PERCEPITO" vs "TOTALE_PERCEPITO")
        for df in all_dataframes:
            df.columns = df.columns.str.replace(" ", "_")

        merged_df = pd.concat(all_dataframes, ignore_index=True)
        merged_df = merged_df.sort_values("page", kind="stable").reset_index(drop=True)

        merged_file = output_dir / f"{pdf_path.stem}_merged.csv"
        merged_df.to_csv(merged_file, index=False, encoding="utf-8-sig")
        logger.info(f"Merged all tables into: {merged_file} ({merged_df.shape})")

    return table_count
