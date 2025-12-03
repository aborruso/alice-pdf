#!/usr/bin/env python3
"""
Extract tables from PDF using Amazon Textract.
Converts PDF pages to images and uses Textract API for table extraction.
"""

import logging
import base64
from pathlib import Path
from io import BytesIO
import json
import time
import shutil
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz  # PyMuPDF
from PIL import Image
import pandas as pd

logger = logging.getLogger(__name__)

# Global client cache for connection reuse
_textract_client_cache = {}


def _get_textract_client(aws_access_key_id, aws_secret_access_key, aws_region):
    """
    Get or create a cached Textract client to reuse connections.
    Uses connection pooling to reduce latency between calls.

    Args:
        aws_access_key_id: AWS access key ID
        aws_secret_access_key: AWS secret access key
        aws_region: AWS region

    Returns:
        Cached boto3 Textract client
    """
    # Create cache key from credentials
    cache_key = (aws_access_key_id, aws_secret_access_key, aws_region)

    if cache_key not in _textract_client_cache:
        import boto3
        from botocore.config import Config

        # Optimize for reduced latency: more connections, faster retries
        config = Config(
            max_pool_connections=50,  # Increase connection pool (default 10)
            retries={'max_attempts': 3, 'mode': 'standard'},
            connect_timeout=5,
            read_timeout=60,
        )

        _textract_client_cache[cache_key] = boto3.client(
            "textract",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
            config=config,
        )
        logger.debug(f"Created new Textract client for region {aws_region} with optimized config")

    return _textract_client_cache[cache_key]


def natural_sort_key(path):
    """
    Generate a key for natural sorting of file paths.
    Extracts page number from filename for proper numeric sorting.
    """
    # Extract page number from filename like "..._page12_table0.csv"
    match = re.search(r"_page(\d+)_", path.name)
    if match:
        return int(match.group(1))
    return 0


def pdf_page_to_base64(pdf_path, page_num, dpi=150):
    """
    Convert PDF page to base64-encoded image with enhanced preprocessing.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-based)
        dpi: Resolution for rendering

    Returns:
        Base64-encoded image string
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # Render page to pixmap at requested DPI (150-200 recommended for most cases)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

    # Convert to PIL Image
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    # Enhance image for better table detection
    from PIL import ImageEnhance, ImageFilter

    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    # Sharpen the image
    img = img.filter(ImageFilter.SHARPEN)

    # Convert to grayscale for better text detection (Textract handles RGB better, but we keep RGB)
    # img = img.convert('L')

    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG", optimize=True)
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    doc.close()
    return img_base64


def extract_tables_with_textract_api(
    textract_client, image_bytes, page_num, max_results=1000, use_async=False
):
    """
    Extract tables from image using Amazon Textract with enhanced options.

    Args:
        textract_client: Textract client
        image_bytes: Image bytes
        page_num: Page number for reference
        max_results: Maximum number of blocks to return
        use_async: Use async processing for better table detection

    Returns:
        Extracted table data as dict
    """
    logger.info(f"  Sending page {page_num + 1} to Textract API...")

    try:
        # Enhanced table detection with multiple feature types
        # Use only TABLES feature to reduce cost; FORMS is ~3x more expensive and not needed here
        response = textract_client.analyze_document(
            Document={"Bytes": image_bytes},
            FeatureTypes=["TABLES"],
        )
        logger.debug(f"  Textract response type: {type(response)}")
        if hasattr(response, "keys"):
            logger.debug(f"  Response keys: {list(response.keys())}")
    except Exception as e:
        logger.error(f"  Textract API request failed for page {page_num + 1}: {e}")
        raise

    # Parse Textract response
    if isinstance(response, dict):
        blocks = response.get("Blocks", [])
    else:
        logger.error(f"  Unexpected response type: {type(response)}")
        logger.debug(f"  Response content: {response}")
        raise ValueError(f"Expected dict, got {type(response)}")

    # Find all table blocks
    table_blocks = [block for block in blocks if block["BlockType"] == "TABLE"]

    tables = []

    for table_idx, table_block in enumerate(table_blocks):
        # Get table cells
        cells = [
            block
            for block in blocks
            if block["BlockType"] == "CELL" and block.get("Confidence", 0) > 30
        ]  # Filter low confidence cells (lowered threshold)

        if not cells:
            continue

        # Organize cells by row and column
        table_data = {}
        max_row = 0
        max_col = 0

        for cell in cells:
            row_index = cell["RowIndex"]
            col_index = cell["ColumnIndex"]

            max_row = max(max_row, row_index)
            max_col = max(max_col, col_index)

            # Get cell text
            cell_text = ""
            cell_relationships = cell.get("Relationships", [])
            if cell_relationships:
                for relationship in cell_relationships:
                    if relationship.get("Type") == "CHILD":
                        child_ids = relationship.get("Ids", [])
                        for block in blocks:
                            if block.get("Id") in child_ids:
                                if block["BlockType"] == "WORD":
                                    cell_text += block.get("Text", "") + " "

            table_data[(row_index, col_index)] = cell_text.strip()

        # Build table matrix
        headers = []
        rows = []

        # First row as headers
        for col in range(1, max_col + 1):
            headers.append(table_data.get((1, col), ""))

        # Remaining rows as data
        for row in range(2, max_row + 1):
            row_data = []
            for col in range(1, max_col + 1):
                row_data.append(table_data.get((row, col), ""))
            rows.append(row_data)

        tables.append({"headers": headers, "rows": rows})

    return {"tables": tables}


def _process_single_page(
    pdf_path, page_num, total_pages, idx, page_list_len, output_dir, dpi, textract_client
):
    """
    Process a single PDF page (thread-safe).
    Returns: (page_num, tables_count, failed, dataframes)
    """
    # Check if page already processed
    existing_files = sorted(
        list(output_dir.glob(f"{pdf_path.stem}_page{page_num + 1}_table*.csv")),
        key=natural_sort_key,
    )
    if existing_files:
        logger.info(
            f"Page {page_num + 1} ({idx}/{page_list_len}) - already processed, skipping"
        )
        # Load existing dataframes for merge
        dataframes = []
        for csv_file in existing_files:
            df = pd.read_csv(csv_file, encoding="utf-8-sig")
            dataframes.append(df)
        return (page_num, len(existing_files), False, dataframes)

    if page_num >= total_pages:
        logger.warning(f"Page {page_num + 1} out of range, skipping")
        return (page_num, 0, True, [])

    logger.info(f"Processing page {page_num + 1} ({idx}/{page_list_len})")

    # Convert page to image (thread-safe: each thread opens its own document)
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Convert to bytes for Textract
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        image_bytes = buffered.getvalue()
        doc.close()
    except Exception as e:
        logger.error(f"  Failed to render page {page_num + 1}: {e}")
        return (page_num, 0, True, [])

    # Extract tables using Textract
    try:
        result = extract_tables_with_textract_api(
            textract_client, image_bytes, page_num
        )
    except Exception as e:
        logger.error(f"  Failed to extract tables from page {page_num + 1}: {e}")
        return (page_num, 0, True, [])

    # Process tables
    tables = result.get("tables", [])
    dataframes = []
    tables_saved = 0

    for i, table_data in enumerate(tables):
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

        dataframes.append(df)
        tables_saved += 1

    return (page_num, tables_saved, False, dataframes)


def extract_tables_with_textract(
    pdf_path,
    output_dir,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    aws_region=None,
    pages="all",
    dpi=150,
    merge_output=False,
    resume=True,
):
    """
    Extract tables from PDF using Amazon Textract sync API with parallel processing.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for CSV files
        aws_access_key_id: AWS access key ID (optional, can use env vars)
        aws_secret_access_key: AWS secret access key (optional, can use env vars)
        aws_region: AWS region (optional, can use env vars)
        pages: Pages to process ('all', '1', '1-3', '1,3,5')
        dpi: Image resolution
        merge_output: If True, merge all tables into single CSV
        resume: If True, skip pages that already have output files

    Returns:
        Number of tables extracted
    """
    # Import boto3 only when needed to avoid dependency issues
    try:
        import boto3
    except ImportError:
        raise ImportError(
            "boto3 is required for Textract support. Install with: pip install boto3"
        )

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Delete merged file if exists
    if merge_output:
        merged_file = output_dir / f"{pdf_path.stem}_merged.csv"
        if merged_file.exists():
            merged_file.unlink()
            logger.info(f"Deleted previous merged file: {merged_file.name}")

    # Always delete the most recently created page CSV
    existing_csvs = list(output_dir.glob(f"{pdf_path.stem}_page*.csv"))
    if existing_csvs:
        most_recent = max(existing_csvs, key=lambda p: p.stat().st_mtime)
        most_recent.unlink()
        logger.info(f"Deleted last created file: {most_recent.name}")

    # Get cached Textract client (reuses connection across calls)
    textract_client = _get_textract_client(
        aws_access_key_id, aws_secret_access_key, aws_region
    )

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
    logger.info(f"DPI: {dpi}")

    # Check if async recommended (implementation planned for future release)
    if len(page_list) > 120:
        logger.warning(
            f"PDF has {len(page_list)} pages (>120). "
            f"For large PDFs, async Textract API provides better performance (single batch job vs {len(page_list)} requests). "
            f"Current version uses sync API with parallel processing (max_workers=5)."
        )

    logger.info(f"Using sync Textract API with parallel processing")
    logger.info(f"Parallel execution: max_workers=5")

    all_dataframes = []
    table_count = 0
    failed_pages = []

    # Process pages in parallel (max 5 workers to respect Textract ~10 req/sec limit)
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all page processing tasks
        future_to_page = {}
        for idx, page_num in enumerate(page_list, start=1):
            future = executor.submit(
                _process_single_page,
                pdf_path,
                page_num,
                total_pages,
                idx,
                len(page_list),
                output_dir,
                dpi,
                textract_client,
            )
            future_to_page[future] = page_num

        # Collect results as they complete
        for future in as_completed(future_to_page):
            page_num, tables_saved, failed, dataframes = future.result()

            if failed:
                failed_pages.append(page_num + 1)
            else:
                table_count += tables_saved
                if merge_output:
                    all_dataframes.extend(dataframes)

    doc.close()

    # Log statistics
    successful_pages = len(page_list) - len(failed_pages)
    logger.info(
        f"Statistics: {successful_pages}/{len(page_list)} pages processed successfully"
    )
    if failed_pages:
        logger.warning(f"Failed pages: {', '.join(map(str, failed_pages))}")

    # Merge all tables if requested
    if merge_output and all_dataframes:
        # Standardize column names before merge
        for df in all_dataframes:
            df.columns = df.columns.str.replace(" ", "_")

        # Sort dataframes by page number using natural sort
        all_csv_files = sorted(
            list(output_dir.glob(f"{pdf_path.stem}_page*.csv")), key=natural_sort_key
        )

        sorted_dataframes = []
        for csv_file in all_csv_files:
            df = pd.read_csv(csv_file, encoding="utf-8-sig")
            df.columns = df.columns.str.replace(" ", "_")
            sorted_dataframes.append(df)

        merged_df = pd.concat(sorted_dataframes, ignore_index=True)

        merged_file = output_dir / f"{pdf_path.stem}_merged.csv"
        merged_df.to_csv(merged_file, index=False, encoding="utf-8-sig")
        logger.info(f"Merged all tables into: {merged_file} ({merged_df.shape})")

    return table_count
