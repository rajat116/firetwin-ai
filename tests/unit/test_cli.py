"""Unit tests for the CLI module."""

from click.testing import CliRunner
from final_extent_helpers import make_final_extent_case

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


def test_run_baselines_rejects_final_extent_case(tmp_path):
    """Horizon baseline command should refuse final-extent-only cases."""
    case_path = tmp_path / "final_case.zarr"
    make_final_extent_case().save_to_zarr(case_path)

    runner = CliRunner()
    result = runner.invoke(main, ["run-baselines", str(case_path)])

    assert result.exit_code != 0
    assert "target_type=final_burned_extent" in result.output
    assert "evaluate-final-extent" in result.output


def test_evaluate_rejects_final_extent_case(tmp_path):
    """Horizon evaluation command should refuse final-extent-only cases."""
    case_path = tmp_path / "final_case.zarr"
    forecasts_dir = tmp_path / "forecasts"
    forecasts_dir.mkdir()
    make_final_extent_case().save_to_zarr(case_path)

    runner = CliRunner()
    result = runner.invoke(main, ["evaluate", str(case_path), str(forecasts_dir)])

    assert result.exit_code != 0
    assert "target_type=final_burned_extent" in result.output
    assert "evaluate-final-extent" in result.output


def test_evaluate_final_extent_command(tmp_path):
    """Final-extent CLI command should evaluate real-data diagnostics."""
    case_path = tmp_path / "final_case.zarr"
    make_final_extent_case().save_to_zarr(case_path)

    runner = CliRunner()
    result = runner.invoke(main, ["evaluate-final-extent", str(case_path)])

    assert result.exit_code == 0
    assert "Final Extent Baselines" in result.output
    assert "burnable_fuel_mask" in result.output
