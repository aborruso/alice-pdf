"""Tests for prompt_generator module."""

import json
from pathlib import Path
import pytest
from alice_pdf.prompt_generator import generate_prompt_from_schema


@pytest.fixture
def test_schema_path():
    """Path to test schema fixture."""
    return Path(__file__).parent / "fixtures" / "test_schema.yaml"


def test_generate_prompt_from_schema(test_schema_path):
    """Test prompt generation from YAML schema."""
    prompt = generate_prompt_from_schema(test_schema_path)

    # Check prompt contains key elements
    assert "Extract all tables from this image" in prompt
    assert "EXACTLY 3 columns" in prompt
    assert "Column 1: ID - Identifier" in prompt
    assert "Column 2: NAME - Name field" in prompt
    assert "Column 3: VALUE - Numeric value" in prompt


def test_prompt_includes_examples(test_schema_path):
    """Test that examples are included in prompt."""
    prompt = generate_prompt_from_schema(test_schema_path)

    # Check examples are present
    assert '"001"' in prompt or "001" in prompt
    assert "John Doe" in prompt
    assert "100.5" in prompt


def test_prompt_includes_notes(test_schema_path):
    """Test that notes are included as CRITICAL instructions."""
    prompt = generate_prompt_from_schema(test_schema_path)

    assert "CRITICAL:" in prompt
    assert "Keep all columns separate" in prompt
    assert "All rows must have 3 columns" in prompt


def test_prompt_includes_json_format(test_schema_path):
    """Test that prompt includes JSON format specification."""
    prompt = generate_prompt_from_schema(test_schema_path)

    assert "Return ONLY valid JSON" in prompt
    assert '"tables":' in prompt
    assert '"headers":' in prompt
    assert '"rows":' in prompt


def test_prompt_headers_match_schema(test_schema_path):
    """Test that JSON headers match schema column names."""
    prompt = generate_prompt_from_schema(test_schema_path)

    # Extract the headers array from prompt
    assert '["ID", "NAME", "VALUE"]' in prompt


def test_schema_not_found():
    """Test error handling for missing schema file."""
    with pytest.raises(FileNotFoundError):
        generate_prompt_from_schema("nonexistent.yaml")


def test_prompt_with_json_schema(tmp_path):
    """Test prompt generation with JSON schema."""
    json_schema = {
        "name": "json_test",
        "description": "Test JSON schema",
        "columns": [
            {"name": "COL1", "description": "First column", "examples": ["A"]},
            {"name": "COL2", "description": "Second column", "examples": ["B"]}
        ],
        "notes": ["Test note"]
    }

    json_file = tmp_path / "test.json"
    with open(json_file, 'w') as f:
        json.dump(json_schema, f)

    prompt = generate_prompt_from_schema(json_file)

    assert "EXACTLY 2 columns" in prompt
    assert "COL1" in prompt
    assert "COL2" in prompt
    assert "Test note" in prompt
