"""
eyes/draw.py — Low-level pixel drawing helpers and the core draw_eye() function.
"""

from eyes.config import DisplayConfig


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
    """
    if rx <= 0 or ry <= 0:
        return

    ry2 = ry * ry

    for dy in range(ry + 1):
        frac = 1.0 - (dy * dy) / (ry2 + 0.0001)
        if frac < 0:
            frac = 0
        dx = int(rx * (frac ** 0.5) + 0.5)

        if corner == 'TL':
            row_y = cy - dy
            _hline(oled, cx - dx, row_y, dx + 1, col)
        elif corner == 'TR':
            row_y = cy - dy
            _hline(oled, cx, row_y, dx + 1, col)
        elif corner == 'BL':
            row_y = cy + dy
            _hline(oled, cx - dx, row_y, dx + 1, col)
        elif corner == 'BR':
            row_y = cy + dy
            _hline(oled, cx, row_y, dx + 1, col)


def _fill_slope_triangle(oled, x_edge, y_top, x_tip, y_bot, col=1):
    """
    Fill a right-angled triangle used to erase/paint the sloped brow edge.

    Vertices: (x_edge, y_top), (x_tip, y_top), (x_tip, y_bot)
    """
    if y_top == y_bot:
        return
    total = abs(y_bot - y_top)
    step  = 1 if y_bot > y_top else -1
    for i, row in enumerate(range(y_top, y_bot + step, step)):
        t  = i / total if total else 1
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
    w   = int(cfg.width)
    h   = int(cfg.height)
    ox  = int(cfg.offset_x)
    oy  = int(cfg.offset_y)
    st  = cfg.slope_top
    sb  = cfg.slope_bottom
    rt  = int(cfg.radius_top)
    rb  = int(cfg.radius_bottom)

    dyt = int(h * st / 2)
    dyb = int(h * sb / 2)

    total_h = h
    if rt + rb > total_h - 1:
        scale = (total_h - 1) / (rt + rb + 0.0001)
        rt = int(rt * scale)
        rb = int(rb * scale)

    cx = center_x + ox
    cy = center_y + oy

    left  = cx - w // 2
    right = left + w - 1
    top   = cy - h // 2
    bot   = top + h - 1

    # 1. Fill the main rectangular body
    body_top = top + rt
    body_bot = bot - rb
    if body_top <= body_bot:
        _fill_rect(oled, left, body_top, w, body_bot - body_top + 1)

    if rt > 0:
        _fill_rect(oled, left + rt, top, w - 2 * rt, rt)
    if rb > 0:
        _fill_rect(oled, left + rb, bot - rb + 1, w - 2 * rb, rb)

    # 2. Rounded corners
    if rt > 0:
        _fill_ellipse_corner(oled, left  + rt, top + rt, rt, rt, 'TL')
        _fill_ellipse_corner(oled, right - rt, top + rt, rt, rt, 'TR')
    if rb > 0:
        _fill_ellipse_corner(oled, left  + rb, bot - rb, rb, rb, 'BL')
        _fill_ellipse_corner(oled, right - rb, bot - rb, rb, rb, 'BR')

    # 3. Slope — erase the corner triangle that the brow cuts away
    if dyt > 0:
        _fill_slope_triangle(oled, left, top, right, top + dyt, col=0)
    elif dyt < 0:
        _fill_slope_triangle(oled, right, top, left, top + abs(dyt), col=0)

    if dyb > 0:
        _fill_slope_triangle(oled, left, bot, right, bot - dyb, col=0)
    elif dyb < 0:
        _fill_slope_triangle(oled, right, bot, left, bot - dyb, col=0)
