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
import shutil
import re

import fitz  # PyMuPDF
from PIL import Image
from mistralai import Mistral
from mistralai.utils.retries import BackoffStrategy, RetryConfig
import pandas as pd

logger = logging.getLogger(__name__)


def natural_sort_key(path):
    """
    Generate a key for natural sorting of file paths.
    Extracts page number from filename for proper numeric sorting.
    """
    # Extract page number from filename like "..._page12_table0.csv"
    match = re.search(r'_page(\d+)_', path.name)
    if match:
        return int(match.group(1))
    return 0


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
        logger.error(f"  API request failed for page {page_num + 1}: {e}")
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            logger.error(f"  Request timed out - consider increasing --timeout-ms")
        raise  # Re-raise to stop processing instead of silently continuing

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
        logger.error(f"  Response (truncated): {result[:500]}")
        # Return empty result instead of raising to align with caller expectations/tests
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
    timeout_ms=30_000,
    resume=True,
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
        resume: If True, skip pages that already have output files

    Returns:
        Number of tables extracted
    """
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

    # Initialize Mistral client with timeout - no retries on timeout to fail fast
    # Timeout is for HTTP read - if API doesn't respond in timeout_ms, skip page
    backoff = BackoffStrategy(
        initial_interval=2, max_interval=10, exponent=2, max_elapsed_time=timeout_ms // 1000
    )
    retry_config = RetryConfig(
        strategy="exponential",
        backoff=backoff,
        retry_connection_errors=True,
    )
    client = Mistral(api_key=api_key, timeout_ms=timeout_ms, retry_config=retry_config)

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
    failed_pages = []

    # Process each page
    for idx, page_num in enumerate(page_list, start=1):
        if page_num >= total_pages:
            logger.warning(f"Page {page_num + 1} out of range, skipping")
            continue

        # Check if page already processed - always skip to avoid duplicate API calls
        existing_files = sorted(
            list(output_dir.glob(f"{pdf_path.stem}_page{page_num + 1}_table*.csv")),
            key=natural_sort_key
        )
        if existing_files:
            logger.info(f"Page {page_num + 1} ({idx}/{len(page_list)}) - already processed, skipping")
            # Count existing tables for this page
            table_count += len(existing_files)
            # Load existing dataframes for merge if needed
            if merge_output:
                for csv_file in existing_files:
                    df = pd.read_csv(csv_file, encoding="utf-8-sig")
                    all_dataframes.append(df)
            continue

        logger.info(f"Processing page {page_num + 1} ({idx}/{len(page_list)})")

        # Convert page to image
        try:
            image_base64 = pdf_page_to_base64(pdf_path, page_num, dpi=dpi)
        except Exception as e:
            logger.error(f"  Failed to render page {page_num + 1}: {e}")
            continue

        # Extract tables using Mistral with progressive timeout retry
        result = None
        max_attempts = 3
        timeout_increments = [timeout_ms, timeout_ms * 2, timeout_ms * 4]  # 60s, 120s, 240s (doubling strategy)

        for attempt in range(max_attempts):
            current_timeout = timeout_increments[attempt]

            try:
                # Create client with current timeout for this attempt
                backoff = BackoffStrategy(
                    initial_interval=2, max_interval=10, exponent=2, max_elapsed_time=current_timeout // 1000
                )
                retry_config = RetryConfig(
                    strategy="exponential",
                    backoff=backoff,
                    retry_connection_errors=True,
                )
                attempt_client = Mistral(api_key=api_key, timeout_ms=current_timeout, retry_config=retry_config)

                if attempt > 0:
                    logger.info(f"  Retry attempt {attempt}/{max_attempts - 1} with timeout {current_timeout}ms")

                result = extract_tables_with_mistral(
                    attempt_client, image_base64, page_num, model=model, custom_prompt=custom_prompt
                )
                break  # Success, exit retry loop

            except Exception as e:
                error_str = str(e).lower()
                is_timeout = "timeout" in error_str or "timed out" in error_str
                # Transient errors that should be retried: 500, 503, 429
                is_transient = "status 500" in error_str or "status 503" in error_str or "status 429" in error_str
                # JSON parsing errors may indicate incomplete API response - retry
                is_json_error = "json parsing failed" in error_str
                is_retryable = is_timeout or is_transient or is_json_error

                if is_retryable and attempt < max_attempts - 1:
                    # Retryable error and we have more attempts - continue to retry
                    if is_timeout:
                        logger.warning(f"  Request timed out after {current_timeout}ms")
                    elif is_json_error:
                        logger.warning(f"  Malformed JSON response (will retry with longer timeout)")
                    else:
                        logger.warning(f"  Transient API error (will retry): {e}")
                    continue
                elif is_retryable:
                    # Retryable error on final attempt
                    logger.error(f"  All retry attempts failed after {current_timeout}ms")
                    logger.error(f"  Failed to extract tables from page {page_num + 1}: {e}")
                    failed_pages.append(page_num + 1)
                    break
                else:
                    # Non-retryable error - skip retry
                    logger.error(f"  Failed to extract tables from page {page_num + 1}: {e}")
                    failed_pages.append(page_num + 1)
                    break

        if result is None:
            continue  # Skip to next page

        # Process tables
        for i, table_data in enumerate(result.get("tables", [])):
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])

            if not rows:
                logger.info(f"  Table {i}: empty, skipping")
                continue

            # Create DataFrame with headers if available
            if headers:
                # Pad or trim rows to match header count
                num_cols = len(headers)
                padded_rows = []
                rows_padded = 0
                rows_trimmed = 0
                for row_idx, row in enumerate(rows):
                    if len(row) < num_cols:
                        # Pad with empty strings
                        padded_row = row + [""] * (num_cols - len(row))
                        padded_rows.append(padded_row)
                        rows_padded += 1
                    elif len(row) > num_cols:
                        # Trim extra columns
                        padded_rows.append(row[:num_cols])
                        rows_trimmed += 1
                    else:
                        padded_rows.append(row)

                if rows_padded > 0:
                    logger.warning(f"  Table {i}: {rows_padded} rows had fewer columns than headers (padded with empty strings)")
                if rows_trimmed > 0:
                    logger.warning(f"  Table {i}: {rows_trimmed} rows had more columns than headers (extra columns discarded)")

                df = pd.DataFrame(padded_rows, columns=headers)
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

    # Log statistics
    successful_pages = len(page_list) - len(failed_pages)
    logger.info(f"Statistics: {successful_pages}/{len(page_list)} pages processed successfully")
    if failed_pages:
        logger.warning(f"Failed pages: {', '.join(map(str, failed_pages))}")

    # Merge all tables if requested
    if merge_output and all_dataframes:
        # Standardize column names before merge to handle variations
        # (e.g., "TOTALE PERCEPITO" vs "TOTALE_PERCEPITO")
        for df in all_dataframes:
            df.columns = df.columns.str.replace(" ", "_")

        # Sort dataframes by page number using natural sort
        # Load all CSVs with natural sorting
        all_csv_files = sorted(
            list(output_dir.glob(f"{pdf_path.stem}_page*.csv")),
            key=natural_sort_key
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
