"""
eyes/config.py — Display layout and eye shape descriptors.
"""


# ---------------------------------------------------------------------------
# Display / layout configuration — change here when swapping hardware
# ---------------------------------------------------------------------------

class DisplayConfig:
    WIDTH  = 128          # display width  in pixels
    HEIGHT = 64           # display height in pixels
    # Eye size (square bounding box before per-expression w/h override)
    EYE_SIZE = 40
    # Gap between the two eyes (pixels from each eye's centre toward midline)
    EYE_GAP  = 4
    # Vertical centre of both eyes on screen
    EYE_Y    = HEIGHT // 2   # 32


# ---------------------------------------------------------------------------
# Eye shape descriptor
# ---------------------------------------------------------------------------

class EyeConfig:
    """
    Describes a single eye's shape at rest (before mirroring).

    width / height  — bounding box of the white part of the eye
    offset_x/y      — shift from eye centre (positive = right / down)
    slope_top       — fraction of height to skew the top edge across the full
                      width: delta_y = height * slope_top / 2
                      positive → inner corner of top edge is lower (angry brow)
                      negative → inner corner is higher (sad, worried)
    slope_bottom    — same but for the bottom edge
    radius_top      — corner radius for top-left & top-right corners
    radius_bottom   — corner radius for bottom-left & bottom-right corners
    """
    __slots__ = (
        'width', 'height', 'offset_x', 'offset_y',
        'slope_top', 'slope_bottom',
        'radius_top', 'radius_bottom',
    )

    def __init__(self, width, height,
                 offset_x=0, offset_y=0,
                 slope_top=0.0, slope_bottom=0.0,
                 radius_top=8, radius_bottom=8):
        self.width         = width
        self.height        = height
        self.offset_x      = offset_x
        self.offset_y      = offset_y
        self.slope_top     = slope_top
        self.slope_bottom  = slope_bottom
        self.radius_top    = radius_top
        self.radius_bottom = radius_bottom

    def clone(self):
        return EyeConfig(
            self.width, self.height,
            self.offset_x, self.offset_y,
            self.slope_top, self.slope_bottom,
            self.radius_top, self.radius_bottom,
        )

    def mirror(self):
        """Return a horizontally mirrored copy (for the left eye).

        offset_x and both slope signs are negated so that the emotion reads
        symmetrically on both sides of the face.

        Convention used throughout this file (for the RIGHT eye):
          slope_top > 0 → outer (right) corner of the top edge drops
          slope_top < 0 → inner (left) corner of the top edge drops
        The left eye is the mirror image, so the sign must flip to keep the
        same corner (outer/inner) dropping on both eyes.
        """
        c = self.clone()
        c.offset_x     = -self.offset_x
        c.slope_top    = -self.slope_top
        c.slope_bottom = -self.slope_bottom
        return c
