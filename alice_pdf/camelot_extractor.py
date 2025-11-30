#!/usr/bin/env python3
"""
Extract tables from PDF using Camelot.
Camelot works best with native PDFs (not scanned) with clear table structure.
"""

import logging
from pathlib import Path
import pandas as pd
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def _pages_have_text(pdf_path: Path, pages_str: str) -> bool:
    """Return True if any selected page contains extractable text.

    Camelot cannot handle scanned/image-only PDFs. We check the pages the user
    requested and bail out early if none contain text.
    """
    doc = fitz.open(pdf_path)

    # Normalize pages_str to a list of 1-based page numbers
    if pages_str == "all":
        page_numbers = range(1, doc.page_count + 1)
    else:
        # Camelot accepts "1,3,5" or "1-3"; mirror that
        page_numbers = []
        for part in pages_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                page_numbers.extend(range(int(start), int(end) + 1))
            else:
                page_numbers.append(int(part))

    for pno in page_numbers:
        if pno < 1 or pno > doc.page_count:
            continue
        page = doc.load_page(pno - 1)
        if page.get_text().strip():
            return True

    return False


def make_unique_columns(columns):
    """Ensure column labels are unique while preserving original order.

    Pandas DataFrames tolerate duplicate column names, but many operations
    (including the wrapped-row merge below) assume uniqueness. This helper
    appends incremental suffixes (col, col_1, col_2, ...) to duplicates.
    """
    cols = pd.Series(columns, copy=True)
    for dup in cols[cols.duplicated()].unique():
        duplicates_idx = cols.index[cols == dup]
        cols.loc[duplicates_idx] = [
            f"{dup}_{i}" if i != 0 else dup for i in range(len(duplicates_idx))
        ]
    return cols.tolist()  # Return list to avoid Series index issues


def merge_wrapped_rows(df, max_non_null=2):
    """
    Merge rows where address text has wrapped to a new line.

    In some PDFs, when an address is too long, it wraps to a new line.
    Camelot interprets this as a separate row with only the address field populated.

    This function identifies such rows (where only 1-2 columns have data) and merges
    them with the following row.

    Strategy:
    - Find rows with very few non-null values (likely wrapped text)
    - Merge them into the following row by concatenating non-null values

    Args:
        df: DataFrame with potential wrapped rows
        max_non_null: Maximum non-null columns for a row to be considered wrapped (default 2)

    Returns:
        DataFrame with wrapped rows merged
    """
    if df.empty or len(df) < 2:
        return df

    merged_rows = []
    skip_next = False

    for i in range(len(df)):
        if skip_next:
            skip_next = False
            continue

        row = df.iloc[i]

        # Check if this is a wrapped row (very few non-empty values)
        # Count only non-null AND non-empty string values
        non_empty_count = sum(1 for val in row if pd.notna(val) and str(val).strip())

        if non_empty_count <= max_non_null and i < len(df) - 1:
            # Get next row
            next_row = df.iloc[i + 1].copy()

            # Find which column(s) have data in wrapped row
            # Merge those values into next row
            for col_idx in range(len(row)):
                if pd.notna(row.iloc[col_idx]) and str(row.iloc[col_idx]).strip():
                    # If next row has data in same column, concatenate
                    if pd.notna(next_row.iloc[col_idx]):
                        next_row.iloc[col_idx] = f"{row.iloc[col_idx]} {next_row.iloc[col_idx]}"
                    else:
                        # Otherwise just use wrapped row's value
                        next_row.iloc[col_idx] = row.iloc[col_idx]

            merged_rows.append(next_row)
            skip_next = True
            continue

        merged_rows.append(row)

    # Convert to DataFrame using values (not Series) to avoid duplicate index issues
    # Use .values to get raw numpy array without column name information
    if merged_rows:
        result_df = pd.DataFrame([row.values for row in merged_rows], columns=df.columns)
        return result_df.reset_index(drop=True)
    else:
        return df.iloc[:0].copy()  # Return empty DataFrame with same columns


def extract_tables_with_camelot(
    pdf_path,
    output_dir,
    pages="all",
    flavor="lattice",
    merge_output=False,
    resume=True,
    split_text=False,
):
    """
    Extract tables from PDF using Camelot.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for CSV files
        pages: Pages to process ('all', '1', '1-3', '1,3,5')
        flavor: Camelot flavor ('lattice' for bordered tables, 'stream' for non-bordered)
        merge_output: If True, merge all tables into single CSV
        resume: If True, skip pages that already have output files
        split_text: If True, split text that spans multiple cells

    Returns:
        Number of tables extracted
    """
    # Import camelot only when needed
    try:
        import camelot
    except ImportError:
        raise ImportError(
            "Camelot support requires camelot-py. Install with: pip install camelot-py[cv]"
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

    # Parse page range for Camelot format
    if pages == "all":
        pages_str = "all"
    else:
        # Camelot uses 1-based indexing and accepts "1-3,5" format directly
        pages_str = pages

    logger.info(f"Processing PDF: {pdf_path}")
    logger.info(f"Flavor: {flavor}, Pages: {pages_str}")

    # Guard: block scanned PDFs (no extractable text) when using Camelot
    if not _pages_have_text(pdf_path, pages_str):
        raise ValueError(
            "Camelot cannot process scanned/image-only PDFs. "
            "No extractable text found on selected pages. "
            "Use --engine textract or mistral instead."
        )

    all_dataframes = []
    table_count = 0
    failed_pages = []

    try:
        # Extract tables from all specified pages
        tables = camelot.read_pdf(
            str(pdf_path),
            pages=pages_str,
            flavor=flavor,
            split_text=split_text,
        )

        logger.info(f"Found {len(tables)} tables across pages")

        if len(tables) == 0:
            logger.warning("No tables found in PDF")
            return 0

        # Process each table
        for idx, table in enumerate(tables):
            page_num = table.page

            # Check if page already processed (resume mode)
            if resume:
                existing_files = list(
                    output_dir.glob(f"{pdf_path.stem}_page{page_num}_table*.csv")
                )
                if existing_files:
                    logger.info(
                        f"Page {page_num} table {idx} - already processed, skipping"
                    )
                    if merge_output:
                        df = pd.read_csv(existing_files[0], encoding="utf-8-sig")
                        all_dataframes.append(df)
                    table_count += 1
                    continue

            # Convert to DataFrame
            df = table.df

            if df.empty:
                logger.info(f"Page {page_num} table {idx}: empty, skipping")
                continue

            # Use first row as header only if it is mostly populated
            header_non_empty = sum(1 for v in df.iloc[0] if pd.notna(v) and str(v).strip())
            if header_non_empty / len(df.columns) >= 0.6:
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)

            # Ensure columns are unique before row-level operations
            # This must be done BEFORE merge_wrapped_rows since that function
            # relies on df.columns when reconstructing the DataFrame
            df.columns = make_unique_columns(df.columns)

            # Merge wrapped rows AFTER removing header and ensuring unique columns
            df = merge_wrapped_rows(df)

            # Add page column
            df.insert(0, "page", page_num)

            logger.info(f"Page {page_num} table {idx}: {df.shape}")

            # Save individual CSV
            # Count existing tables for this page to determine table index
            existing_count = len(
                list(output_dir.glob(f"{pdf_path.stem}_page{page_num}_table*.csv"))
            )
            output_file = (
                output_dir / f"{pdf_path.stem}_page{page_num}_table{existing_count}.csv"
            )
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            logger.info(f"  Saved: {output_file}")

            if merge_output:
                all_dataframes.append(df)

            table_count += 1

    except Exception as e:
        logger.error(f"Camelot extraction failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

    # Merge all tables if requested
    if merge_output and all_dataframes:
        # Headless merge using positional columns (col_0, col_1, ...), not headers
        max_cols = max(len(df.columns) for df in all_dataframes)
        # Keep first column as page marker, rest are positional
        col_names = ["page"] + [f"col_{i}" for i in range(max_cols - 1)]

        normalized_frames = []
        for df in all_dataframes:
            df = df.copy()

            # Ensure unique columns first to avoid reindex issues
            df.columns = make_unique_columns(df.columns)

            # Pad or truncate to match max_cols
            if len(df.columns) < max_cols:
                # Add missing columns with NaN values
                for i in range(len(df.columns), max_cols):
                    df[f"_pad_{i}"] = pd.NA
            elif len(df.columns) > max_cols:
                logger.warning(
                    f"Column count mismatch: expected {max_cols}, got {len(df.columns)}; truncating extra columns"
                )
                df = df.iloc[:, :max_cols]

            # Now assign standardized column names
            df.columns = col_names
            normalized_frames.append(df)

        merged_df = pd.concat(normalized_frames, ignore_index=True)

        # Sort by page if page column exists
        if "page" in merged_df.columns:
            merged_df = merged_df.sort_values("page").reset_index(drop=True)

        merged_file = output_dir / f"{pdf_path.stem}_merged.csv"
        merged_df.to_csv(merged_file, index=False, encoding="utf-8-sig")
        logger.info(f"Merged all tables into: {merged_file} ({merged_df.shape})")

    return table_count
