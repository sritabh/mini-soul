"""
eyes/anim.py — Interpolation and blink animation helpers.
"""

from eyes.config import EyeConfig


# ---------------------------------------------------------------------------
# Blink animation timing (ms) — matches the C++ TrapeziumAnimation(40, 100, 40)
# ---------------------------------------------------------------------------
BLINK_CLOSE_MS = 40
BLINK_HOLD_MS  = 100
BLINK_OPEN_MS  = 40
BLINK_TOTAL_MS = BLINK_CLOSE_MS + BLINK_HOLD_MS + BLINK_OPEN_MS  # 180 ms


# ---------------------------------------------------------------------------
# Interpolation helpers
# ---------------------------------------------------------------------------

def _lerp(a, b, t):
    return a + (b - a) * t


def _ease(t):
    """Smoothstep S-curve: starts and ends gently."""
    return t * t * (3 - 2 * t)


def lerp_eye_config(a, b, t):
    """Return an EyeConfig linearly interpolated between a and b at fraction t."""
    return EyeConfig(
        width         = _lerp(a.width,         b.width,         t),
        height        = _lerp(a.height,        b.height,        t),
        offset_x      = _lerp(a.offset_x,      b.offset_x,      t),
        offset_y      = _lerp(a.offset_y,      b.offset_y,      t),
        slope_top     = _lerp(a.slope_top,     b.slope_top,     t),
        slope_bottom  = _lerp(a.slope_bottom,  b.slope_bottom,  t),
        radius_top    = _lerp(a.radius_top,    b.radius_top,    t),
        radius_bottom = _lerp(a.radius_bottom, b.radius_bottom, t),
    )


def apply_blink(cfg, t, blink_width, blink_height):
    """
    Squish an EyeConfig toward the closed-eye shape.

    t=0 → eye fully open (cfg unchanged)
    t=1 → eye fully closed (height=blink_height, width=blink_width, slopes/radii=0)

    t² is applied so closing snaps quickly and opening eases in gently.
    """
    t2 = t * t
    return EyeConfig(
        width         = _lerp(cfg.width,         blink_width,  t2),
        height        = _lerp(cfg.height,        blink_height, t2),
        offset_x      = cfg.offset_x,
        offset_y      = cfg.offset_y,
        slope_top     = cfg.slope_top    * (1.0 - t2),
        slope_bottom  = cfg.slope_bottom * (1.0 - t2),
        radius_top    = cfg.radius_top   * (1.0 - t2),
        radius_bottom = cfg.radius_bottom * (1.0 - t2),
    )
