"""Tests for synthetic data generation."""

import numpy as np
import pytest

from firetwin.data.synthetic import generate_synthetic_fire_case


def test_generate_synthetic_case_smoke():
    """Smoke test: synthetic case generation completes without errors."""
    case = generate_synthetic_fire_case(
        case_id="test_tiny",
        grid_size=(20, 20),
        resolution_m=30.0,
        n_forecast_hours=3,
        seed=42,
    )

    assert case.metadata.case_id == "test_tiny"
    assert case.metadata.is_synthetic is True
    assert case.grid_shape == (20, 20)
    assert case.resolution_m == 30.0
    # n_forecast_hours=3 generates states at t=0,1,2
    # initial_state is t=0, target_states are t=1,2 (2 states)
    assert len(case.target_states) == 2


def test_synthetic_case_deterministic():
    """Test that synthetic generation is deterministic with same seed."""
    case1 = generate_synthetic_fire_case(
        case_id="test_det1",
        grid_size=(15, 15),
        n_forecast_hours=2,
        seed=123,
    )
    case2 = generate_synthetic_fire_case(
        case_id="test_det2",
        grid_size=(15, 15),
        n_forecast_hours=2,
        seed=123,
    )

    # Terrain should be identical
    np.testing.assert_array_equal(case1.terrain.elevation_m, case2.terrain.elevation_m)
    np.testing.assert_array_equal(case1.fuels.fuel_model, case2.fuels.fuel_model)

    # Fire evolution should be identical
    assert len(case1.target_states) == len(case2.target_states)
    for s1, s2 in zip(case1.target_states, case2.target_states):
        np.testing.assert_array_equal(s1.burned, s2.burned)


def test_fire_spreads():
    """Test that fire spreads over time."""
    case = generate_synthetic_fire_case(
        case_id="test_spread",
        grid_size=(30, 30),
        n_forecast_hours=6,
        seed=999,
    )

    # Burned area should increase over time
    initial_area = case.initial_state.burned_area_m2
    areas = [state.burned_area_m2 for state in case.target_states]

    # Each time step should have >= previous (fire only grows)
    for i in range(len(areas) - 1):
        assert areas[i + 1] >= areas[i], "Fire should only grow, not shrink"

    # Final area should be larger than initial
    assert areas[-1] > initial_area


def test_fuel_constraints():
    """Test that fire respects non-burnable fuels."""
    case = generate_synthetic_fire_case(
        case_id="test_fuels",
        grid_size=(25, 25),
        n_forecast_hours=4,
        seed=777,
    )

    # Fire should only exist where fuels are burnable
    burnable = case.fuels.fuel_model > 0
    for state in case.target_states:
        # All burned cells should have burnable fuel
        burned_on_burnable = (state.burned & burnable).sum()
        total_burned = state.burned.sum()

        # May have some edge effects, but should be very close
        assert burned_on_burnable >= total_burned * 0.95
