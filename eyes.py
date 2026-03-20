"""
eyes.py — Animated robot eyes for SSD1306 OLED (MicroPython)

A port of the esp32-eyes C++ library adapted for single-panel OLEDs.
Each eye is drawn as a filled rounded rectangle with optional slope on
the top/bottom edges (to express emotion) and configurable corner radii.

Display config lives in DisplayConfig; tweak it when you change hardware.

Usage:
    from machine import SoftI2C, Pin
    from ssd1306 import SSD1306_I2C
    from eyes import Eyes, EXPR_HAPPY, EXPR_SAD   # etc.

    i2c  = SoftI2C(sda=Pin(8), scl=Pin(9))
    oled = SSD1306_I2C(128, 64, i2c)
    eyes = Eyes(oled)

    eyes.set_expression(EXPR_HAPPY)
    eyes.draw()
    oled.show()
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
        """Return a horizontally mirrored copy (for the left eye)."""
        c = self.clone()
        c.offset_x   = -self.offset_x
        # Slope sign flipped so the emotion reads the same on both sides
        c.slope_top    = self.slope_top
        c.slope_bottom = self.slope_bottom
        return c


# ---------------------------------------------------------------------------
# Expression presets  (right-eye config; left eye is auto-mirrored)
# ---------------------------------------------------------------------------
# Scaled relative to EYE_SIZE=40 (the reference used in the C++ original).
# When EYE_SIZE changes, call Eyes.recalculate_presets() or pass a custom
# scale_factor into the Eyes constructor.

def _presets(eye_size):
    """Return a dict of expression-name → (right_cfg, left_cfg or None).

    If left_cfg is None the right_cfg is mirrored automatically.
    Some expressions use a slightly different shape on each eye for realism.
    """
    s = eye_size / 40.0   # scale factor vs reference 40 px

    def sc(v):
        return int(v * s)

    def mk(w, h, ox=0, oy=0, st=0.0, sb=0.0, rt=8, rb=8):
        return EyeConfig(sc(w), sc(h), sc(ox), sc(oy), st, sb, sc(rt), sc(rb))

    p = {}

    # ---- basic expressions ------------------------------------------------
    p['normal']    = (mk(40, 40, rt=8, rb=8), None)

    p['happy']     = (mk(40, 10, rt=10, rb=0), None)

    p['sad']       = (mk(40, 15, st=-0.5, rt=1, rb=10),
                      mk(40, 15, st=-0.5, rt=1, rb=10))

    p['angry']     = (mk(40, 20,  ox=-3, st= 0.3, rt=2, rb=12),
                      mk(40, 20,  ox= 3, st=-0.3, rt=2, rb=12))

    p['surprised'] = (mk(45, 45, ox=-2, rt=16, rb=16), None)

    p['sleepy']    = (mk(40, 14, oy=-2, st=-0.5, sb=-0.5, rt=3, rb=3),
                      mk(40,  8, oy=-2, st=-0.5, sb=-0.5, rt=3, rb=3))

    # ---- additional expressions -------------------------------------------
    p['furious']   = (mk(40, 30, ox=-2, st= 0.4, rt=2, rb=8),
                      mk(40, 30, ox= 2, st=-0.4, rt=2, rb=8))

    p['fearful']   = (mk(40, 40, ox=-3, st=-0.1, rt=12, rb=8),
                      mk(40, 40, ox= 3, st= 0.1, rt=12, rb=8))

    p['suspicious'] = (mk(40, 22, rt=8, rb=3),
                       mk(40, 16, oy=-3, st=0.2, rt=6, rb=3))

    p['annoyed']   = (mk(40, 12, rt=0, rb=10),
                      mk(40,  5, rt=0, rb=4))

    return p


# Expression name constants for convenience
EXPR_NORMAL     = 'normal'
EXPR_HAPPY      = 'happy'
EXPR_SAD        = 'sad'
EXPR_ANGRY      = 'angry'
EXPR_SURPRISED  = 'surprised'
EXPR_SLEEPY     = 'sleepy'
EXPR_FURIOUS    = 'furious'
EXPR_FEARFUL    = 'fearful'
EXPR_SUSPICIOUS = 'suspicious'
EXPR_ANNOYED    = 'annoyed'


# ---------------------------------------------------------------------------
# Low-level drawing helpers
# ---------------------------------------------------------------------------

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _fill_rect(oled, x, y, w, h, col=1):
    """Fill a rectangle; clips silently to display bounds."""
    if w <= 0 or h <= 0:
        return
    dw = DisplayConfig.WIDTH
    dh = DisplayConfig.HEIGHT
    x1 = _clamp(x, 0, dw - 1)
    y1 = _clamp(y, 0, dh - 1)
    x2 = _clamp(x + w - 1, 0, dw - 1)
    y2 = _clamp(y + h - 1, 0, dh - 1)
    if x1 > x2 or y1 > y2:
        return
    oled.fill_rect(x1, y1, x2 - x1 + 1, y2 - y1 + 1, col)


def _hline(oled, x, y, length, col=1):
    """Draw a horizontal line; clips to display."""
    if length <= 0:
        return
    dw = DisplayConfig.WIDTH
    dh = DisplayConfig.HEIGHT
    if y < 0 or y >= dh:
        return
    x  = _clamp(x, 0, dw - 1)
    x2 = _clamp(x + length - 1, 0, dw - 1)
    if x > x2:
        return
    oled.hline(x, y, x2 - x + 1, col)


def _fill_ellipse_corner(oled, cx, cy, rx, ry, corner, col=1):
    """
    Fill one quadrant of an ellipse (the rounded corner of the eye).

    (cx, cy) is the centre of the full ellipse (= the corner anchor point).
    corner: 'TL', 'TR', 'BL', 'BR'

    For each row we compute how far the ellipse boundary is from the centre,
    then draw a horizontal line from that boundary to the centre column so the
    quarter-ellipse is fully filled.
    """
    if rx <= 0 or ry <= 0:
        return

    ry2 = ry * ry

    for dy in range(ry + 1):
        # half-width of the ellipse at this row offset
        frac = 1.0 - (dy * dy) / (ry2 + 0.0001)
        if frac < 0:
            frac = 0
        dx = int(rx * (frac ** 0.5) + 0.5)

        if corner == 'TL':
            # rows go from cy (top of body) upward; dy=0 is at cy, dy=ry is at top
            row_y = cy - dy
            # fill from cx-dx to cx (left side, upper quadrant)
            _hline(oled, cx - dx, row_y, dx + 1, col)
        elif corner == 'TR':
            row_y = cy - dy
            # fill from cx to cx+dx (right side, upper quadrant)
            _hline(oled, cx, row_y, dx + 1, col)
        elif corner == 'BL':
            row_y = cy + dy
            # fill from cx-dx to cx (left side, lower quadrant)
            _hline(oled, cx - dx, row_y, dx + 1, col)
        elif corner == 'BR':
            row_y = cy + dy
            # fill from cx to cx+dx (right side, lower quadrant)
            _hline(oled, cx, row_y, dx + 1, col)


def _fill_slope_triangle(oled, x_edge, y_top, x_tip, y_bot, col=1):
    """
    Fill a right-angled triangle used to erase/paint the sloped brow edge.

    The triangle has a horizontal top edge at y_top spanning x_edge→x_tip,
    and tapers to the single point x_tip at y_bot.

    Vertices: (x_edge, y_top), (x_tip, y_top), (x_tip, y_bot)
    """
    if y_top == y_bot:
        return
    total = abs(y_bot - y_top)
    step  = 1 if y_bot > y_top else -1
    for i, row in enumerate(range(y_top, y_bot + step, step)):
        # at row y_top the line spans the full width; at y_bot it is zero
        t  = i / total if total else 1
        # x_edge slides toward x_tip as we move from y_top to y_bot
        xi = int(x_edge + t * (x_tip - x_edge) + 0.5)
        lo = min(xi, x_tip)
        hi = max(xi, x_tip)
        if hi >= lo:
            _hline(oled, lo, row, hi - lo + 1, col)


# ---------------------------------------------------------------------------
# Core eye drawing
# ---------------------------------------------------------------------------

def draw_eye(oled, center_x, center_y, cfg):
    """
    Draw one eye.

    center_x, center_y — pixel centre of this eye on the display
    cfg                — EyeConfig describing this eye's shape
    """
    w   = cfg.width
    h   = cfg.height
    ox  = cfg.offset_x
    oy  = cfg.offset_y
    st  = cfg.slope_top
    sb  = cfg.slope_bottom
    rt  = cfg.radius_top
    rb  = cfg.radius_bottom

    # --- slope deltas (vertical shift at the edge of the eye) ---
    dyt = int(h * st / 2)   # + means right side of top edge is lower
    dyb = int(h * sb / 2)

    # --- clamp radii so they don't exceed available height ---
    total_h = h
    if rt + rb > total_h - 1:
        scale = (total_h - 1) / (rt + rb + 0.0001)
        rt = int(rt * scale)
        rb = int(rb * scale)

    # Eye bounding-box corners (before slope)
    cx = center_x + ox
    cy = center_y + oy

    left  = cx - w // 2
    right = left + w - 1
    top   = cy - h // 2
    bot   = top + h - 1

    # --- 1. Fill the main rectangular body (shrunk by radii on each side) ---
    # Horizontal centre strip (full width, between the four corner arcs)
    body_top = top + rt
    body_bot = bot - rb
    if body_top <= body_bot:
        _fill_rect(oled, left, body_top, w, body_bot - body_top + 1)

    # Top strip (between top-left arc and top-right arc, above body)
    if rt > 0:
        _fill_rect(oled, left + rt, top, w - 2 * rt, rt)
    # Bottom strip
    if rb > 0:
        _fill_rect(oled, left + rb, bot - rb + 1, w - 2 * rb, rb)

    # --- 2. Rounded corners ---
    # Corner anchor is the centre of the arc circle; we pass (cx, cy) as the
    # arc centre and the fill goes outward by rx/ry pixels.
    if rt > 0:
        # TL arc centre: (left+rt, top+rt)  → fills the top-left quadrant
        _fill_ellipse_corner(oled, left  + rt, top + rt, rt, rt, 'TL')
        # TR arc centre: (right-rt, top+rt) → fills the top-right quadrant
        _fill_ellipse_corner(oled, right - rt, top + rt, rt, rt, 'TR')
    if rb > 0:
        _fill_ellipse_corner(oled, left  + rb, bot - rb, rb, rb, 'BL')
        _fill_ellipse_corner(oled, right - rb, bot - rb, rb, rb, 'BR')

    # --- 3. Slope — erase the corner triangle that the brow cuts away ---
    # dyt > 0: right side of top edge is LOWER than left  → erase top-LEFT corner
    # dyt < 0: left  side of top edge is LOWER than right → erase top-RIGHT corner
    # The erase triangle runs from the far corner (y=top) tapering to the
    # opposite side at (y = top + |dyt|), spanning the full eye width.

    if dyt > 0:
        # Angry/focused: inner (right for right eye) side drops down.
        # Erase the raised outer (left) triangle.
        _fill_slope_triangle(oled, left, top, right, top + dyt, col=0)
    elif dyt < 0:
        # Sad/worried: outer corner drops down.
        # Erase the raised inner (right for right eye) triangle.
        _fill_slope_triangle(oled, right, top, left, top + abs(dyt), col=0)

    if dyb > 0:
        _fill_slope_triangle(oled, left, bot, right, bot - dyb, col=0)
    elif dyb < 0:
        _fill_slope_triangle(oled, right, bot, left, bot - dyb, col=0)


# ---------------------------------------------------------------------------
# Eyes controller
# ---------------------------------------------------------------------------

class Eyes:
    """
    High-level interface for drawing a pair of robot eyes on an OLED display.

    Parameters
    ----------
    oled        — an SSD1306_I2C (or compatible) instance
    eye_size    — reference eye size (default 40, same as the C++ original)
    display_config — pass a custom DisplayConfig class to override screen size

    Example
    -------
        eyes = Eyes(oled)
        eyes.set_expression(EXPR_HAPPY)
        eyes.draw()
        oled.show()
    """

    def __init__(self, oled, eye_size=None, display_config=None):
        self.oled = oled

        # Allow overriding display config at runtime
        if display_config is not None:
            self._dc = display_config
        else:
            self._dc = DisplayConfig

        self.eye_size = eye_size if eye_size is not None else self._dc.EYE_SIZE

        # Pre-compute eye centre positions
        self._left_cx  = self._dc.WIDTH // 2 - self.eye_size // 2 - self._dc.EYE_GAP
        self._right_cx = self._dc.WIDTH // 2 + self.eye_size // 2 + self._dc.EYE_GAP
        self._eye_cy   = self._dc.EYE_Y

        # Load expression presets
        self._presets = _presets(self.eye_size)
        self._current_expression = EXPR_NORMAL

        # Current eye configs (may differ per eye)
        right_cfg, left_cfg = self._presets[EXPR_NORMAL]
        self._right_cfg = right_cfg
        self._left_cfg  = left_cfg if left_cfg is not None else right_cfg.mirror()

    # ------------------------------------------------------------------
    def set_expression(self, name):
        """
        Switch to a named expression immediately.

        name — one of the EXPR_* constants or a string key
        """
        if name not in self._presets:
            raise ValueError("Unknown expression: {}".format(name))
        self._current_expression = name
        right_cfg, left_cfg = self._presets[name]
        self._right_cfg = right_cfg
        self._left_cfg  = left_cfg if left_cfg is not None else right_cfg.mirror()

    # ------------------------------------------------------------------
    def draw(self, clear=True):
        """
        Render both eyes to the framebuffer.

        Calls oled.fill(0) first to clear unless clear=False.
        Does NOT call oled.show() — call that yourself after draw().
        """
        if clear:
            self.oled.fill(0)
        draw_eye(self.oled, self._right_cx, self._eye_cy, self._right_cfg)
        draw_eye(self.oled, self._left_cx,  self._eye_cy, self._left_cfg)

    # ------------------------------------------------------------------
    def available_expressions(self):
        return list(self._presets.keys())
