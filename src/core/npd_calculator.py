"""
Nominal Point Density (NPD) Calculator — self-contained module.

Estimates the single-pass, single-return Nominal Point Density
for an airborne LiDAR survey under ideal, simplified assumptions.

Assumptions
-----------
- Single pass (no sidelap / overlap)
- Constant ground speed and AGL
- Single return per pulse
- Uniform point distribution across the effective swath
- All pulses within the effective FOV generate a ground return

Math Model
----------
    effective_PRR = PRR × (eFOV / sFOV)
    W             = 2 × AGL × tan(eFOV / 2)
    NPD           = effective_PRR / (v × W)

Where:
    PRR   = Total pulse repetition rate (pts/sec)
    sFOV  = Sensor's maximum horizontal scanning FOV (degrees)
    eFOV  = User-defined effective FOV (degrees), must be ≤ sFOV
    AGL   = Above Ground Level (metres)
    v     = Ground speed (m/s)
    W     = Swath width on the ground (metres)
    NPD   = Nominal Point Density (pts/m²)
"""

import math
from dataclasses import dataclass


# ────────────────────────────────────────────────────────────────
#  Data classes
# ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NpdInputs:
    """User-provided inputs for the NPD calculation.

    All values are sensor-agnostic — no database lookup required.
    """

    prr_hz: float
    """Total pulse repetition rate (points per second)."""

    ground_speed_ms: float
    """Aircraft ground speed (m/s)."""

    agl_m: float
    """Flying height above ground level (metres)."""

    sensor_fov_deg: float
    """Sensor's maximum horizontal scanning FOV — sFOV (degrees)."""

    effective_fov_deg: float
    """User-defined effective FOV — eFOV (degrees). Must be ≤ sFOV."""


@dataclass(frozen=True)
class NpdResult:
    """Computed outputs from the NPD calculation."""

    swath_width_m: float
    """Ground swath width (metres)."""

    effective_prr_hz: float
    """Pulse repetition rate scaled to effective FOV (points per second)."""

    coverage_rate_m2s: float
    """Ground area scanned per second (m²/s)."""

    npd_pts_m2: float
    """Nominal Point Density (points per square metre)."""


# ────────────────────────────────────────────────────────────────
#  Validation
# ────────────────────────────────────────────────────────────────


def validate_inputs(inputs: NpdInputs) -> None:
    """Validate *inputs* and raise ``ValueError`` on any problem.

    Can be called independently to pre-validate before computing.
    """
    if inputs.prr_hz <= 0:
        raise ValueError(
            f"prr_hz must be positive, got {inputs.prr_hz}"
        )
    if inputs.ground_speed_ms <= 0:
        raise ValueError(
            f"ground_speed_ms must be positive, got {inputs.ground_speed_ms}"
        )
    if inputs.agl_m <= 0:
        raise ValueError(
            f"agl_m must be positive, got {inputs.agl_m}"
        )
    if inputs.sensor_fov_deg <= 0:
        raise ValueError(
            f"sensor_fov_deg must be positive, got {inputs.sensor_fov_deg}"
        )
    if inputs.effective_fov_deg <= 0:
        raise ValueError(
            f"effective_fov_deg must be positive, got {inputs.effective_fov_deg}"
        )
    if inputs.effective_fov_deg > inputs.sensor_fov_deg:
        raise ValueError(
            f"effective_fov_deg ({inputs.effective_fov_deg}°) must not exceed "
            f"sensor_fov_deg ({inputs.sensor_fov_deg}°)"
        )
    if inputs.effective_fov_deg >= 180.0:
        raise ValueError(
            f"effective_fov_deg must be < 180° (tan(90°) is undefined), "
            f"got {inputs.effective_fov_deg}°"
        )


# ────────────────────────────────────────────────────────────────
#  Calculator
# ────────────────────────────────────────────────────────────────


def calculate_npd(inputs: NpdInputs) -> NpdResult:
    """Compute the Nominal Point Density from *inputs*.

    Parameters
    ----------
    inputs : NpdInputs
        Flight and sensor parameters.

    Returns
    -------
    NpdResult
        Swath width, effective PRR, coverage rate, and NPD.

    Raises
    ------
    ValueError
        If any input value is out of range.
    """
    validate_inputs(inputs)

    # ── Effective PRR ────────────────────────────────────────
    # The sensor fires uniformly across its full sFOV.
    # Only pulses within the eFOV generate usable returns.
    effective_prr = inputs.prr_hz * (
        inputs.effective_fov_deg / inputs.sensor_fov_deg
    )

    # ── Swath width ──────────────────────────────────────────
    half_angle_rad = math.radians(inputs.effective_fov_deg / 2.0)
    swath_width = 2.0 * inputs.agl_m * math.tan(half_angle_rad)

    # ── Coverage rate & NPD ──────────────────────────────────
    coverage_rate = inputs.ground_speed_ms * swath_width
    npd = effective_prr / coverage_rate

    return NpdResult(
        swath_width_m=swath_width,
        effective_prr_hz=effective_prr,
        coverage_rate_m2s=coverage_rate,
        npd_pts_m2=npd,
    )
