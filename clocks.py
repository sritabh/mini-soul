# clocks.py  — v3
# Four clock faces for 128×64 SSD1306 OLED + DS3231 RTC

import time
import math
import rtc_utils

W = 128
H = 64


# ────────────────────────────────────────────────────────────────────────────
#  Low-level drawing primitives
# ────────────────────────────────────────────────────────────────────────────

def _px(oled, x, y, col=1):
    if 0 <= x < W and 0 <= y < H:
        oled.pixel(x, y, col)


def draw_line(oled, x0, y0, x1, y1, col=1):
    dx =  abs(x1 - x0);  sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0);  sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _px(oled, x0, y0, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy;  x0 += sx
        if e2 <= dx:
            err += dx;  y0 += sy


def draw_circle(oled, cx, cy, r, col=1):
    x   = r
    y   = 0
    err = -(r >> 1)
    while x >= y:
        _px(oled, cx + x, cy + y, col)
        _px(oled, cx + y, cy + x, col)
        _px(oled, cx - y, cy + x, col)
        _px(oled, cx - x, cy + y, col)
        _px(oled, cx - x, cy - y, col)
        _px(oled, cx - y, cy - x, col)
        _px(oled, cx + y, cy - x, col)
        _px(oled, cx + x, cy - y, col)
        y += 1
        if err <= 0:
            err += 2 * y + 1
        else:
            x  -= 1
            err += 2 * (y - x) + 1


def fill_circle(oled, cx, cy, r, col=1):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        row = cy + dy
        if 0 <= row < H:
            for x in range(max(0, cx - dx), min(W, cx + dx + 1)):
                oled.pixel(x, row, col)


def draw_thick_line(oled, x0, y0, x1, y1, col=1):
    draw_line(oled, x0, y0, x1, y1, col)
    if abs(y1 - y0) >= abs(x1 - x0):
        draw_line(oled, x0 + 1, y0, x1 + 1, y1, col)
    else:
        draw_line(oled, x0, y0 + 1, x1, y1 + 1, col)


# ────────────────────────────────────────────────────────────────────────────
#  Tiny 3×5 pixel font
# ────────────────────────────────────────────────────────────────────────────

_FONT = {
    '0': [0b111, 0b101, 0b101, 0b101, 0b111],
    '1': [0b010, 0b110, 0b010, 0b010, 0b111],
    '2': [0b111, 0b001, 0b111, 0b100, 0b111],
    '3': [0b111, 0b001, 0b111, 0b001, 0b111],
    '4': [0b101, 0b101, 0b111, 0b001, 0b001],
    '5': [0b111, 0b100, 0b111, 0b001, 0b111],
    '6': [0b111, 0b100, 0b111, 0b101, 0b111],
    '7': [0b111, 0b001, 0b011, 0b010, 0b010],
    '8': [0b111, 0b101, 0b111, 0b101, 0b111],
    '9': [0b111, 0b101, 0b111, 0b001, 0b111],
    ':': [0b000, 0b010, 0b000, 0b010, 0b000],
    '/': [0b001, 0b001, 0b010, 0b100, 0b100],
    '-': [0b000, 0b000, 0b111, 0b000, 0b000],
    ' ': [0b000, 0b000, 0b000, 0b000, 0b000],
    '.': [0b000, 0b000, 0b000, 0b000, 0b010],
    'A': [0b010, 0b101, 0b111, 0b101, 0b101],
    'B': [0b110, 0b101, 0b110, 0b101, 0b110],
    'C': [0b011, 0b100, 0b100, 0b100, 0b011],
    'D': [0b110, 0b101, 0b101, 0b101, 0b110],
    'E': [0b111, 0b100, 0b110, 0b100, 0b111],
    'F': [0b111, 0b100, 0b110, 0b100, 0b100],
    'G': [0b011, 0b100, 0b101, 0b101, 0b011],
    'H': [0b101, 0b101, 0b111, 0b101, 0b101],
    'I': [0b111, 0b010, 0b010, 0b010, 0b111],
    'J': [0b001, 0b001, 0b001, 0b101, 0b011],
    'M': [0b101, 0b111, 0b101, 0b101, 0b101],
    'N': [0b101, 0b111, 0b111, 0b101, 0b101],
    'O': [0b010, 0b101, 0b101, 0b101, 0b010],
    'P': [0b110, 0b101, 0b110, 0b100, 0b100],
    'R': [0b110, 0b101, 0b110, 0b101, 0b101],
    'S': [0b011, 0b100, 0b010, 0b001, 0b110],
    'T': [0b111, 0b010, 0b010, 0b010, 0b010],
    'U': [0b101, 0b101, 0b101, 0b101, 0b011],
    'V': [0b101, 0b101, 0b101, 0b010, 0b010],
    'W': [0b101, 0b101, 0b101, 0b111, 0b101],
    'Y': [0b101, 0b101, 0b010, 0b010, 0b010],
}

def _draw_char(oled, x, y, ch, scale=1):
    rows = _FONT.get(ch.upper(), _FONT[' '])
    for ri, row in enumerate(rows):
        for ci in range(3):
            if row & (0b100 >> ci):
                bx = x + ci * scale
                by = y + ri * scale
                if scale == 1:
                    _px(oled, bx, by)
                else:
                    for sy in range(scale):
                        for sx in range(scale):
                            _px(oled, bx + sx, by + sy)


def draw_text(oled, x, y, text, scale=1):
    cx = x
    for ch in text:
        _draw_char(oled, cx, y, ch, scale)
        cx += (3 + 1) * scale
    return cx


def text_w(text, scale=1):
    return len(text) * (3 + 1) * scale


def cx_for(text, scale=1, area_w=W, area_x=0):
    return area_x + (area_w - text_w(text, scale)) // 2


# ────────────────────────────────────────────────────────────────────────────
#  Shared trig table
# ────────────────────────────────────────────────────────────────────────────

_SIN = [math.sin(i * math.pi / 30) for i in range(60)]
_COS = [math.cos(i * math.pi / 30) for i in range(60)]


class _DigitalBold:

    def draw(self, oled):
        yy, mo, dd, hh, mm, ss, dow, mon, hh12, period = rtc_utils.get_time_raw()
        oled.fill(0)

        # ── Time ──────────────────────────────────────────────────────
        ts = "{:02d}:{:02d}".format(hh12, mm)
        draw_text(oled, cx_for(ts, 4), 2, ts, 4)
        draw_text(oled, W - text_w(period, 2) - 1, 2, period, 2)

        # ── Seconds progress bar ──────────────────────────────────────
        prog = (ss * (W - 2)) // 59
        oled.hline(0, 27, prog + 1, 1)

        # ── DOW + date, scale 2 ───────────────────────────────────────
        # Draw DOW first, then fake a comma, then the rest
        dow_x = cx_for("{} {:02d} {}".format(dow, dd, mon), 2)
        after_dow = draw_text(oled, dow_x, 30, dow, 2)
        # Comma: small 2-pixel descender right after DOW
        _px(oled, after_dow,     38)
        _px(oled, after_dow - 1, 39)
        # Resume date after comma gap (one char-width at scale 2)
        draw_text(oled, after_dow + (3 + 1) * 2, 30, "{:02d} {}".format(dd, mon), 2)

        # ── Year ──────────────────────────────────────────────────────
        draw_text(oled, cx_for(str(yy), 3), 46, str(yy), 3)

        oled.show()

# ────────────────────────────────────────────────────────────────────────────
#  Face 2 — Minimal Split  (v4)
#
#  ┌──────────────┬─────────────────┐
#  │  HH  (×5)   │  DD  (×3)       │
#  │  ──          ├─────────────────┤
#  │  MM  (×5)   │  DOW (×2)       │
#  │         AM  ├─────────────────┤
#  │              │  MON            │
#  │              │  YYYY           │
#  └──────────────┴─────────────────┘
#
#  Left  = pure time (HH stacked over MM, separator dot-row, AM/PM corner)
#  Right = pure date (DD large, DOW, month, year) — no time at all
# ────────────────────────────────────────────────────────────────────────────

class _MinimalSplit:

    def draw(self, oled):
        yy, mo, dd, hh, mm, ss, dow, mon, hh12, period = rtc_utils.get_time_raw()
        oled.fill(0)

        DIV = 46
        oled.vline(DIV, 0, H, 1)

        # ── Left panel: time only ─────────────────────────────────────
        lw = DIV

        hh_str = "{:02d}".format(hh12)
        mm_str = "{:02d}".format(mm)

        # HH at scale 5, top quarter
        draw_text(oled, cx_for(hh_str, 5, lw, 0), 1, hh_str, 5)

        # Thin separator line between HH and MM
        oled.hline(4, 30, lw - 8, 1)

        # MM at scale 5, bottom quarter
        draw_text(oled, cx_for(mm_str, 5, lw, 0), 33, mm_str, 5)

        # AM/PM tiny, bottom-left corner
        draw_text(oled, 2, 57, period, 1)

        # ── Right panel: date only ────────────────────────────────────
        rx = DIV + 3
        rw = W - rx     # ≈ 79 px

        # DD — scale 3
        draw_text(oled, cx_for("{:02d}".format(dd), 3, rw, rx),
                  2, "{:02d}".format(dd), 3)

        oled.hline(DIV + 1, 20, rw, 1)

        # Day of week — scale 2
        draw_text(oled, cx_for(dow, 2, rw, rx), 23, dow, 2)

        oled.hline(DIV + 1, 36, rw, 1)

        # Month — scale 1
        draw_text(oled, cx_for(mon, 1, rw, rx), 39, mon, 1)

        # Year — scale 1, below month
        draw_text(oled, cx_for(str(yy), 1, rw, rx), 51, str(yy), 1)

        oled.show()


# ────────────────────────────────────────────────────────────────────────────
#  Face 3 — Analog  (v4)
#
#  Right panel — date only, no seconds counter:
#    y=2  : DD  (scale 3)
#    y=20 : ────────────
#    y=23 : DOW (scale 2)
#    y=36 : ────────────
#    y=39 : MON (scale 1)
#    y=51 : YYYY (scale 1)
#
#  Seconds hand on the dial already shows seconds — no need to repeat it.
# ────────────────────────────────────────────────────────────────────────────

class _Analog:

    def draw(self, oled):
        yy, mo, dd, hh, mm, ss, dow, mon, hh12, period = rtc_utils.get_time_raw()
        oled.fill(0)

        cx, cy, r = 32, 32, 30

        # ── Dial ──────────────────────────────────────────────────────
        draw_circle(oled, cx, cy, r)

        for i in range(12):
            idx    = (i * 5) % 60
            sa, ca = _SIN[idx], _COS[idx]
            tlen   = 5 if i % 3 == 0 else 3
            ox = round(cx + (r - 1) * sa);  oy = round(cy - (r - 1) * ca)
            ix = round(cx + (r - 1 - tlen) * sa)
            iy = round(cy - (r - 1 - tlen) * ca)
            draw_line(oled, ix, iy, ox, oy)
            if i % 3 == 0:
                draw_line(oled, ix + 1, iy, ox + 1, oy)

        h_idx = int(((hh % 12) * 60 + mm) / 720.0 * 60) % 60
        hlen  = int(r * 0.50)
        draw_thick_line(oled, cx, cy,
                        round(cx + hlen * _SIN[h_idx]),
                        round(cy - hlen * _COS[h_idx]))

        mlen = int(r * 0.76)
        draw_thick_line(oled, cx, cy,
                        round(cx + mlen * _SIN[mm]),
                        round(cy - mlen * _COS[mm]))

        slen = r - 4
        draw_line(oled, cx, cy,
                  round(cx + slen * _SIN[ss]),
                  round(cy - slen * _COS[ss]))

        fill_circle(oled, cx, cy, 2)

        pm_x = cx_for(period, 1, 2 * r - 2, cx - r + 1)
        draw_text(oled, pm_x, cy + r - 9, period, 1)

        # ── Divider ───────────────────────────────────────────────────
        oled.vline(68, 0, H, 1)

        # ── Right panel — date only ───────────────────────────────────
        rx = 71
        rw = W - rx     # = 57

        draw_text(oled, cx_for("{:02d}".format(dd), 3, rw, rx),
                  2, "{:02d}".format(dd), 3)

        oled.hline(69, 20, rw + 1, 1)

        draw_text(oled, cx_for(dow, 2, rw, rx), 23, dow, 2)

        oled.hline(69, 36, rw + 1, 1)

        draw_text(oled, cx_for(mon, 1, rw, rx), 39, mon, 1)

        draw_text(oled, cx_for(str(yy), 1, rw, rx), 51, str(yy), 1)

        oled.show()

# ────────────────────────────────────────────────────────────────────────────
#  Face 4 — Orbit  (v3)
#
#  The ring is kept but the interior is redesigned for clarity.
#  At scale 3 the 5-char "HH:MM" string is 5*(3+1)*3 = 60px wide — fits
#  inside r=29 ring comfortably.  Date below at scale 2.
#
#  Centre layout:
#    y=8  : HH:MM  (scale 3)
#    y=28 : AM/PM  (scale 1, centred)
#    y=36 : DD MON (scale 2, centred)   — bigger than v2's scale 1
#    y=50 : DOW    (scale 2, centred)   — bigger than v2's scale 1
#
#  Changes from v2:
#   • Date and DOW promoted from scale 1 → scale 2 (much more readable)
#   • Strings shortened to fit: "DD MON" (no year — too wide at scale 2)
#   • Year dropped from centre; it's the least time-critical field
#   • Orbiting dot kept at r (on the ring itself)
# ────────────────────────────────────────────────────────────────────────────

class _Orbit:

    def draw(self, oled):
        yy, mo, dd, hh, mm, ss, dow, mon, hh12, period = rtc_utils.get_time_raw()
        oled.fill(0)

        cx, cy, r = 64, 32, 30

        # ── Ring ──────────────────────────────────────────────────────
        draw_circle(oled, cx, cy, r)

        for i in range(12):
            idx    = (i * 5) % 60
            sa, ca = _SIN[idx], _COS[idx]
            tlen   = 4 if i % 3 == 0 else 2
            ox = round(cx + (r - 1) * sa);  oy = round(cy - (r - 1) * ca)
            ix = round(cx + (r - 1 - tlen) * sa)
            iy = round(cy - (r - 1 - tlen) * ca)
            draw_line(oled, ix, iy, ox, oy)

        # ── Orbiting seconds dot ──────────────────────────────────────
        ox = round(cx + r * _SIN[ss])
        oy = round(cy - r * _COS[ss])
        fill_circle(oled, ox, oy, 3)

        # ── Centre content ────────────────────────────────────────────
        # Time — scale 3
        ts = "{:02d}:{:02d}".format(hh12, mm)
        draw_text(oled, cx_for(ts, 3), 8, ts, 3)

        # AM/PM — scale 1
        draw_text(oled, cx_for(period, 1), 29, period, 1)

        # DD MON — scale 2  (was scale 1 in v2)
        # "DD MON" = 6 chars → 6*8=48px at scale 2 → fits inside r=29 (58px diameter)
        date_s = "{:02d} {}".format(dd, mon)
        draw_text(oled, cx_for(date_s, 2), 36, date_s, 2)

        # DOW — scale 2
        draw_text(oled, cx_for(dow, 2), 50, dow, 2)

        oled.show()


# ────────────────────────────────────────────────────────────────────────────
#  Public interface
# ────────────────────────────────────────────────────────────────────────────

_FACES = {
    "digital_bold":  _DigitalBold(),
    "minimal_split": _MinimalSplit(),
    "analog":        _Analog(),
    "orbit":         _Orbit(),
}


class ClockFace:
    """
    Manages face selection and frame rendering.

    Parameters
    ----------
    oled  : SSD1306_I2C instance
    face  : "digital_bold" | "minimal_split" | "analog" | "orbit"

    Methods
    -------
    tick()      — draw one frame; pair with time.sleep(1) in your loop
    run()       — blocking 1-fps loop
    next()      — advance to the next face
    face_name   — property, current face key string
    """

    FACE_NAMES = list(_FACES.keys())

    def __init__(self, oled, face="digital_bold"):
        self.oled  = oled
        self._idx  = self.FACE_NAMES.index(face) if face in self.FACE_NAMES else 0

    @property
    def face_name(self):
        return self.FACE_NAMES[self._idx]

    def tick(self):
        _FACES[self.face_name].draw(self.oled)

    def next(self):
        self._idx = (self._idx + 1) % len(self.FACE_NAMES)

    def run(self):
        while True:
            self.tick()
            time.sleep(1)

    async def run_async(self):
        import uasyncio as asyncio
        while True:
            self.tick()
            await asyncio.sleep(1)


if __name__ == "__main__":
    from ssd1306 import SSD1306_I2C

    i2c  = rtc_utils.i2c
    oled = SSD1306_I2C(128, 64, i2c)

    # digital_bold
    # minimal_split
    # analog
    # orbit

    clock = ClockFace(oled, face="digital_bold")
    clock.run()
