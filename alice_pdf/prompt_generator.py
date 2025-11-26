"""
Generate Mistral OCR prompt from table schema template.
"""

import yaml
import json
from pathlib import Path


def generate_prompt_from_schema(schema_file):
    """
    Generate extraction prompt from YAML/JSON schema.

    Args:
        schema_file: Path to schema file (YAML or JSON)

    Returns:
        Prompt string for Mistral OCR
    """
    schema_path = Path(schema_file)

    # Load schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            schema = yaml.safe_load(f)
        else:
            schema = json.load(f)

    # Build prompt
    prompt_parts = [
        "Extract all tables from this image.",
        "",
        f"IMPORTANT: The table has EXACTLY {len(schema['columns'])} columns with this structure:",
        ""
    ]

    # Add column descriptions
    for i, col in enumerate(schema['columns'], 1):
        col_desc = [f"Column {i}: {col['name']} - {col['description']}"]
        if 'examples' in col:
            examples = ', '.join([f'"{ex}"' for ex in col['examples'][:3]])
            col_desc.append(f"  (e.g., {examples})")
        prompt_parts.extend(col_desc)

    prompt_parts.append("")

    # Add notes
    if 'notes' in schema:
        for note in schema['notes']:
            prompt_parts.append(f"CRITICAL: {note}")
        prompt_parts.append("")

    # Add JSON format
    headers = [col['name'] for col in schema['columns']]
    example_rows = []

    # Build example rows from examples
    for row_idx in range(min(2, max(len(col.get('examples', [])) for col in schema['columns']))):
        row = []
        for col in schema['columns']:
            examples = col.get('examples', [])
            row.append(examples[row_idx] if row_idx < len(examples) else "...")
        example_rows.append(row)

    prompt_parts.extend([
        "Return ONLY valid JSON in this format:",
        "{",
        '  "tables": [',
        "    {",
        f'      "headers": {json.dumps(headers)},',
        '      "rows": ['
    ])

    for i, row in enumerate(example_rows):
        row_json = json.dumps(row)
        comma = "," if i < len(example_rows) - 1 else ""
        prompt_parts.append(f'        {row_json}{comma}')

    prompt_parts.extend([
        "      ]",
        "    }",
        "  ]",
        "}",
        "",
        'If no tables found, return: {"tables": []}'
    ])

    return "\n".join(prompt_parts)
