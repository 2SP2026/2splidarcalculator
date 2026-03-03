"""Unit tests for the GSD (Ground Sample Distance) calculator module."""

import pytest

from src.core.gsd_calculator import GsdInputs, GsdResult, calculate_gsd


# ────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────


def _default_inputs(**overrides) -> GsdInputs:
    """Sony a5100 with 16mm lens at 100m AGL."""
    defaults = dict(
        sensor_width_mm=23.5,
        image_width_px=6000,
        focal_length_mm=16.0,
        agl_m=100.0,
    )
    defaults.update(overrides)
    return GsdInputs(**defaults)


# ────────────────────────────────────────────────────────────────
#  Happy-path tests
# ────────────────────────────────────────────────────────────────


class TestBasicGsd:
    """Core formula correctness."""

    def test_basic_gsd(self):
        """Sony a5100 + 16mm @ 100m → GSD = (23.5/6000)*100/16 = 0.02448 m."""
        result = calculate_gsd(_default_inputs())
        assert isinstance(result, GsdResult)
        expected_gsd = (23.5 / 6000) * 100.0 / 16.0
        assert result.gsd_m == pytest.approx(expected_gsd, rel=1e-9)

    def test_pixel_pitch(self):
        """pixel_pitch = sensor_width / image_width."""
        result = calculate_gsd(_default_inputs())
        expected_pitch = 23.5 / 6000
        assert result.pixel_pitch_mm == pytest.approx(expected_pitch, rel=1e-9)

    def test_higher_agl_increases_gsd(self):
        """Flying higher → coarser GSD."""
        low = calculate_gsd(_default_inputs(agl_m=50.0))
        high = calculate_gsd(_default_inputs(agl_m=200.0))
        assert high.gsd_m > low.gsd_m

    def test_longer_focal_decreases_gsd(self):
        """Longer focal length (zoom in) → finer GSD."""
        wide = calculate_gsd(_default_inputs(focal_length_mm=16.0))
        tele = calculate_gsd(_default_inputs(focal_length_mm=24.0))
        assert tele.gsd_m < wide.gsd_m


# ────────────────────────────────────────────────────────────────
#  Validation tests
# ────────────────────────────────────────────────────────────────


class TestValidation:
    """Input validation raises ValueError when it should."""

    def test_zero_focal_length(self):
        with pytest.raises(ValueError, match="focal_length_mm"):
            calculate_gsd(_default_inputs(focal_length_mm=0.0))

    def test_zero_agl(self):
        with pytest.raises(ValueError, match="agl_m"):
            calculate_gsd(_default_inputs(agl_m=0.0))

    def test_negative_inputs(self):
        with pytest.raises(ValueError, match="sensor_width_mm"):
            calculate_gsd(_default_inputs(sensor_width_mm=-10.0))
