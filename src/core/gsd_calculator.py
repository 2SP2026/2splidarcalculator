"""
Ground Sample Distance (GSD) Calculator — self-contained module.

Estimates the ground sample distance for a nadir-looking camera
under ideal, simplified assumptions.

Assumptions
-----------
- Flat terrain
- Nadir-looking camera (no oblique angle)
- Pinhole camera model
- Square pixels (same pitch in both sensor axes)

Math Model
----------
    pixel_pitch = sensor_width_mm / image_width_px
    GSD         = (pixel_pitch × AGL) / focal_length_mm

Where:
    sensor_width_mm  = Physical width of the camera sensor (mm)
    image_width_px   = Image width in pixels
    focal_length_mm  = Lens focal length (mm)
    AGL              = Above Ground Level (metres)
    GSD              = Ground Sample Distance (metres per pixel)
"""

from dataclasses import dataclass


# ────────────────────────────────────────────────────────────────
#  Data classes
# ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GsdInputs:
    """User-provided inputs for the GSD calculation.

    All values are sensor-agnostic — no database lookup required.
    """

    sensor_width_mm: float
    """Physical width of the camera sensor (mm)."""

    image_width_px: int
    """Image width in pixels."""

    focal_length_mm: float
    """Lens focal length (mm)."""

    agl_m: float
    """Flying height above ground level (metres)."""


@dataclass(frozen=True)
class GsdResult:
    """Computed outputs from the GSD calculation."""

    pixel_pitch_mm: float
    """Physical size of one pixel on the sensor (mm)."""

    gsd_m: float
    """Ground Sample Distance (metres per pixel)."""


# ────────────────────────────────────────────────────────────────
#  Validation
# ────────────────────────────────────────────────────────────────


def validate_inputs(inputs: GsdInputs) -> None:
    """Validate *inputs* and raise ``ValueError`` on any problem.

    Can be called independently to pre-validate before computing.
    """
    if inputs.sensor_width_mm <= 0:
        raise ValueError(
            f"sensor_width_mm must be positive, got {inputs.sensor_width_mm}"
        )
    if inputs.image_width_px <= 0:
        raise ValueError(
            f"image_width_px must be positive, got {inputs.image_width_px}"
        )
    if inputs.focal_length_mm <= 0:
        raise ValueError(
            f"focal_length_mm must be positive, got {inputs.focal_length_mm}"
        )
    if inputs.agl_m <= 0:
        raise ValueError(
            f"agl_m must be positive, got {inputs.agl_m}"
        )


# ────────────────────────────────────────────────────────────────
#  Calculator
# ────────────────────────────────────────────────────────────────


def calculate_gsd(inputs: GsdInputs) -> GsdResult:
    """Compute the Ground Sample Distance from *inputs*.

    Parameters
    ----------
    inputs : GsdInputs
        Camera and flight parameters.

    Returns
    -------
    GsdResult
        Pixel pitch and GSD.

    Raises
    ------
    ValueError
        If any input value is out of range.
    """
    validate_inputs(inputs)

    # ── Pixel pitch ──────────────────────────────────────────
    pixel_pitch = inputs.sensor_width_mm / inputs.image_width_px

    # ── GSD ──────────────────────────────────────────────────
    # Convert AGL from metres to mm for consistent units,
    # then result is in mm/px → convert back to m/px.
    gsd = (pixel_pitch * inputs.agl_m) / inputs.focal_length_mm
    # pixel_pitch is in mm, agl_m is in m, focal_length_mm is in mm
    # → (mm × m) / mm = m/px  ✓

    return GsdResult(
        pixel_pitch_mm=pixel_pitch,
        gsd_m=gsd,
    )
