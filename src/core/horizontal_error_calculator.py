"""
Horizontal Error (RMSE_H) Calculator — self-contained module.

Estimates the horizontal positional accuracy of a lidar-derived
point cloud based on GNSS positional error, IMU angular errors,
and flying height, using the ASPRS model.

Assumptions
-----------
- Beam divergence is neglected (narrow footprint for modern sensors)
- Laser ranging and clock timing errors are negligible
- Flat terrain (no slope correction)

Math Model (ASPRS)
------------------
    RMSE_H = sqrt(
        GNSS_pos_error² +
        ( (tan(IMU_rp) + tan(IMU_hdg)) / 1.478 × FH )²
    )

Where:
    GNSS_pos_error = Radial GNSS positional accuracy (metres)
    IMU_rp         = IMU roll/pitch error (degrees, converted internally)
    IMU_hdg        = IMU heading/yaw error (degrees, converted internally)
    FH             = Flying height above mean terrain (metres)
    1.478          = Geometric constant from the ASPRS model
    RMSE_H         = Estimated horizontal error (metres)

Reference:
    ASPRS Positional Accuracy Standards, Edition 2, 2024.
"""

import math
from dataclasses import dataclass


# ASPRS geometric constant
_ASPRS_K = 1.478


# ────────────────────────────────────────────────────────────────
#  Data classes
# ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class HorizontalErrorInputs:
    """User-provided inputs for the RMSE_H calculation.

    All angular values are in **degrees**.
    """

    gnss_error_m: float
    """GNSS radial positional accuracy (metres)."""

    imu_roll_pitch_error_deg: float
    """IMU roll/pitch accuracy (degrees)."""

    imu_heading_error_deg: float
    """IMU heading/yaw accuracy (degrees)."""

    flying_height_m: float
    """Flying height above mean terrain (metres)."""


@dataclass(frozen=True)
class HorizontalErrorResult:
    """Computed outputs from the RMSE_H calculation."""

    rmse_h_m: float
    """Estimated horizontal error (metres)."""


# ────────────────────────────────────────────────────────────────
#  Validation
# ────────────────────────────────────────────────────────────────


def validate_inputs(inputs: HorizontalErrorInputs) -> None:
    """Validate *inputs* and raise ``ValueError`` on any problem.

    Can be called independently to pre-validate before computing.
    """
    if inputs.gnss_error_m < 0:
        raise ValueError(
            f"gnss_error_m must be non-negative, got {inputs.gnss_error_m}"
        )
    if inputs.imu_roll_pitch_error_deg < 0:
        raise ValueError(
            f"imu_roll_pitch_error_deg must be non-negative, "
            f"got {inputs.imu_roll_pitch_error_deg}"
        )
    if inputs.imu_heading_error_deg < 0:
        raise ValueError(
            f"imu_heading_error_deg must be non-negative, "
            f"got {inputs.imu_heading_error_deg}"
        )
    if inputs.flying_height_m <= 0:
        raise ValueError(
            f"flying_height_m must be positive, got {inputs.flying_height_m}"
        )


# ────────────────────────────────────────────────────────────────
#  Calculator
# ────────────────────────────────────────────────────────────────


def calculate_horizontal_error(
    inputs: HorizontalErrorInputs,
) -> HorizontalErrorResult:
    """Compute the estimated horizontal error (RMSE_H) from *inputs*.

    Parameters
    ----------
    inputs : HorizontalErrorInputs
        GNSS, IMU, and flight parameters.

    Returns
    -------
    HorizontalErrorResult
        Estimated RMSE_H.

    Raises
    ------
    ValueError
        If any input value is out of range.
    """
    validate_inputs(inputs)

    # ── Angular contribution ─────────────────────────────────
    rp_rad = math.radians(inputs.imu_roll_pitch_error_deg)
    hdg_rad = math.radians(inputs.imu_heading_error_deg)

    angular_term = (
        (math.tan(rp_rad) + math.tan(hdg_rad)) / _ASPRS_K
        * inputs.flying_height_m
    )

    # ── RMSE_H (root-sum-square) ─────────────────────────────
    rmse_h = math.sqrt(inputs.gnss_error_m ** 2 + angular_term ** 2)

    return HorizontalErrorResult(rmse_h_m=rmse_h)
