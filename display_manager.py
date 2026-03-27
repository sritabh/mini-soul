import uasyncio as asyncio
from machine import Pin
from ssd1306 import SSD1306_I2C
import config_utils
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
    dm = DisplayManager(i2c)
    dm.show_clock("digital_bold")
    await dm.run()

    After every lightsleep call dm.awake_from_sleep() before rendering.
    """

    def __init__(self, i2c):
        self._i2c = i2c
        # Pin 7 powers the OLED VCC rail; keep the object so we can
        # re-assert HIGH after every lightsleep.
        self._vcc = Pin(7, Pin.OUT, value=1)
        self.oled = SSD1306_I2C(128, 64, i2c)
        self._clock = ClockFace(self.oled, face=config_utils.get_clock_face())
        self._mode  = None
        self._qr_data   = None
        self._qr_scale  = 1
        self._text_lines = []
        self._timer_task = None

    # ── Wake from sleep ───────────────────────────────────────────────────

    def awake_from_sleep(self):
        """Re-initialise the OLED after lightsleep.

        lightsleep drops the I2C bus and can float GPIO outputs, so the
        SSD1306 must be re-handed-shake and VCC must be re-asserted.
        Call this once at the start of every awake phase.
        """
        self._vcc.value(1)
        self.oled = SSD1306_I2C(128, 64, self._i2c)
        self._clock = ClockFace(self.oled, face=config_utils.get_clock_face())

    # ── Default screen ────────────────────────────────────────────────────

    def show_default_screen(self):
        """Revert to the default screen (clock face set at init)."""
        self.show_clock()

    # ── Mode setters ──────────────────────────────────────────────────────

    def show_clock(self, face=None):
        """Switch to clock mode. Optionally change the face."""
        self._cancel_timer()
        if face is not None and face in ClockFace.FACE_NAMES:
            self._clock = ClockFace(self.oled, face=face)
        self._mode = "clock"

    def show_qr(self, data, scale=1, show_for=3000):
        """Switch to QR mode and immediately render the QR code.
        Reverts to the default screen after show_for milliseconds."""
        self._cancel_timer()
        self._qr_data  = data
        self._qr_scale = scale
        self._mode     = "qr"
        self._render()
        self._schedule_default(show_for)

    def show_text(self, *lines, show_for=3000):
        """Switch to text mode and immediately render the given lines.
        Reverts to the default screen after show_for milliseconds."""
        self._cancel_timer()
        self._text_lines = list(lines)
        self._mode       = "text"
        self._render()
        self._schedule_default(show_for)

    # ── Timer helpers ─────────────────────────────────────────────────────

    def _cancel_timer(self):
        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = None

    def _schedule_default(self, ms):
        self._timer_task = asyncio.create_task(self._revert_after(ms))

    async def _revert_after(self, ms):
        await asyncio.sleep_ms(ms)
        self._timer_task = None
        self.show_default_screen()

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


if __name__ == "__main__":
    from machine import SoftI2C

    # Bring up I2C on the same pins used by rtc_utils
    i2c = SoftI2C(sda=Pin(8), scl=Pin(9))

    dm = DisplayManager(i2c)  # creates OLED internally and powers Pin 7
    dm.show_clock()

    asyncio.run(dm.run())
