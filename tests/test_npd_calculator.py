"""Unit tests for the NPD (Nominal Point Density) calculator module."""

import math

import pytest

from src.core.npd_calculator import NpdInputs, NpdResult, calculate_npd, validate_inputs


# ────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────

def _default_inputs(**overrides) -> NpdInputs:
    """Return a baseline NpdInputs with sensible defaults, applying overrides."""
    defaults = dict(
        prr_hz=200_000,
        ground_speed_ms=5.0,
        agl_m=80.0,
        sensor_fov_deg=360.0,
        effective_fov_deg=60.0,
    )
    defaults.update(overrides)
    return NpdInputs(**defaults)


# ────────────────────────────────────────────────────────────────
#  Happy-path tests
# ────────────────────────────────────────────────────────────────


class TestBasicNpd:
    """Core formula correctness."""

    def test_basic_npd(self):
        """Hand-calculate: ePRR=33333, W=92.38, NPD=72.1."""
        result = calculate_npd(_default_inputs())
        assert isinstance(result, NpdResult)
        assert result.npd_pts_m2 == pytest.approx(72.1, abs=0.5)

    def test_swath_width(self):
        """W = 2 × AGL × tan(eFOV/2)."""
        result = calculate_npd(_default_inputs())
        expected_w = 2.0 * 80.0 * math.tan(math.radians(30.0))
        assert result.swath_width_m == pytest.approx(expected_w, rel=1e-9)

    def test_prr_scaling(self):
        """eFOV < sFOV → effective PRR is proportionally reduced."""
        result = calculate_npd(_default_inputs())
        expected_prr = 200_000 * (60.0 / 360.0)
        assert result.effective_prr_hz == pytest.approx(expected_prr, rel=1e-9)

    def test_full_fov(self):
        """eFOV == sFOV → 100 % PRR utilisation."""
        inputs = _default_inputs(sensor_fov_deg=90.0, effective_fov_deg=90.0)
        result = calculate_npd(inputs)
        assert result.effective_prr_hz == pytest.approx(200_000, rel=1e-9)

    def test_coverage_rate(self):
        """Coverage rate = v × W."""
        result = calculate_npd(_default_inputs())
        expected = 5.0 * result.swath_width_m
        assert result.coverage_rate_m2s == pytest.approx(expected, rel=1e-9)


# ────────────────────────────────────────────────────────────────
#  Validation / edge-case tests
# ────────────────────────────────────────────────────────────────


class TestValidation:
    """Input validation raises ValueError when it should."""

    def test_efov_exceeds_sfov(self):
        with pytest.raises(ValueError, match="must not exceed"):
            calculate_npd(_default_inputs(effective_fov_deg=400.0))

    def test_zero_speed(self):
        with pytest.raises(ValueError, match="ground_speed_ms"):
            calculate_npd(_default_inputs(ground_speed_ms=0.0))

    def test_zero_agl(self):
        with pytest.raises(ValueError, match="agl_m"):
            calculate_npd(_default_inputs(agl_m=0.0))

    def test_negative_inputs(self):
        with pytest.raises(ValueError, match="prr_hz"):
            calculate_npd(_default_inputs(prr_hz=-100))

    def test_efov_at_180(self):
        """tan(90°) is undefined → must reject eFOV == 180°."""
        with pytest.raises(ValueError, match="< 180"):
            calculate_npd(
                _default_inputs(sensor_fov_deg=360.0, effective_fov_deg=180.0)
            )


# ────────────────────────────────────────────────────────────────
#  Sanity-check scenario
# ────────────────────────────────────────────────────────────────


class TestSanityScenario:
    """End-to-end scenario matching our hand-calculated example."""

    def test_sanity_riegl_scenario(self):
        """RIEGL-like: 200 kHz, sFOV=360°, eFOV=60°, AGL=80m, v=5 m/s → ≈72 pts/m²."""
        inputs = NpdInputs(
            prr_hz=200_000,
            ground_speed_ms=5.0,
            agl_m=80.0,
            sensor_fov_deg=360.0,
            effective_fov_deg=60.0,
        )
        result = calculate_npd(inputs)

        # Intermediate checks
        assert result.effective_prr_hz == pytest.approx(33_333.33, rel=1e-4)
        assert result.swath_width_m == pytest.approx(92.38, abs=0.01)

        # Final NPD
        assert result.npd_pts_m2 == pytest.approx(72.1, abs=0.5)
