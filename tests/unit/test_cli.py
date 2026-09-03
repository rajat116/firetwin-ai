"""Unit tests for the CLI module."""

from click.testing import CliRunner

from firetwin import __version__
from firetwin.cli import main


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
