"""Unit tests for the Horizontal Error (RMSE_H) calculator module."""

import math

import pytest

from src.core.horizontal_error_calculator import (
    HorizontalErrorInputs,
    HorizontalErrorResult,
    calculate_horizontal_error,
)


# ────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────


def _arcsec_to_deg(arcsec: float) -> float:
    """Convert arc-seconds to degrees."""
    return arcsec / 3600.0


def _inputs(**overrides) -> HorizontalErrorInputs:
    """Baseline inputs with sensible defaults."""
    defaults = dict(
        gnss_error_m=0.10,
        imu_roll_pitch_error_deg=_arcsec_to_deg(10),
        imu_heading_error_deg=_arcsec_to_deg(15),
        flying_height_m=500.0,
    )
    defaults.update(overrides)
    return HorizontalErrorInputs(**defaults)


# ────────────────────────────────────────────────────────────────
#  ASPRS Table B.8 validation
# ────────────────────────────────────────────────────────────────


class TestAsprsTableB8:
    """Validate against ASPRS Table B.8 (all 5 rows)."""

    @pytest.mark.parametrize(
        "fh, expected_cm",
        [(500, 10.7), (1000, 12.9), (1500, 15.8), (2000, 19.2), (2500, 22.8)],
        ids=["FH=500", "FH=1000", "FH=1500", "FH=2000", "FH=2500"],
    )
    def test_table_b8(self, fh, expected_cm):
        result = calculate_horizontal_error(
            _inputs(flying_height_m=fh)
        )
        assert result.rmse_h_m * 100 == pytest.approx(expected_cm, abs=0.2)


# ────────────────────────────────────────────────────────────────
#  Real system scenarios (from user's Excel)
# ────────────────────────────────────────────────────────────────


class TestRealSystems:
    """Validate against user-provided system examples."""

    def test_comp1(self):
        """Comp1: GNSS=1cm, RP=0.025°, HDG=0.050°, AGL=100m → 8.91 cm."""
        result = calculate_horizontal_error(HorizontalErrorInputs(
            gnss_error_m=0.01,
            imu_roll_pitch_error_deg=0.025,
            imu_heading_error_deg=0.050,
            flying_height_m=100.0,
        ))
        assert result.rmse_h_m * 100 == pytest.approx(8.91, abs=0.1)

    def test_echo(self):
        """ECHO: GNSS=0.5cm, RP=0.006°, HDG=0.030°, AGL=100m → 4.28 cm."""
        result = calculate_horizontal_error(HorizontalErrorInputs(
            gnss_error_m=0.005,
            imu_roll_pitch_error_deg=0.006,
            imu_heading_error_deg=0.030,
            flying_height_m=100.0,
        ))
        assert result.rmse_h_m * 100 == pytest.approx(4.28, abs=0.1)

    def test_asprs_benchmark(self):
        """ASPRS Benchmark: GNSS=10cm, RP=0.004°, HDG=0.003°, AGL=500m → 10.82 cm."""
        result = calculate_horizontal_error(HorizontalErrorInputs(
            gnss_error_m=0.10,
            imu_roll_pitch_error_deg=0.004,
            imu_heading_error_deg=0.003,
            flying_height_m=500.0,
        ))
        assert result.rmse_h_m * 100 == pytest.approx(10.82, abs=0.1)


# ────────────────────────────────────────────────────────────────
#  Validation / edge-case tests
# ────────────────────────────────────────────────────────────────


class TestValidation:
    """Input validation raises ValueError when it should."""

    def test_negative_gnss(self):
        with pytest.raises(ValueError, match="gnss_error_m"):
            calculate_horizontal_error(_inputs(gnss_error_m=-0.01))

    def test_negative_imu_rp(self):
        with pytest.raises(ValueError, match="imu_roll_pitch_error_deg"):
            calculate_horizontal_error(_inputs(imu_roll_pitch_error_deg=-1.0))

    def test_zero_flying_height(self):
        with pytest.raises(ValueError, match="flying_height_m"):
            calculate_horizontal_error(_inputs(flying_height_m=0.0))

    def test_higher_altitude_increases_error(self):
        """Sanity: more altitude → larger RMSE_H."""
        low = calculate_horizontal_error(_inputs(flying_height_m=100.0))
        high = calculate_horizontal_error(_inputs(flying_height_m=2000.0))
        assert high.rmse_h_m > low.rmse_h_m
