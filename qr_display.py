# qr_display.py
#
# Display a QR code on a 128×64 SSD1306 OLED using uQR.
#
# Dependency: uQR.py  — https://github.com/JASchilz/uQR
#
# Usage:
#   from qr_display import show_qr, show_qr_with_label
#
#   show_qr(oled, "https://example.com")
#
#   # With a small label beneath the QR (shortens the usable QR area):
#   show_qr_with_label(oled, "https://example.com", "example.com")
#
# Notes:
#   • Keep data short — every extra character pushes uQR to a higher
#     version, making the matrix larger.  Rough limits at scale 1:
#       ~25 chars  → version 2, 25×25 matrix  ✓ fits easily
#       ~47 chars  → version 3, 29×29 matrix  ✓ fits
#       ~77 chars  → version 4, 33×33 matrix  ✓ fits
#       ~114 chars → version 5, 37×37 matrix  marginal (needs centering)
#     Beyond that the matrix is taller than 64px and won't display fully.
#   • The code is drawn white-on-black (OLED default) for best contrast.
#   • Error correction level is L (lowest) to keep matrix size down.

from uQR import QRCode

W = 128
H = 64


def _render(oled, matrix, x0, y0, scale=1):
    """Draw a QR matrix onto the OLED at (x0, y0) with given pixel scale."""
    for row_idx, row in enumerate(matrix):
        for col_idx, cell in enumerate(row):
            col = 1 if cell else 0          # dark module = lit pixel
            if scale == 1:
                x = x0 + col_idx
                y = y0 + row_idx
                if 0 <= x < W and 0 <= y < H:
                    oled.pixel(x, y, col)
            else:
                for dy in range(scale):
                    for dx in range(scale):
                        x = x0 + col_idx * scale + dx
                        y = y0 + row_idx * scale + dy
                        if 0 <= x < W and 0 <= y < H:
                            oled.pixel(x, y, col)


def show_qr(oled, data, scale=1):
    """
    Generate and display a QR code centred on the screen.

    Parameters
    ----------
    oled  : SSD1306_I2C instance
    data  : str — the text / URL to encode
    scale : int — pixel size per QR module (1 = smallest, 2 = 2×2 px each)
            scale=2 only works for very short strings (version 1, 21×21).
    """
    qr = QRCode(error_correction=0)
    qr.add_data(data)
    matrix = qr.get_matrix()

    size   = len(matrix)            # matrix is square: size × size modules
    px_w   = size * scale           # pixel width of the rendered QR
    px_h   = size * scale           # pixel height

    x0 = max(0, (W - px_w) // 2)   # centre horizontally
    y0 = max(0, (H - px_h) // 2)   # centre vertically

    oled.fill(0)
    _render(oled, matrix, x0, y0, scale)
    oled.show()

    return size                     # handy for debugging


def show_qr_with_label(oled, data, label, scale=1):
    """
    Display a QR code with a small text label beneath it.

    The label uses the built-in 8×8 font via oled.text().
    The QR is shifted up to leave 10px at the bottom for the label.

    Parameters
    ----------
    label : str — kept short (≤15 chars fits on one line at 8px font)
    """
    qr = QRCode(error_correction=0)
    qr.add_data(data)
    matrix = qr.get_matrix()

    size   = len(matrix)
    px_w   = size * scale
    px_h   = size * scale

    label_h = 10                            # pixels reserved for label row
    avail_h = H - label_h

    x0 = max(0, (W - px_w) // 2)
    y0 = max(0, (avail_h - px_h) // 2)     # centre within the upper area

    oled.fill(0)
    _render(oled, matrix, x0, y0, scale)

    # Label centred horizontally using the built-in 8px font
    char_w  = 8
    label_x = max(0, (W - len(label) * char_w) // 2)
    oled.text(label, label_x, H - 9)

    oled.show()

    return size


# ── Standalone test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    from machine import SoftI2C, Pin
    from ssd1306 import SSD1306_I2C

    i2c  = SoftI2C(sda=Pin(8), scl=Pin(9))
    oled = SSD1306_I2C(128, 64, i2c)

    # Basic QR — scan to visit a URL
    show_qr(oled, "https://example.com")

    # Uncomment to try with a label underneath:
    # show_qr_with_label(oled, "https://example.com", "example.com")

    # Uncomment to try scale=2 (only works for very short strings):
    # show_qr(oled, "HELLO", scale=2)
