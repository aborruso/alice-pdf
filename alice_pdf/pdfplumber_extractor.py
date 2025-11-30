#!/usr/bin/env python3
"""
Extract tables from PDF using pdfplumber.
pdfplumber provides robust text extraction from both native and scanned PDFs.
"""

import logging
import pandas as pd
from pathlib import Path
import re

logger = logging.getLogger(__name__)

def distribute_id_cespite_values(df, id_cespite_col="Id. Cespite"):
    """
    Distribute multi-line Id. Cespite values across rows.

    If a cell contains multiple numeric values like:
    "24\n24\n24\n24\n24\n24\n24\n24\n26\n27\n28\n29\n29\n29\n29\n29\n29\n29\n29\n29\n31\n31\n32\n33"

    This function distributes them so each row gets the appropriate value.
    """
    if df.empty or id_cespite_col not in df.columns:
        return df.copy()

    df_fixed = df.copy()

    # Find all rows that need processing (contain multi-line Id. Cespite)
    rows_to_process = []
    for idx, row in df.iterrows():
        id_cell = row[id_cespite_col]

        if pd.notna(id_cell) and '\n' in str(id_cell):
            rows_to_process.append(idx)

    if not rows_to_process:
        return df  # No processing needed

    # Collect all Id. Cespite values
    all_id_values = []
    for idx in rows_to_process:
        id_cell = df.iloc[idx][id_cespite_col]
        lines = [line.strip() for line in str(id_cell).split('\n') if line.strip().isdigit()]
        all_id_values.extend(lines)

    logger.info(f"Found {len(all_id_values)} Id. Cespite values to distribute across {len(rows_to_process)} rows")

    # Distribute values to target rows
    for i, row_idx in enumerate(rows_to_process):
        if i < len(all_id_values):
            df_fixed.loc[row_idx, id_cespite_col] = all_id_values[i]
            logger.debug(f"  Row {row_idx + 1}: assigned Id. Cespite value '{all_id_values[i]}'")
        else:
            # If we run out of values, use the last one
            df_fixed.loc[row_idx, id_cespite_col] = all_id_values[-1]
            logger.debug(f"  Row {row_idx + 1}: assigned last Id. Cespite value '{all_id_values[-1]}'")

    logger.info(f"Distributed Id. Cespite values: {df_fixed[id_cespite_col].tolist()}")
    return df_fixed


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


def extract_tables_with_pdfplumber(
    pdf_path,
    output_dir,
    pages="all",
    merge_output=False,
    resume=True,
    min_rows=1,
    min_cols=1,
    strip_text=True,
):
    """
    Extract tables from PDF using pdfplumber.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for CSV files
        pages: Pages to process ('all', '1', '1-3', '1,3,5')
        merge_output: If True, merge all tables into single CSV
        resume: If True, skip pages that already have output files
        min_rows: Minimum number of rows for a table to be extracted
        min_cols: Minimum number of columns for a table to be extracted
        strip_text: Whether to strip whitespace from extracted text

    Returns:
        Number of tables extracted
    """
    # Import pdfplumber only when needed
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber support required. Install with: pip install pdfplumber"
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

    logger.info(f"Processing PDF: {pdf_path}")
    logger.info(f"Pages: {pages}, Min rows: {min_rows}, Min cols: {min_cols}")

    all_dataframes = []
    table_count = 0
    failed_pages = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

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

            # Process each page
            for idx, page_num in enumerate(page_list, start=1):
                if page_num >= total_pages:
                    logger.warning(f"Page {page_num + 1} out of range, skipping")
                    continue

                # Check if page already processed (resume mode)
                if resume:
                    existing_files = sorted(
                        list(output_dir.glob(f"{pdf_path.stem}_page{page_num + 1}_table*.csv")),
                        key=natural_sort_key
                    )
                    if existing_files:
                        logger.info(
                            f"Page {page_num + 1} ({idx}/{len(page_list)}) - already processed, skipping"
                        )
                        if merge_output:
                            for csv_file in existing_files:
                                df = pd.read_csv(csv_file, encoding="utf-8-sig")
                                all_dataframes.append(df)
                        table_count += len(existing_files)
                        continue

                logger.info(f"Processing page {page_num + 1} ({idx}/{len(page_list)})")

                try:
                    page = pdf.pages[page_num]

                    # Extract tables using pdfplumber's table finder
                    try:
                        tables = page.extract_tables(
                            table_settings={
                                "vertical_strategy": "lines",
                                "horizontal_strategy": "lines",
                                "explicit_vertical_lines": page.curves + page.edges,
                                "explicit_horizontal_lines": page.curves + page.edges,
                                "text_tolerance": 3,
                                "vertical_tolerance": 3,
                                "horizontal_tolerance": 3,
                                "intersection_tolerance": 3,
                            }
                        )
                    except Exception as e:
                        logger.debug(f"  Lines strategy failed: {e}")
                        tables = []

                    if not tables:
                        try:
                            # Try with whitespace strategy if no lines found
                            tables = page.extract_tables(
                                table_settings={
                                    "vertical_strategy": "text",
                                    "horizontal_strategy": "text",
                                    "text_tolerance": 3,
                                    "vertical_tolerance": 3,
                                    "horizontal_tolerance": 3,
                                    "intersection_tolerance": 3,
                                }
                            )
                        except Exception as e:
                            logger.debug(f"  Text strategy failed: {e}")
                            tables = []

                    if not tables:
                        # Try with basic extraction
                        try:
                            tables = page.extract_tables()
                        except Exception as e:
                            logger.debug(f"  Basic extraction failed: {e}")
                            tables = []

                    if not tables:
                        logger.info(f"  No tables found on page {page_num + 1}")
                        continue

                    logger.info(f"  Found {len(tables)} table(s) on page {page_num + 1}")

                    # Process each table
                    for table_idx, table_data in enumerate(tables):
                        # Filter out empty tables that don't meet minimum requirements
                        if (len(table_data) < min_rows or
                            (len(table_data) > 0 and len(table_data[0]) < min_cols)):
                            logger.info(f"  Table {table_idx}: too small ({len(table_data)}x{len(table_data[0]) if table_data else 0}), skipping")
                            continue

                        # Convert to DataFrame
                        try:
                            # Use first row as header if it looks like headers
                            # Check if first row has more non-empty cells than other rows
                            df = pd.DataFrame(table_data)

                            if not df.empty:
                                # Detect if first row is likely a header
                                first_row_non_empty = sum(1 for cell in df.iloc[0] if cell and str(cell).strip())
                                avg_non_empty = df.apply(lambda row: sum(1 for cell in row if cell and str(cell).strip()), axis=1).mean()

                                if first_row_non_empty >= avg_non_empty * 0.8 and first_row_non_empty > 0:
                                    # Use first row as headers
                                    headers = df.iloc[0].fillna('').astype(str)
                                    if strip_text:
                                        headers = headers.str.strip()
                                    df = df[1:].reset_index(drop=True)
                                    df.columns = headers
                                else:
                                    # Generate default column names
                                    num_cols = len(df.columns)
                                    df.columns = [f"col_{i}" for i in range(num_cols)]

                                # Clean data
                                if strip_text:
                                    df = df.map(lambda x: x.strip() if isinstance(x, str) and x else x)

                                # Add page column
                                df.insert(0, "page", page_num + 1)

                                logger.info(f"  Table {table_idx}: {df.shape}")

                                # Apply post-processing fix for Id. Cespite column if needed
                                df_fixed = distribute_id_cespite_values(df, "Id. Cespite")

                                if not df_fixed.equals(df):
                                    logger.info(f"  Applied Id. Cespite distribution fix for {len(df_fixed)} rows")

                                # Save individual CSV
                                output_file = (
                                    output_dir / f"{pdf_path.stem}_page{page_num + 1}_table{table_idx}.csv"
                                )
                                df_fixed.to_csv(output_file, index=False, encoding="utf-8-sig")
                                logger.info(f"    Saved: {output_file}")

                                if merge_output:
                                    all_dataframes.append(df_fixed)

                                table_count += 1

                        except Exception as e:
                            logger.warning(f"  Failed to process table {table_idx}: {e}")
                            continue

                except Exception as e:
                    logger.error(f"  Failed to process page {page_num + 1}: {e}")
                    failed_pages.append(page_num + 1)
                    continue

    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

    # Log statistics
    successful_pages = len(page_list) - len(failed_pages)
    logger.info(f"Statistics: {successful_pages}/{len(page_list)} pages processed successfully")
    if failed_pages:
        logger.warning(f"Failed pages: {', '.join(map(str, failed_pages))}")

    # Merge all tables if requested
    if merge_output and all_dataframes:
        # Standardize column names before merge to handle variations
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