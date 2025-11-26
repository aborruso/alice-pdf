#!/usr/bin/env python3
"""
Alice PDF CLI - Extract tables from PDFs using Mistral OCR.
"""

import sys
import argparse
import logging
from pathlib import Path

from .extractor import extract_tables
from .prompt_generator import generate_prompt_from_schema

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="alice-pdf",
        description="Extract tables from PDFs using Mistral OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all tables (requires MISTRAL_API_KEY env var)
  alice-pdf input.pdf output/

  # Extract specific pages
  alice-pdf input.pdf output/ --pages "1-3,5"

  # Merge all tables into one CSV
  alice-pdf input.pdf output/ --merge

  # Use table schema for better accuracy
  alice-pdf input.pdf output/ --schema table_schema.yaml

  # Use API key directly
  alice-pdf input.pdf output/ --api-key "your-key-here"
        """,
    )

    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("output_dir", help="Output directory for CSV files")
    parser.add_argument(
        "--api-key", help="Mistral API key (or set MISTRAL_API_KEY env var)"
    )
    parser.add_argument(
        "--pages",
        default="all",
        help='Pages to process (default: all). Examples: "1", "1-3", "1,3,5"',
    )
    parser.add_argument(
        "--model",
        default="pixtral-12b-2409",
        help="Mistral model to use (default: pixtral-12b-2409)",
    )
    parser.add_argument(
        "--dpi", type=int, default=150, help="Image resolution (default: 150)"
    )
    parser.add_argument(
        "-m", "--merge", action="store_true", help="Merge all tables into single CSV"
    )
    parser.add_argument(
        "--schema",
        type=str,
        help="Path to table schema file (YAML/JSON) for custom prompt generation",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt describing table structure (overrides --schema)",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get API key
    import os
    from pathlib import Path

    api_key = args.api_key or os.getenv("MISTRAL_API_KEY")

    # Try to load from .env file if not found
    if not api_key:
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("MISTRAL_API_KEY=") or line.startswith(
                        "api_key="
                    ):
                        api_key = line.split("=", 1)[1].strip().strip('"')
                        break

    if not api_key:
        logger.error(
            "API key required. Set MISTRAL_API_KEY env var, use --api-key, or add to .env file"
        )
        return 1

    # Generate prompt from schema if provided
    custom_prompt = args.prompt
    if args.schema and not custom_prompt:
        try:
            custom_prompt = generate_prompt_from_schema(args.schema)
            logger.info(f"Generated prompt from schema: {args.schema}")
        except Exception as e:
            logger.error(f"Failed to generate prompt from schema: {e}")
            if args.debug:
                raise
            return 1

    try:
        num_tables = extract_tables(
            args.pdf_path,
            args.output_dir,
            api_key,
            pages=args.pages,
            model=args.model,
            dpi=args.dpi,
            merge_output=args.merge,
            custom_prompt=custom_prompt,
        )

        logger.info(f"Extraction complete: {num_tables} tables processed")
        return 0

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        if args.debug:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
