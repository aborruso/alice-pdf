"""Tests for extractor module."""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import pandas as pd
from alice_pdf.extractor import (
    pdf_page_to_base64,
    extract_tables_with_mistral,
    extract_tables
)


@pytest.fixture
def mock_mistral_response():
    """Mock Mistral API response."""
    return {
        "tables": [
            {
                "headers": ["ID", "NAME", "VALUE"],
                "rows": [
                    ["001", "John Doe", "100.5"],
                    ["002", "Jane Smith", "250.75"]
                ]
            }
        ]
    }


@pytest.fixture
def mock_mistral_response_with_markdown():
    """Mock Mistral API response wrapped in markdown code blocks."""
    return '''```json
{
    "tables": [
        {
            "headers": ["COL1", "COL2"],
            "rows": [["A", "B"], ["C", "D"]]
        }
    ]
}
```'''


def test_extract_tables_with_mistral_success(mock_mistral_response):
    """Test successful table extraction from Mistral API."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_mistral_response)
    mock_client.chat.complete.return_value = mock_response

    result = extract_tables_with_mistral(
        mock_client,
        "fake_base64_image",
        page_num=0
    )

    assert "tables" in result
    assert len(result["tables"]) == 1
    assert result["tables"][0]["headers"] == ["ID", "NAME", "VALUE"]
    assert len(result["tables"][0]["rows"]) == 2


def test_extract_tables_with_mistral_markdown_format(mock_mistral_response_with_markdown):
    """Test extraction with markdown-formatted response."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = mock_mistral_response_with_markdown
    mock_client.chat.complete.return_value = mock_response

    result = extract_tables_with_mistral(
        mock_client,
        "fake_base64_image",
        page_num=0
    )

    assert "tables" in result
    assert len(result["tables"]) == 1
    assert result["tables"][0]["headers"] == ["COL1", "COL2"]


def test_extract_tables_with_mistral_custom_prompt():
    """Test extraction with custom prompt."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"tables": []}'
    mock_client.chat.complete.return_value = mock_response

    custom_prompt = "Extract my custom table format"

    extract_tables_with_mistral(
        mock_client,
        "fake_base64_image",
        page_num=0,
        custom_prompt=custom_prompt
    )

    # Check that custom prompt was used
    call_args = mock_client.chat.complete.call_args
    messages = call_args[1]["messages"]
    assert messages[0]["content"][0]["text"] == custom_prompt


def test_extract_tables_with_mistral_invalid_json():
    """Test handling of invalid JSON response."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is not valid JSON"
    mock_client.chat.complete.return_value = mock_response

    result = extract_tables_with_mistral(
        mock_client,
        "fake_base64_image",
        page_num=0
    )

    # Should return empty tables on error
    assert result == {"tables": []}


def test_extract_tables_with_mistral_model_parameter():
    """Test that model parameter is passed correctly."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"tables": []}'
    mock_client.chat.complete.return_value = mock_response

    extract_tables_with_mistral(
        mock_client,
        "fake_base64_image",
        page_num=0,
        model="custom-model"
    )

    call_args = mock_client.chat.complete.call_args
    assert call_args[1]["model"] == "custom-model"


@patch('alice_pdf.extractor.fitz')
def test_pdf_page_to_base64(mock_fitz):
    """Test PDF page to base64 conversion."""
    # Mock PyMuPDF objects
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_pix = MagicMock()

    mock_pix.width = 100
    mock_pix.height = 100
    mock_pix.samples = b'\x00' * (100 * 100 * 3)

    mock_page.get_pixmap.return_value = mock_pix
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz.open.return_value = mock_doc

    result = pdf_page_to_base64("test.pdf", 0, dpi=150)

    # Check that result is a base64 string
    assert isinstance(result, str)
    assert len(result) > 0

    # Check that PyMuPDF was called correctly
    mock_fitz.open.assert_called_once_with("test.pdf")
    mock_doc.__getitem__.assert_called_once_with(0)
    mock_doc.close.assert_called_once()


@patch('alice_pdf.extractor.Mistral')
@patch('alice_pdf.extractor.fitz')
@patch('alice_pdf.extractor.shutil')
def test_extract_tables_page_range(mock_shutil, mock_fitz, mock_mistral_class):
    """Test extraction with page range specification."""
    # Mock PDF document
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 10
    mock_page = MagicMock()
    mock_pix = MagicMock()
    mock_pix.width = 100
    mock_pix.height = 100
    mock_pix.samples = b'\x00' * (100 * 100 * 3)
    mock_page.get_pixmap.return_value = mock_pix
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz.open.return_value = mock_doc

    # Mock Mistral client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "tables": [
            {"headers": ["A", "B"], "rows": [["1", "2"]]}
        ]
    })
    mock_client.chat.complete.return_value = mock_response
    mock_mistral_class.return_value = mock_client

    # Create temporary output directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        num_tables = extract_tables(
            "test.pdf",
            tmp_dir,
            "fake_api_key",
            pages="1,3,5"
        )

        # Should process 3 pages
        assert mock_client.chat.complete.call_count == 3
        assert num_tables == 3


@patch('alice_pdf.extractor.Mistral')
@patch('alice_pdf.extractor.fitz')
@patch('alice_pdf.extractor.shutil')
def test_extract_tables_merge_output(mock_shutil, mock_fitz, mock_mistral_class, tmp_path):
    """Test table merging functionality."""
    # Mock PDF document
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_page = MagicMock()
    mock_pix = MagicMock()
    mock_pix.width = 100
    mock_pix.height = 100
    mock_pix.samples = b'\x00' * (100 * 100 * 3)
    mock_page.get_pixmap.return_value = mock_pix
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz.open.return_value = mock_doc

    # Mock Mistral client with different responses per page
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]

    responses = [
        json.dumps({"tables": [{"headers": ["A", "B"], "rows": [["1", "2"]]}]}),
        json.dumps({"tables": [{"headers": ["A", "B"], "rows": [["3", "4"]]}]})
    ]
    mock_response.choices[0].message.content = responses[0]
    mock_client.chat.complete.side_effect = [
        Mock(choices=[Mock(message=Mock(content=responses[0]))]),
        Mock(choices=[Mock(message=Mock(content=responses[1]))])
    ]
    mock_mistral_class.return_value = mock_client

    output_dir = tmp_path / "output"

    num_tables = extract_tables(
        "test.pdf",
        str(output_dir),
        "fake_api_key",
        pages="all",
        merge_output=True
    )

    # Check merged file exists
    merged_file = output_dir / "test_merged.csv"
    assert merged_file.exists()

    # Check merged data
    df = pd.read_csv(merged_file)
    assert len(df) == 2
    assert "page" in df.columns
    assert list(df["page"]) == [1, 2]


def test_extract_tables_empty_response():
    """Test handling of empty table response."""
    with patch('alice_pdf.extractor.Mistral') as mock_mistral_class, \
         patch('alice_pdf.extractor.fitz') as mock_fitz, \
         patch('alice_pdf.extractor.shutil'):

        # Mock PDF
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.width = 100
        mock_pix.height = 100
        mock_pix.samples = b'\x00' * (100 * 100 * 3)
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Mock Mistral with empty tables
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"tables": []}'
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            num_tables = extract_tables(
                "test.pdf",
                tmp_dir,
                "fake_api_key",
                pages="1"
            )

            assert num_tables == 0
