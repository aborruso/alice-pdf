#!/usr/bin/env python3
"""
Alice PDF CLI - Extract tables from PDFs using Camelot, Mistral OCR, or AWS Textract.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

from .extractor import extract_tables
from .prompt_generator import generate_prompt_from_schema

# Setup logging with unbuffered output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)


def main():
    # Clear log files at startup
    for log_file in ["alice_debug.log", "alice_run.log"]:
        log_path = Path(log_file)
        if log_path.exists():
            log_path.unlink()

    parser = argparse.ArgumentParser(
        prog="alice-pdf",
        description="Extract tables from PDFs using Camelot (default), Mistral OCR, AWS Textract, or pdfplumber",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all tables with Camelot (default, free, no API)
  alice-pdf input.pdf output/

  # Extract specific pages
  alice-pdf input.pdf output/ --pages "1-3,5"

  # Merge all tables into one CSV
  alice-pdf input.pdf output/ --merge

  # Use Mistral for scanned PDFs (requires MISTRAL_API_KEY env var)
  alice-pdf input.pdf output/ --engine mistral

  # Use Mistral with table schema for better accuracy
  alice-pdf input.pdf output/ --engine mistral --schema table_schema.yaml

  # Use Camelot stream mode for tables without borders
  alice-pdf input.pdf output/ --camelot-flavor stream

  # Use pdfplumber for robust free extraction (works on native and scanned PDFs)
  alice-pdf input.pdf output/ --engine pdfplumber

  # Use pdfplumber with minimum table size constraints
  alice-pdf input.pdf output/ --engine pdfplumber --pdfplumber-min-rows 2 --pdfplumber-min-cols 3
        """,
    )

    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("output_dir", help="Output directory for CSV files")

    # Engine selection
    parser.add_argument(
        "--engine",
        choices=["mistral", "textract", "camelot", "pdfplumber"],
        default="camelot",
        help="Extraction engine to use (default: camelot - free, no API required)",
    )

    # Common options
    parser.add_argument(
        "--pages",
        default="all",
        help='Pages to process (default: all). Examples: "1", "1-3", "1,3,5"',
    )
    parser.add_argument(
        "--dpi", type=int, default=150, help="Image resolution (default: 150)"
    )
    parser.add_argument(
        "-m", "--merge", action="store_true", help="Merge all tables into single CSV"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Clear output directory and reprocess all pages (default: resume from existing files)",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )

    # Mistral-specific options
    parser.add_argument(
        "--api-key",
        "--mistral-api-key",
        dest="api_key",
        help="Mistral API key (or set MISTRAL_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default="pixtral-12b-2409",
        help="Mistral model to use (default: pixtral-12b-2409)",
    )
    parser.add_argument(
        "--schema",
        type=str,
        help="Path to table schema file (YAML/JSON) for custom prompt generation (Mistral only)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt describing table structure (Mistral only, overrides --schema)",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60_000,
        help="HTTP read timeout for Mistral API in milliseconds (default: 60000)",
    )

    # AWS Textract-specific options
    parser.add_argument(
        "--aws-region",
        help="AWS region for Textract (or set AWS_DEFAULT_REGION env var)",
    )
    parser.add_argument(
        "--aws-access-key-id",
        help="AWS access key ID (or set AWS_ACCESS_KEY_ID env var)",
    )
    parser.add_argument(
        "--aws-secret-access-key",
        help="AWS secret access key (or set AWS_SECRET_ACCESS_KEY env var)",
    )

    # Camelot-specific options
    parser.add_argument(
        "--camelot-flavor",
        choices=["lattice", "stream"],
        default="lattice",
        help="Camelot extraction mode: lattice (bordered tables) or stream (whitespace-based) (default: lattice)",
    )
    parser.add_argument(
        "--camelot-split-text",
        action="store_true",
        help="Split text that spans multiple cells (useful for complex tables with merged cells)",
    )

    # pdfplumber-specific options
    parser.add_argument(
        "--pdfplumber-min-rows",
        type=int,
        default=1,
        help="Minimum number of rows for a table to be extracted (pdfplumber only, default: 1)",
    )
    parser.add_argument(
        "--pdfplumber-min-cols",
        type=int,
        default=1,
        help="Minimum number of columns for a table to be extracted (pdfplumber only, default: 1)",
    )
    parser.add_argument(
        "--pdfplumber-strip-text",
        dest="pdfplumber_strip_text",
        action="store_true",
        default=True,
        help="Strip whitespace from extracted text (pdfplumber only, default: True)",
    )
    parser.add_argument(
        "--no-pdfplumber-strip-text",
        dest="pdfplumber_strip_text",
        action="store_false",
        help="Disable whitespace stripping in pdfplumber output",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    args = parser.parse_args()

    # Auto-switch to Mistral if user provides Mistral-specific options without setting --engine
    if args.engine == "camelot":
        mistral_triggers = any(
            [
                args.api_key,
                os.getenv("MISTRAL_API_KEY"),
                args.schema,
                args.prompt,
                args.model != "pixtral-12b-2409",
            ]
        )
        if mistral_triggers:
            logger.info(
                "Detected Mistral options/credentials without --engine mistral; switching engine to mistral. "
                "Use --engine camelot to force Camelot."
            )
            args.engine = "mistral"

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Shared validation to avoid diverging logic per engine
    def used_options():
        """Return per-engine lists of options actually used (non-default)."""
        return {
            "mistral": [
                ("--schema", bool(args.schema)),
                ("--prompt", bool(args.prompt)),
                ("--model", args.model != "pixtral-12b-2409"),
                ("--api-key", bool(args.api_key or os.getenv("MISTRAL_API_KEY"))),
            ],
            "textract": [
                ("--aws-region", bool(args.aws_region)),
                ("--aws-access-key-id", bool(args.aws_access_key_id)),
                ("--aws-secret-access-key", bool(args.aws_secret_access_key)),
            ],
            "camelot": [
                ("--camelot-flavor", args.camelot_flavor != "lattice"),
                ("--camelot-split-text", args.camelot_split_text),
            ],
            "pdfplumber": [
                ("--pdfplumber-min-rows", args.pdfplumber_min_rows != 1),
                ("--pdfplumber-min-cols", args.pdfplumber_min_cols != 1),
                ("--no-pdfplumber-strip-text", args.pdfplumber_strip_text is False),
            ],
        }

    def first_invalid_for(engine):
        """Return first offending flag list for engines that don't match the selected one."""
        options_map = used_options()
        order = ["mistral", "textract", "camelot", "pdfplumber"]
        for other in order:
            if other == engine:
                continue
            invalid = [flag for flag, used in options_map[other] if used]
            if invalid:
                logger.error(
                    f"Options {', '.join(invalid)} are only compatible with --engine {other}"
                )
                return False
        return True

    if not first_invalid_for(args.engine):
        return 1

    # Route to appropriate engine
    if args.engine == "mistral":
        # Get API key
        api_key = args.api_key or os.getenv("MISTRAL_API_KEY")

        # Try to load from .env file if not found (unless explicitly ignored)
        if not api_key and os.getenv("ALICE_PDF_IGNORE_ENV") != "1":
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("MISTRAL_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break

        if not api_key:
            logger.error(
                "API key required for Mistral. Set MISTRAL_API_KEY env var, use --api-key, or add to .env file"
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
                timeout_ms=args.timeout_ms,
                resume=not args.no_resume,
            )

            logger.info(f"Extraction complete: {num_tables} tables processed")
            return 0

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            if args.debug:
                raise
            return 1

    elif args.engine == "textract":
        # Import textract extractor
        try:
            from .textract_extractor import extract_tables_with_textract
        except ImportError:
            logger.error(
                "Textract support requires boto3. Install with: pip install boto3"
            )
            return 1

        # Get AWS credentials from environment or CLI args
        aws_access_key_id = args.aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = args.aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = args.aws_region or os.getenv("AWS_DEFAULT_REGION")

        try:
            num_tables = extract_tables_with_textract(
                pdf_path=args.pdf_path,
                output_dir=args.output_dir,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_region=aws_region,
                pages=args.pages,
                dpi=args.dpi,
                merge_output=args.merge,
                resume=not args.no_resume,
            )

            logger.info(f"Extraction complete: {num_tables} tables processed")
            return 0

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            if args.debug:
                raise
            return 1

    elif args.engine == "camelot":
        # Import camelot extractor
        try:
            from .camelot_extractor import extract_tables_with_camelot
        except ImportError:
            logger.error(
                "Camelot support requires camelot-py. Install with: pip install camelot-py[cv]"
            )
            return 1

        try:
            num_tables = extract_tables_with_camelot(
                pdf_path=args.pdf_path,
                output_dir=args.output_dir,
                pages=args.pages,
                flavor=args.camelot_flavor,
                merge_output=args.merge,
                resume=not args.no_resume,
                split_text=args.camelot_split_text,
            )

            logger.info(f"Extraction complete: {num_tables} tables processed")
            return 0

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            if args.debug:
                raise
            return 1

    elif args.engine == "pdfplumber":
        # Import pdfplumber extractor
        try:
            from .pdfplumber_extractor import extract_tables_with_pdfplumber
        except ImportError:
            logger.error(
                "pdfplumber support required. Install with: pip install pdfplumber"
            )
            return 1

        try:
            num_tables = extract_tables_with_pdfplumber(
                pdf_path=args.pdf_path,
                output_dir=args.output_dir,
                pages=args.pages,
                merge_output=args.merge,
                resume=not args.no_resume,
                min_rows=args.pdfplumber_min_rows,
                min_cols=args.pdfplumber_min_cols,
                strip_text=args.pdfplumber_strip_text,
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
