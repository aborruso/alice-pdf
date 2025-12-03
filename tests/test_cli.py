"""Tests for CLI module."""

import sys
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
from alice_pdf.cli import main


@pytest.fixture
def mock_extract_tables():
    """Mock extract_tables function."""
    with patch('alice_pdf.cli.extract_tables') as mock:
        mock.return_value = 5
        yield mock


@pytest.fixture
def test_schema_path():
    """Path to test schema fixture."""
    return str(Path(__file__).parent / "fixtures" / "test_schema.yaml")


def test_cli_help():
    """Test CLI help output."""
    with patch.object(sys, 'argv', ['alice-pdf', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_version():
    """Test CLI version output."""
    with patch.object(sys, 'argv', ['alice-pdf', '--version']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_missing_api_key(mock_extract_tables):
    """Test error when API key is missing."""
    with patch.object(sys, 'argv', ['alice-pdf', 'test.pdf', 'output/']), \
         patch.dict('os.environ', {'ALICE_PDF_IGNORE_ENV': '1'}, clear=True):
        result = main()
        assert result == 1
        mock_extract_tables.assert_not_called()


def test_cli_with_api_key_flag(mock_extract_tables):
    """Test CLI with --api-key flag."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key'
    ]):
        result = main()
        assert result == 0
        mock_extract_tables.assert_called_once()
        call_kwargs = mock_extract_tables.call_args[1]
        assert call_kwargs['pages'] == 'all'
        assert call_kwargs['model'] == 'pixtral-12b-2409'


def test_cli_with_env_var(mock_extract_tables):
    """Test CLI with MISTRAL_API_KEY environment variable."""
    with patch.object(sys, 'argv', ['alice-pdf', 'test.pdf', 'output/']), \
         patch.dict('os.environ', {'MISTRAL_API_KEY': 'env_key'}):
        result = main()
        assert result == 0
        mock_extract_tables.assert_called_once()


def test_cli_default_engine_mistral_routes(mock_extract_tables):
    """Default engine mistral should call extract_tables."""
    with patch.object(sys, 'argv', ['alice-pdf', 'test.pdf', 'output/', '--api-key', 'k']):
        result = main()
        assert result == 0
        mock_extract_tables.assert_called_once()


def test_cli_textract_routes_and_env_creds():
    """Textract engine should route to extract_tables_with_textract and pick env creds."""
    import types

    mock_module = types.ModuleType('alice_pdf.textract_extractor')
    mock_module.extract_tables_with_textract = Mock(return_value=2)

    with patch.object(sys, 'argv', [
        'alice-pdf', 'test.pdf', 'output/', '--engine', 'textract', '--aws-region', 'eu-west-1'
    ]), patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'env_access',
        'AWS_SECRET_ACCESS_KEY': 'env_secret',
    }, clear=True), patch.dict('sys.modules', {'alice_pdf.textract_extractor': mock_module}):
        result = main()
        assert result == 0
        mock_module.extract_tables_with_textract.assert_called_once()
        kwargs = mock_module.extract_tables_with_textract.call_args[1]
        assert kwargs['aws_access_key_id'] == 'env_access'
        assert kwargs['aws_secret_access_key'] == 'env_secret'
        assert kwargs['aws_region'] == 'eu-west-1'


def test_cli_textract_import_error():
    """If textract_extractor import fails, CLI should exit with error."""
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == 'alice_pdf.textract_extractor' or name.endswith('.textract_extractor'):
            raise ImportError("no textract")
        return real_import(name, *args, **kwargs)

    with patch.object(sys, 'argv', ['alice-pdf', 'test.pdf', 'out/', '--engine', 'textract']), \
         patch('builtins.__import__', side_effect=fake_import):
        result = main()
        assert result == 1


def test_cli_textract_cli_creds_override_env():
    """CLI AWS creds should override env vars for textract engine."""
    import types

    mock_module = types.ModuleType('alice_pdf.textract_extractor')
    mock_module.extract_tables_with_textract = Mock(return_value=1)

    with patch.object(sys, 'argv', [
        'alice-pdf', 'test.pdf', 'output/', '--engine', 'textract',
        '--aws-region', 'cli-region',
        '--aws-access-key-id', 'cli-ak',
        '--aws-secret-access-key', 'cli-sk'
    ]), patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'env_access',
        'AWS_SECRET_ACCESS_KEY': 'env_secret',
        'AWS_DEFAULT_REGION': 'env-region'
    }, clear=True), patch.dict('sys.modules', {'alice_pdf.textract_extractor': mock_module}):
        result = main()
        assert result == 0
        kwargs = mock_module.extract_tables_with_textract.call_args[1]
        assert kwargs['aws_access_key_id'] == 'cli-ak'
        assert kwargs['aws_secret_access_key'] == 'cli-sk'
        assert kwargs['aws_region'] == 'cli-region'


def test_cli_textract_missing_boto3_error():
    """Missing boto3 should cause textract engine to error cleanly."""
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == 'boto3':
            raise ImportError('no boto3')
        return real_import(name, *args, **kwargs)

    with patch.object(sys, 'argv', ['alice-pdf', 'test.pdf', 'out/', '--engine', 'textract']), \
         patch('builtins.__import__', side_effect=fake_import):
        result = main()
        assert result == 1


def test_cli_camelot_stream_routes():
    """Camelot stream flavor should be passed through to extractor."""
    import types

    mock_module = types.ModuleType('alice_pdf.camelot_extractor')
    mock_module.extract_tables_with_camelot = Mock(return_value=1)

    with patch.object(sys, 'argv', [
        'alice-pdf', 'test.pdf', 'out/', '--engine', 'camelot', '--camelot-flavor', 'stream'
    ]), patch.dict('sys.modules', {'alice_pdf.camelot_extractor': mock_module}), \
         patch.dict('os.environ', {'MISTRAL_API_KEY': ''}, clear=False):
        result = main()
        assert result == 0
        kwargs = mock_module.extract_tables_with_camelot.call_args[1]
        assert kwargs['flavor'] == 'stream'


def test_cli_camelot_lattice_default():
    """Camelot default flavor should be lattice."""
    import types

    mock_module = types.ModuleType('alice_pdf.camelot_extractor')
    mock_module.extract_tables_with_camelot = Mock(return_value=1)

    with patch.object(sys, 'argv', [
        'alice-pdf', 'test.pdf', 'out/', '--engine', 'camelot'
    ]), patch.dict('sys.modules', {'alice_pdf.camelot_extractor': mock_module}), \
         patch.dict('os.environ', {'MISTRAL_API_KEY': ''}, clear=False):
        result = main()
        assert result == 0
        kwargs = mock_module.extract_tables_with_camelot.call_args[1]
        assert kwargs['flavor'] == 'lattice'


def test_cli_camelot_missing_dep_error():
    """Missing camelot dependency should produce clear error."""
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == 'alice_pdf.camelot_extractor' or name.endswith('.camelot_extractor'):
            raise ImportError('no camelot')
        return real_import(name, *args, **kwargs)

    with patch.object(sys, 'argv', ['alice-pdf', 'test.pdf', 'out/', '--engine', 'camelot']), \
         patch('builtins.__import__', side_effect=fake_import):
        result = main()
        assert result == 1


def test_cli_pdfplumber_strip_text_toggle():
    """pdfplumber engine should honor --no-pdfplumber-strip-text."""
    import types

    mock_module = types.ModuleType('alice_pdf.pdfplumber_extractor')
    mock_module.extract_tables_with_pdfplumber = Mock(return_value=1)

    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'out/',
        '--engine',
        'pdfplumber',
        '--no-pdfplumber-strip-text'
    ]), patch.dict('sys.modules', {'alice_pdf.pdfplumber_extractor': mock_module}), \
         patch.dict('os.environ', {'MISTRAL_API_KEY': ''}, clear=False):
        result = main()
        assert result == 0
        kwargs = mock_module.extract_tables_with_pdfplumber.call_args[1]
        assert kwargs['strip_text'] is False


def test_cli_with_pages_option(mock_extract_tables):
    """Test CLI with --pages option."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--pages',
        '1-3,5'
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        assert call_kwargs['pages'] == '1-3,5'


def test_cli_with_merge_option(mock_extract_tables):
    """Test CLI with --merge option."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--merge'
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        assert call_kwargs['merge_output'] is True


def test_cli_with_custom_model(mock_extract_tables):
    """Test CLI with --model option."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--model',
        'custom-model'
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        assert call_kwargs['model'] == 'custom-model'


def test_cli_with_custom_dpi(mock_extract_tables):
    """Test CLI with --dpi option."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--dpi',
        '300'
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        assert call_kwargs['dpi'] == 300


def test_cli_with_schema(mock_extract_tables, test_schema_path):
    """Test CLI with --schema option."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--schema',
        test_schema_path
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        # Should have custom_prompt generated from schema
        assert call_kwargs['custom_prompt'] is not None
        assert 'Extract all tables' in call_kwargs['custom_prompt']


def test_cli_with_custom_prompt(mock_extract_tables):
    """Test CLI with --prompt option."""
    custom_prompt = "My custom extraction prompt"
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--prompt',
        custom_prompt
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        assert call_kwargs['custom_prompt'] == custom_prompt


def test_cli_prompt_overrides_schema(mock_extract_tables, test_schema_path):
    """Test that --prompt overrides --schema."""
    custom_prompt = "Override prompt"
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--schema',
        test_schema_path,
        '--prompt',
        custom_prompt
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        # Prompt should override schema
        assert call_kwargs['custom_prompt'] == custom_prompt


def test_cli_schema_not_found(mock_extract_tables):
    """Test error handling when schema file doesn't exist."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--schema',
        'nonexistent.yaml'
    ]):
        result = main()
        assert result == 1
        mock_extract_tables.assert_not_called()


def test_cli_extraction_failure(mock_extract_tables):
    """Test error handling when extraction fails."""
    mock_extract_tables.side_effect = Exception("Extraction failed")

    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key'
    ]):
        result = main()
        assert result == 1


def test_cli_debug_mode(mock_extract_tables):
    """Test CLI with --debug flag."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--debug'
    ]), patch('logging.getLogger') as mock_logger:
        result = main()
        assert result == 0
        # Debug logging should be enabled
        mock_logger.return_value.setLevel.assert_called()


def test_cli_all_options_combined(mock_extract_tables):
    """Test CLI with all options combined."""
    with patch.object(sys, 'argv', [
        'alice-pdf',
        'test.pdf',
        'output/',
        '--api-key',
        'test_key',
        '--pages',
        '1-10',
        '--model',
        'custom-model',
        '--dpi',
        '200',
        '--merge',
        '--prompt',
        'Custom prompt',
        '--debug'
    ]):
        result = main()
        assert result == 0
        call_kwargs = mock_extract_tables.call_args[1]
        assert call_kwargs['pages'] == '1-10'
        assert call_kwargs['model'] == 'custom-model'
        assert call_kwargs['dpi'] == 200
        assert call_kwargs['merge_output'] is True
        assert call_kwargs['custom_prompt'] == 'Custom prompt'
