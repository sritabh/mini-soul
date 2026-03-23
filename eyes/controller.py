"""
eyes/controller.py — High-level Eyes controller class.
"""

import time

from eyes.config   import DisplayConfig
from eyes.presets  import _presets, EXPR_NORMAL
from eyes.anim     import _ease, lerp_eye_config, apply_blink, BLINK_CLOSE_MS, BLINK_HOLD_MS, BLINK_OPEN_MS, BLINK_TOTAL_MS
from eyes.draw     import draw_eye


class Eyes:
    """
    High-level interface for drawing a pair of robot eyes on an OLED display.

    Parameters
    ----------
    oled              — an SSD1306_I2C (or compatible) instance
    eye_size          — reference eye size (default 40)
    display_config    — pass a custom DisplayConfig class to override screen size
    transition_ms     — default expression transition duration in milliseconds
    auto_blink        — automatically blink at blink_interval_ms intervals
    blink_interval_ms — milliseconds between auto-blinks

    Example
    -------
        eyes = Eyes(oled)
        eyes.set_expression(EXPR_HAPPINESS)
        eyes.draw()
        oled.show()
    """

    def __init__(self, oled, eye_size=None, display_config=None,
                 transition_ms=300, auto_blink=True, blink_interval_ms=3500):
        self.oled = oled

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
        self.blink_height      = 2
        self.blink_width       = int(60 * self.eye_size / 40)
        self._blink_start_ms   = None
        self._last_blink_ms    = time.ticks_ms()

    # ------------------------------------------------------------------
    def register_expression(self, name, right_cfg, left_cfg=None):
        """
        Add (or overwrite) a custom expression preset.

        right_cfg — EyeConfig for the right eye
        left_cfg  — EyeConfig for the left eye, or None to auto-mirror right_cfg

        Example
        -------
            from eyes.config import EyeConfig
            wink = EyeConfig(width=40, height=2, radius_top=1, radius_bottom=1)
            eyes.register_expression('wink', right_cfg=wink)
        """
        self._presets[name] = (right_cfg, left_cfg)

    # ------------------------------------------------------------------
    def set_expression(self, name, duration_ms=None):
        """
        Transition to a named expression.

        name        — one of the EXPR_* constants or a name previously passed
                      to register_expression()
        duration_ms — transition duration in ms; omit to use the default
                      (300 ms). Pass 0 for an instant switch.
        """
        if name not in self._presets:
            raise ValueError("Unknown expression: {}".format(name))

        dur = duration_ms if duration_ms is not None else self._default_trans_ms

        t = _ease(self._trans_t())
        self._from_right = lerp_eye_config(self._from_right, self._to_right, t)
        self._from_left  = lerp_eye_config(self._from_left,  self._to_left,  t)

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
        """
        if self.auto_blink and not self.is_blinking():
            if time.ticks_diff(time.ticks_ms(), self._last_blink_ms) >= self.blink_interval_ms:
                self.blink()

        t     = _ease(self._trans_t())
        right = lerp_eye_config(self._from_right, self._to_right, t)
        left  = lerp_eye_config(self._from_left,  self._to_left,  t)

        bt = self._blink_raw_t()
        if bt > 0.0:
            right = apply_blink(right, bt, self.blink_width, self.blink_height)
            left  = apply_blink(left,  bt, self.blink_width, self.blink_height)

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
        if elapsed >= BLINK_TOTAL_MS:
            self._blink_start_ms = None
            return 0.0
        if elapsed < BLINK_CLOSE_MS:
            return elapsed / BLINK_CLOSE_MS
        if elapsed < BLINK_CLOSE_MS + BLINK_HOLD_MS:
            return 1.0
        return 1.0 - (elapsed - BLINK_CLOSE_MS - BLINK_HOLD_MS) / BLINK_OPEN_MS
