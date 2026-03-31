"""
sim/ssd1306.py — pygame-backed drop-in for SSD1306_I2C.

Exposes the same framebuf.FrameBuffer subset that the project uses:
  fill, fill_rect, hline, vline, pixel, text, show

The display is scaled up by SCALE (default 4) so each OLED pixel becomes a
4×4 block on screen, making the 128×64 display easy to read at 512×256.

External code can register pygame event listeners via add_event_listener(fn);
each listener receives raw pygame.event.Event objects.  The stub Button class
uses this to fire its callback on keyboard presses without needing a separate
event loop.
"""

import sys
import pygame

# ── Rendering constants ────────────────────────────────────────────────────
SCALE      = 4                   # OLED pixels → screen pixels
BG_COLOR   = (10, 10, 10)        # off-pixel colour (very dark grey)
ON_COLOR   = (220, 220, 220)     # on-pixel colour  (near white)

# ── Module-level event listener list ──────────────────────────────────────
_event_listeners = []


def add_event_listener(fn):
    """Register callable(event) — called inside show() for every pygame event."""
    _event_listeners.append(fn)


# ── Main simulated display class ──────────────────────────────────────────

class SSD1306_I2C:
    """pygame-backed SSD1306_I2C compatible class."""

    def __init__(self, width, height, i2c=None, addr=0x3C, external_vcc=False):
        self.width  = width
        self.height = height
        self._buf   = bytearray(width * height)  # 1 byte per pixel (0 or 1)

        if not pygame.get_init():
            pygame.init()

        win_w = width  * SCALE
        win_h = height * SCALE
        screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption(f"OLED Simulator  {width}×{height}")
        screen.fill(BG_COLOR)
        pygame.display.flip()

    # ── FrameBuffer-compatible drawing primitives ──────────────────────

    def fill(self, color):
        v = 1 if color else 0
        for i in range(len(self._buf)):
            self._buf[i] = v

    def fill_rect(self, x, y, w, h, color):
        v   = 1 if color else 0
        x0  = max(x, 0);          x1 = min(x + w, self.width)
        y0  = max(y, 0);          y1 = min(y + h, self.height)
        for row in range(y0, y1):
            base = row * self.width
            for col in range(x0, x1):
                self._buf[base + col] = v

    def hline(self, x, y, length, color):
        v = 1 if color else 0
        if not (0 <= y < self.height):
            return
        x0 = max(x, 0)
        x1 = min(x + length, self.width)
        base = y * self.width
        for col in range(x0, x1):
            self._buf[base + col] = v

    def vline(self, x, y, length, color):
        v = 1 if color else 0
        if not (0 <= x < self.width):
            return
        for row in range(max(y, 0), min(y + length, self.height)):
            self._buf[row * self.width + x] = v

    def pixel(self, x, y, color=None):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0
        if color is None:
            return self._buf[y * self.width + x]
        self._buf[y * self.width + x] = 1 if color else 0

    def text(self, s, x, y, color=1):
        """Render a string using a 5×8 pixel bitmap font (6 px advance)."""
        _draw_text(self, s, x, y, color)

    # ── Render buffer to pygame window ────────────────────────────────

    def show(self):
        # Dispatch all pending pygame events first.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            for listener in _event_listeners:
                listener(event)

        s      = SCALE
        buf    = self._buf
        w      = self.width

        # Fast blit: build a Surface from the buffer then scale it up.
        surf = pygame.Surface((self.width, self.height))
        surf.fill(BG_COLOR)
        for y in range(self.height):
            base = y * w
            for x in range(w):
                if buf[base + x]:
                    surf.set_at((x, y), ON_COLOR)

        scaled = pygame.transform.scale(surf, (self.width * s, self.height * s))
        pygame.display.get_surface().blit(scaled, (0, 0))


# ---------------------------------------------------------------------------
# Minimal 5×8 bitmap font — enough for labels and clock digits
# Each entry: 5 column bytes, MSB = top row.
# ---------------------------------------------------------------------------

_FONT: dict[int, list[int]] = {
    # space
    32:  [0x00, 0x00, 0x00, 0x00, 0x00],
    # !
    33:  [0x00, 0x00, 0x5F, 0x00, 0x00],
    # digits 0-9
    48:  [0x3E, 0x51, 0x49, 0x45, 0x3E],
    49:  [0x00, 0x42, 0x7F, 0x40, 0x00],
    50:  [0x42, 0x61, 0x51, 0x49, 0x46],
    51:  [0x21, 0x41, 0x45, 0x4B, 0x31],
    52:  [0x18, 0x14, 0x12, 0x7F, 0x10],
    53:  [0x27, 0x45, 0x45, 0x45, 0x39],
    54:  [0x3C, 0x4A, 0x49, 0x49, 0x30],
    55:  [0x01, 0x71, 0x09, 0x05, 0x03],
    56:  [0x36, 0x49, 0x49, 0x49, 0x36],
    57:  [0x06, 0x49, 0x49, 0x29, 0x1E],
    # colon
    58:  [0x00, 0x36, 0x36, 0x00, 0x00],
    # A-Z
    65:  [0x7E, 0x11, 0x11, 0x11, 0x7E],
    66:  [0x7F, 0x49, 0x49, 0x49, 0x36],
    67:  [0x3E, 0x41, 0x41, 0x41, 0x22],
    68:  [0x7F, 0x41, 0x41, 0x22, 0x1C],
    69:  [0x7F, 0x49, 0x49, 0x49, 0x41],
    70:  [0x7F, 0x09, 0x09, 0x09, 0x01],
    71:  [0x3E, 0x41, 0x49, 0x49, 0x7A],
    72:  [0x7F, 0x08, 0x08, 0x08, 0x7F],
    73:  [0x00, 0x41, 0x7F, 0x41, 0x00],
    74:  [0x20, 0x40, 0x41, 0x3F, 0x01],
    75:  [0x7F, 0x08, 0x14, 0x22, 0x41],
    76:  [0x7F, 0x40, 0x40, 0x40, 0x40],
    77:  [0x7F, 0x02, 0x0C, 0x02, 0x7F],
    78:  [0x7F, 0x04, 0x08, 0x10, 0x7F],
    79:  [0x3E, 0x41, 0x41, 0x41, 0x3E],
    80:  [0x7F, 0x09, 0x09, 0x09, 0x06],
    81:  [0x3E, 0x41, 0x51, 0x21, 0x5E],
    82:  [0x7F, 0x09, 0x19, 0x29, 0x46],
    83:  [0x46, 0x49, 0x49, 0x49, 0x31],
    84:  [0x01, 0x01, 0x7F, 0x01, 0x01],
    85:  [0x3F, 0x40, 0x40, 0x40, 0x3F],
    86:  [0x1F, 0x20, 0x40, 0x20, 0x1F],
    87:  [0x3F, 0x40, 0x38, 0x40, 0x3F],
    88:  [0x63, 0x14, 0x08, 0x14, 0x63],
    89:  [0x07, 0x08, 0x70, 0x08, 0x07],
    90:  [0x61, 0x51, 0x49, 0x45, 0x43],
    # a-z
    97:  [0x20, 0x54, 0x54, 0x54, 0x78],
    98:  [0x7F, 0x48, 0x44, 0x44, 0x38],
    99:  [0x38, 0x44, 0x44, 0x44, 0x20],
    100: [0x38, 0x44, 0x44, 0x48, 0x7F],
    101: [0x38, 0x54, 0x54, 0x54, 0x18],
    102: [0x08, 0x7E, 0x09, 0x01, 0x02],
    103: [0x0C, 0x52, 0x52, 0x52, 0x3E],
    104: [0x7F, 0x08, 0x04, 0x04, 0x78],
    105: [0x00, 0x44, 0x7D, 0x40, 0x00],
    106: [0x20, 0x40, 0x44, 0x3D, 0x00],
    107: [0x7F, 0x10, 0x28, 0x44, 0x00],
    108: [0x00, 0x41, 0x7F, 0x40, 0x00],
    109: [0x7C, 0x04, 0x18, 0x04, 0x78],
    110: [0x7C, 0x08, 0x04, 0x04, 0x78],
    111: [0x38, 0x44, 0x44, 0x44, 0x38],
    112: [0x7C, 0x14, 0x14, 0x14, 0x08],
    113: [0x08, 0x14, 0x14, 0x18, 0x7C],
    114: [0x7C, 0x08, 0x04, 0x04, 0x08],
    115: [0x48, 0x54, 0x54, 0x54, 0x20],
    116: [0x04, 0x3F, 0x44, 0x40, 0x20],
    117: [0x3C, 0x40, 0x40, 0x40, 0x7C],
    118: [0x1C, 0x20, 0x40, 0x20, 0x1C],
    119: [0x3C, 0x40, 0x30, 0x40, 0x3C],
    120: [0x44, 0x28, 0x10, 0x28, 0x44],
    121: [0x0C, 0x50, 0x50, 0x50, 0x3C],
    122: [0x44, 0x64, 0x54, 0x4C, 0x44],
}

_BLANK = [0x00, 0x00, 0x00, 0x00, 0x00]


def _draw_text(oled, s, x, y, color):
    """Render string s at (x, y) pixel position into the oled buffer."""
    cx = x
    for ch in s:
        cols = _FONT.get(ord(ch), _BLANK)
        for col_idx, byte in enumerate(cols):
            for row in range(8):
                if byte & (0x80 >> row):
                    oled.pixel(cx + col_idx, y + row, color)
        cx += 6  # 5 px glyph + 1 px gap
