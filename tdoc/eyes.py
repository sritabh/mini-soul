"""
eyes.py — Animated robot eyes for SSD1306 OLED (MicroPython)

A port of the esp32-eyes C++ library adapted for single-panel OLEDs.
Each eye is drawn as a filled rounded rectangle with optional slope on
the top/bottom edges (to express emotion) and configurable corner radii.

Display config lives in DisplayConfig; tweak it when you change hardware.

Usage:
    from machine import SoftI2C, Pin
    from ssd1306 import SSD1306_I2C
    from eyes import Eyes, EXPR_HAPPINESS, EXPR_SADNESS   # etc.

    i2c  = SoftI2C(sda=Pin(8), scl=Pin(9))
    oled = SSD1306_I2C(128, 64, i2c)
    eyes = Eyes(oled)

    eyes.set_expression(EXPR_HAPPINESS)
    eyes.draw()
    oled.show()
"""

import time

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


# ---------------------------------------------------------------------------
# Expression presets  (right-eye config; left eye is auto-mirrored)
# ---------------------------------------------------------------------------
# Scaled relative to EYE_SIZE=40 (the reference used in the C++ original).
# When EYE_SIZE changes, call Eyes.recalculate_presets() or pass a custom
# scale_factor into the Eyes constructor.

def _presets(eye_size):
    """Return a dict of expression-name → (right_cfg, left_cfg or None).

    If left_cfg is None the right_cfg is auto-mirrored for the left eye.
    Provide explicit left_cfg only for intentionally asymmetric expressions
    such as EXPR_SKEPTICAL and EXPR_CONFUSED.

    Slope convention (right eye):
      slope_top > 0  →  outer (right) top corner drops  →  sad / droopy family
      slope_top < 0  →  inner (left)  top corner drops  →  angry / focused family
    mirror() negates both slope signs automatically.
    """
    s = eye_size / 40.0   # scale vs. reference eye_size=40

    def sc(v):
        return int(v * s)

    def mk(w, h, ox=0, oy=0, st=0.0, sb=0.0, rt=8, rb=8):
        return EyeConfig(sc(w), sc(h), sc(ox), sc(oy), st, sb, sc(rt), sc(rb))

    p = {}

    # ------------------------------------------------------------------
    # Internal neutral state (not part of the 24 emotions but useful as
    # a reset / starting point).
    # ------------------------------------------------------------------
    p['normal']      = (mk(40, 40, rt=8,  rb=8),  None)

    # ------------------------------------------------------------------
    # Six basic expressions
    # ------------------------------------------------------------------

    # SADNESS: narrow, outer corners drooping, sharp top, rounded bottom
    p['sadness']     = (mk(40, 15, st= 0.50, rt=1,  rb=10), None)

    # ANGER: inner top corners pushed down, sharp top, large bottom radius
    p['anger']       = (mk(40, 20, ox=-3, st=-0.30, rt=2,  rb=12), None)

    # HAPPINESS: short inverted-D, flat bottom, fully rounded top
    p['happiness']   = (mk(40, 10, rt=10, rb=0),  None)

    # SURPRISE: large, nearly circular eyes
    p['surprise']    = (mk(45, 45, ox=-2, rt=16, rb=16), None)

    # DISGUST: narrow horizontal, inner top corners slightly down
    p['disgust']     = (mk(40, 12, st=-0.20, rt=2,  rb=8),  None)

    # FEAR: wide open, outer corners very slightly lower
    p['fear']        = (mk(40, 40, ox=-3, st= 0.10, rt=12, rb=8),  None)

    # ------------------------------------------------------------------
    # Sub-faces of sadness
    # ------------------------------------------------------------------

    # PLEADING: large puppy-dog eyes, outer droop, shifted slightly down
    p['pleading']    = (mk(44, 30, oy= 2, st= 0.30, rt=10, rb=14), None)

    # VULNERABLE: dramatic outer droop, tall eyes
    p['vulnerable']  = (mk(40, 25, st= 0.45, rt=6,  rb=10), None)

    # DESPAIR: extreme outer drop, very narrow
    p['despair']     = (mk(40, 13, st= 0.65, rt=1,  rb=6),  None)

    # ------------------------------------------------------------------
    # Secondary middle row
    # ------------------------------------------------------------------

    # GUILTY: half-closed, inner brow slightly down, eyes shifted up
    p['guilty']      = (mk(40, 18, oy=-5, st=-0.20, rt=4,  rb=14), None)

    # DISAPPOINTED: narrow, offset toward centre, flat inner corner
    p['disappointed'] = (mk(40, 13, ox= 3, rt=2,  rb=10), None)

    # EMBARRASSED: short, eyes shifted up (lower half visible), no slope
    p['embarrassed'] = (mk(40, 13, oy=-4, rt=3,  rb=10), None)

    # ------------------------------------------------------------------
    # Sub-faces of disgust and anger
    # ------------------------------------------------------------------

    # HORRIFIED: large wide eyes, outer corners slightly elevated
    p['horrified']   = (mk(46, 38, ox=-2, st= 0.20, rt=14, rb=12), None)

    # SKEPTICAL: intentionally asymmetric
    #   right eye squints with downward inner slope
    #   left  eye stays wide open
    p['skeptical']   = (mk(40, 22, oy=-5, st=-0.25, rt=2,  rb=8),
                        mk(40, 40,                   rt=8,  rb=8))

    # ANNOYED: flat top edge, large rounded bottom
    p['annoyed']     = (mk(40, 14, rt=0,  rb=12), None)

    # ------------------------------------------------------------------
    # Sub-faces of surprise
    # ------------------------------------------------------------------

    # CONFUSED: intentionally asymmetric — each eye tilts a different way
    p['confused']    = (mk(46, 32, st= 0.25, rt=10, rb=14),
                        mk(40, 22, st=-0.20, rt=6,  rb=8))

    # AMAZED: maximum openness, perfectly round
    p['amazed']      = (mk(48, 48, rt=18, rb=18), None)

    # EXCITED: wide open with inner corners slightly raised
    p['excited']     = (mk(46, 36, st=-0.12, rt=14, rb=14), None)

    # ------------------------------------------------------------------
    # "Bad" expressions
    # ------------------------------------------------------------------

    # FURIOUS: extreme anger, steep inner drop, tall
    p['furious']     = (mk(40, 30, ox=-2, st=-0.40, rt=2,  rb=8),  None)

    # SUSPICIOUS: asymmetric brow — right narrows, left differs
    p['suspicious']  = (mk(40, 22, st=-0.15, rt=6,  rb=3),
                        mk(40, 16, oy=-3, st= 0.15, rt=5,  rb=3))

    # REJECTED: outer corners collapse, very narrow
    p['rejected']    = (mk(40, 12, ox=-2, st= 0.55, rt=1,  rb=5),  None)

    # BORED: half-closed, eye floats to lower half of socket
    p['bored']       = (mk(40, 20, oy= 5, rt=8,  rb=14), None)

    # TIRED: narrow, both top and bottom slope same direction (drooping)
    p['tired']       = (mk(40, 10, oy=-2, st= 0.35, sb= 0.35, rt=3, rb=3), None)

    # ASLEEP: eyes reduced to a thin sliver
    p['asleep']      = (mk(40,  4, rt=2,  rb=2),  None)

    return p


# ---------------------------------------------------------------------------
# Expression name constants
# ---------------------------------------------------------------------------
# Six basic expressions
EXPR_SADNESS      = 'sadness'
EXPR_ANGER        = 'anger'
EXPR_HAPPINESS    = 'happiness'
EXPR_SURPRISE     = 'surprise'
EXPR_DISGUST      = 'disgust'
EXPR_FEAR         = 'fear'
# Sub-faces of sadness
EXPR_PLEADING     = 'pleading'
EXPR_VULNERABLE   = 'vulnerable'
EXPR_DESPAIR      = 'despair'
# Secondary middle row
EXPR_GUILTY       = 'guilty'
EXPR_DISAPPOINTED = 'disappointed'
EXPR_EMBARRASSED  = 'embarrassed'
# Sub-faces of disgust and anger
EXPR_HORRIFIED    = 'horrified'
EXPR_SKEPTICAL    = 'skeptical'
EXPR_ANNOYED      = 'annoyed'
# Sub-faces of surprise
EXPR_CONFUSED     = 'confused'
EXPR_AMAZED       = 'amazed'
EXPR_EXCITED      = 'excited'
# Bad expressions
EXPR_FURIOUS      = 'furious'
EXPR_SUSPICIOUS   = 'suspicious'
EXPR_REJECTED     = 'rejected'
EXPR_BORED        = 'bored'
EXPR_TIRED        = 'tired'
EXPR_ASLEEP       = 'asleep'
# Neutral (internal, not one of the 24 emotions)
EXPR_NORMAL       = 'normal'


# ---------------------------------------------------------------------------
# Interpolation helpers (used for transitions)
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


# Blink animation timing (ms) — matches the C++ TrapeziumAnimation(40, 100, 40)
_BLINK_CLOSE_MS = 40
_BLINK_HOLD_MS  = 100
_BLINK_OPEN_MS  = 40
_BLINK_TOTAL_MS = _BLINK_CLOSE_MS + _BLINK_HOLD_MS + _BLINK_OPEN_MS  # 180 ms


def _apply_blink(cfg, t, blink_width, blink_height):
    """
    Squish an EyeConfig toward the closed-eye shape.

    t=0 → eye fully open (cfg unchanged)
    t=1 → eye fully closed (height=blink_height, width=blink_width, slopes/radii=0)

    t² is applied (same as C++ EyeBlink::Update) so closing snaps quickly
    and opening eases in gently.
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
    # Cast to int — configs may hold floats during transitions
    w   = int(cfg.width)
    h   = int(cfg.height)
    ox  = int(cfg.offset_x)
    oy  = int(cfg.offset_y)
    st  = cfg.slope_top        # kept as float: used in multiply only
    sb  = cfg.slope_bottom
    rt  = int(cfg.radius_top)
    rb  = int(cfg.radius_bottom)

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

    def __init__(self, oled, eye_size=None, display_config=None,
                 transition_ms=300, auto_blink=True, blink_interval_ms=3500):
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

        # Expression registry (presets + any user-registered expressions)
        self._presets = _presets(self.eye_size)
        self._current_expression = EXPR_NORMAL
        self._default_trans_ms = transition_ms

        # Transition state
        right_cfg, left_cfg = self._presets[EXPR_NORMAL]
        left_cfg = left_cfg if left_cfg is not None else right_cfg.mirror()
        self._from_right     = right_cfg
        self._from_left      = left_cfg
        self._to_right       = right_cfg
        self._to_left        = left_cfg
        self._trans_start_ms = None
        self._trans_dur_ms   = transition_ms

        # Blink state
        self.auto_blink        = auto_blink
        self.blink_interval_ms = blink_interval_ms
        # Closed-eye dimensions (scaled to this eye_size)
        self.blink_height      = 2
        self.blink_width       = int(60 * self.eye_size / 40)
        self._blink_start_ms   = None          # None = not blinking
        self._last_blink_ms    = time.ticks_ms()

    # ------------------------------------------------------------------
    def register_expression(self, name, right_cfg, left_cfg=None):
        """
        Add (or overwrite) a custom expression preset.

        right_cfg — EyeConfig for the right eye
        left_cfg  — EyeConfig for the left eye, or None to auto-mirror right_cfg

        Example
        -------
            from eyes import EyeConfig
            wink = EyeConfig(width=40, height=2, radius_top=1, radius_bottom=1)
            eyes.register_expression('wink', right_cfg=wink)
        """
        self._presets[name] = (right_cfg, left_cfg)

    # ------------------------------------------------------------------
    def set_expression(self, name, duration_ms=None):
        """
        Transition to a named expression.

        name        — one of the EXPR_* constants, a string key, or any name
                      previously passed to register_expression()
        duration_ms — transition duration in milliseconds; omit to use the
                      default set at construction time (default 300 ms).
                      Pass 0 for an instant switch.
        """
        if name not in self._presets:
            raise ValueError("Unknown expression: {}".format(name))

        dur = duration_ms if duration_ms is not None else self._default_trans_ms

        # Snapshot the current mid-transition position as the new start
        t = _ease(self._trans_t())
        self._from_right = lerp_eye_config(self._from_right, self._to_right, t)
        self._from_left  = lerp_eye_config(self._from_left,  self._to_left,  t)

        # Set target
        right_cfg, left_cfg = self._presets[name]
        self._to_right = right_cfg
        self._to_left  = left_cfg if left_cfg is not None else right_cfg.mirror()

        self._trans_start_ms  = time.ticks_ms()
        self._trans_dur_ms    = dur
        self._current_expression = name

    # ------------------------------------------------------------------
    def blink(self):
        """Trigger a single blink immediately."""
        self._blink_start_ms = time.ticks_ms()
        self._last_blink_ms  = self._blink_start_ms

    # ------------------------------------------------------------------
    def is_blinking(self):
        """Return True while a blink animation is in progress."""
        return self._blink_start_ms is not None

    # ------------------------------------------------------------------
    def is_transitioning(self):
        """Return True while a transition is still in progress."""
        return self._trans_t() < 1.0

    # ------------------------------------------------------------------
    def draw(self, clear=True):
        """
        Render both eyes to the framebuffer at the current animation state.

        Applies (in order): expression transition → blink squish.
        Calls oled.fill(0) first to clear unless clear=False.
        Does NOT call oled.show() — call that yourself after draw().
        Call this every frame in your main loop.
        """
        # --- auto-blink timer ---
        if self.auto_blink and not self.is_blinking():
            if time.ticks_diff(time.ticks_ms(), self._last_blink_ms) >= self.blink_interval_ms:
                self.blink()

        # --- expression transition ---
        t     = _ease(self._trans_t())
        right = lerp_eye_config(self._from_right, self._to_right, t)
        left  = lerp_eye_config(self._from_left,  self._to_left,  t)

        # --- blink squish (applied on top of whatever expression is showing) ---
        bt = self._blink_raw_t()
        if bt > 0.0:
            right = _apply_blink(right, bt, self.blink_width, self.blink_height)
            left  = _apply_blink(left,  bt, self.blink_width, self.blink_height)

        if clear:
            self.oled.fill(0)
        draw_eye(self.oled, self._right_cx, self._eye_cy, right)
        draw_eye(self.oled, self._left_cx,  self._eye_cy, left)

    # ------------------------------------------------------------------
    def available_expressions(self):
        """Return a list of all registered expression names."""
        return list(self._presets.keys())

    # ------------------------------------------------------------------
    def _trans_t(self):
        """Raw linear transition progress in [0, 1]."""
        if self._trans_start_ms is None:
            return 1.0
        if self._trans_dur_ms <= 0:
            return 1.0
        elapsed = time.ticks_diff(time.ticks_ms(), self._trans_start_ms)
        t = elapsed / self._trans_dur_ms
        return min(1.0, max(0.0, t))

    # ------------------------------------------------------------------
    def _blink_raw_t(self):
        """Trapezoid blink progress: 0=open, ramps to 1=shut, ramps back to 0=open."""
        if self._blink_start_ms is None:
            return 0.0
        elapsed = time.ticks_diff(time.ticks_ms(), self._blink_start_ms)
        if elapsed >= _BLINK_TOTAL_MS:
            self._blink_start_ms = None   # blink finished
            return 0.0
        if elapsed < _BLINK_CLOSE_MS:
            return elapsed / _BLINK_CLOSE_MS
        if elapsed < _BLINK_CLOSE_MS + _BLINK_HOLD_MS:
            return 1.0
        return 1.0 - (elapsed - _BLINK_CLOSE_MS - _BLINK_HOLD_MS) / _BLINK_OPEN_MS
