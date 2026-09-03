"""Unit tests for settings module."""

from firetwin.settings import FireTwinSettings, check_optional_dependencies, get_system_info


def test_settings_defaults():
    """Test that settings have sensible defaults."""
    settings = FireTwinSettings()
    assert settings.data_root.name == "data"
    assert settings.mlflow_tracking_uri == "./mlruns"


def test_get_system_info():
    """Test system info retrieval."""
    info = get_system_info()
    assert "python_version" in info
    assert "platform" in info
    assert "machine" in info


def test_check_optional_dependencies():
    """Test optional dependency checking."""
    deps = check_optional_dependencies()
    assert isinstance(deps, dict)
    # At minimum, check that the function returns something for common packages
    for pkg in ["torch", "geopandas", "rasterio", "xarray", "mlflow"]:
        assert pkg in deps
        assert "available" in deps[pkg]
