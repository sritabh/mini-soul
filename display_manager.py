import uasyncio as asyncio
from clocks import ClockFace
from qr_display import show_qr as _render_qr


class DisplayManager:
    """
    Controls what is shown on the OLED.

    Modes
    -----
    clock  — ticking clock face, redrawn every second
    qr     — static QR code
    text   — static centred text lines

    Usage
    -----
    dm = DisplayManager(oled)
    dm.show_clock("digital_bold")
    await dm.run()
    """

    def __init__(self, oled, default_face="digital_bold"):
        self.oled   = oled
        self._clock = ClockFace(oled, face=default_face)
        self._mode  = None
        self._qr_data   = None
        self._qr_scale  = 1
        self._text_lines = []

    # ── Mode setters ──────────────────────────────────────────────────────

    def show_clock(self, face=None):
        """Switch to clock mode. Optionally change the face."""
        if face is not None and face in ClockFace.FACE_NAMES:
            self._clock = ClockFace(self.oled, face=face)
        self._mode = "clock"

    def show_qr(self, data, scale=1):
        """Switch to QR mode and immediately render the QR code."""
        self._qr_data  = data
        self._qr_scale = scale
        self._mode     = "qr"
        self._render()

    def show_text(self, *lines):
        """Switch to text mode and immediately render the given lines."""
        self._text_lines = list(lines)
        self._mode       = "text"
        self._render()

    def _render(self):
        if self._mode == "clock":
            self._clock.tick()
        elif self._mode == "qr" and self._qr_data:
            self.oled.fill(0)
            _render_qr(self.oled, self._qr_data, scale=self._qr_scale)
        elif self._mode == "text":
            self.oled.fill(0)
            line_h = 10
            total  = len(self._text_lines) * line_h
            y0     = max(0, (64 - total) // 2)
            for i, line in enumerate(self._text_lines):
                self.oled.text(line, 0, y0 + i * line_h)
            self.oled.show()

    async def run(self):
        """Continuously render the current mode. Yields every second."""
        while True:
            self._render()
            await asyncio.sleep(1)
