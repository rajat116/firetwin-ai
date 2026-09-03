"""Tests for baseline forecast models."""

import numpy as np

from firetwin.data.synthetic import generate_synthetic_fire_case
from firetwin.models import EllipticalBaseline, PersistenceBaseline, RadialBaseline


def test_persistence_baseline():
    """Test persistence baseline produces valid forecasts."""
    case = generate_synthetic_fire_case(
        case_id="test_pers",
        grid_size=(20, 20),
        n_forecast_hours=6,
        seed=42,
    )

    model = PersistenceBaseline()
    forecasts = model.forecast(case, [3.0, 6.0])

    assert len(forecasts) == 2
    assert 3.0 in forecasts
    assert 6.0 in forecasts

    # Persistence should keep initial state unchanged
    np.testing.assert_array_equal(forecasts[3.0].burned, case.initial_state.burned)
    np.testing.assert_array_equal(forecasts[6.0].burned, case.initial_state.burned)


def test_radial_baseline():
    """Test radial baseline spreads from initial state."""
    case = generate_synthetic_fire_case(
        case_id="test_radial",
        grid_size=(30, 30),
        n_forecast_hours=6,
        seed=123,
    )

    model = RadialBaseline(spread_rate_m_h=50.0)
    forecasts = model.forecast(case, [3.0, 6.0])

    # Should produce forecasts
    assert len(forecasts) == 2

    # Burned area should increase
    initial_burned = case.initial_state.burned.sum()
    assert forecasts[3.0].burned.sum() >= initial_burned
    assert forecasts[6.0].burned.sum() >= forecasts[3.0].burned.sum()

    # Should not exceed grid size
    assert forecasts[6.0].burned.sum() <= case.grid_shape[0] * case.grid_shape[1]


def test_elliptical_baseline():
    """Test elliptical baseline accounts for wind."""
    case = generate_synthetic_fire_case(
        case_id="test_ellip",
        grid_size=(40, 40),
        n_forecast_hours=6,
        seed=456,
    )

    model = EllipticalBaseline(base_spread_rate_m_h=80.0, wind_factor=2.0)
    forecasts = model.forecast(case, [3.0, 6.0])

    # Should produce forecasts
    assert len(forecasts) == 2

    # Burned area should increase
    assert forecasts[6.0].burned.sum() > forecasts[3.0].burned.sum()
    assert forecasts[3.0].burned.sum() > case.initial_state.burned.sum()


def test_all_baselines_comparable():
    """Test that all baselines can run on same case."""
    case = generate_synthetic_fire_case(
        case_id="test_compare",
        grid_size=(25, 25),
        n_forecast_hours=6,
        seed=789,
    )

    models = {
        "persistence": PersistenceBaseline(),
        "radial": RadialBaseline(),
        "elliptical": EllipticalBaseline(),
    }

    horizons = [3.0, 6.0]

    for name, model in models.items():
        forecasts = model.forecast(case, horizons)

        # All should produce same number of forecasts
        assert len(forecasts) == len(horizons), f"{name} failed"

        # All forecasts should have correct shape
        for _horizon, forecast in forecasts.items():
            assert forecast.burned.shape == case.grid_shape, f"{name} shape mismatch"
            assert forecast.burned.dtype == np.int32, f"{name} dtype mismatch"
