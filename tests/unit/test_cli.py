"""Unit tests for the CLI module."""

from click.testing import CliRunner

from firetwin import __version__
from firetwin.cli import _has_cds_credentials, main


def test_version():
    """Test that version command works."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help():
    """Test that help command works."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "FireTwin" in result.output


def test_doctor_command():
    """Test that doctor command runs without errors."""
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "FireTwin Doctor" in result.output
    assert "System Information" in result.output


def test_cds_credentials_detects_cdsapirc(tmp_path):
    """Test CDS credentials can be detected from the standard cdsapi file."""
    cdsapirc = tmp_path / ".cdsapirc"
    assert not _has_cds_credentials(cdsapirc)

    cdsapirc.write_text(
        "url: https://cds.climate.copernicus.eu/api\nkey: token\n",
        encoding="utf-8",
    )
    assert _has_cds_credentials(cdsapirc)
