"""
ui_screens.py — UIScreen hierarchy for MiniSoul OLED display.

Each screen type owns its own render logic.
DisplayManager.show_screen(screen) is the only entry point needed.

Adding a new screen = subclass UIScreen, implement render(oled).
"""


class UIScreen:
    """Base class for all OLED screens.  Subclasses must implement render()."""

    def render(self, oled):
        raise NotImplementedError


class SettingsScreen(UIScreen):
    """Screen shown during the settings / HTTP-server session.

    States
    ------
    LOADING   — server is starting up
    READY     — hotspot is up, showing IP / mDNS address
    CONNECTED — a client has connected
    SAVED     — configuration was saved
    EXITING   — user pressed button; brief farewell before returning to clock

    Usage
    -----
    screen = SettingsScreen()
    dm.show_screen(screen)

    # later, from a callback:
    screen.update(SettingsScreen.READY, ip="192.168.4.1", seconds_left=295)
    screen.seconds_left = 290  # tick down each second
    """

    LOADING   = "loading"
    READY     = "ready"
    CONNECTED = "connected"
    SAVED     = "saved"
    EXITING   = "exiting"

    def __init__(self, seconds_total=300):
        self.state        = self.LOADING
        self.ip           = None
        self.ssid         = None
        self.password     = None
        self.seconds_left = seconds_total

    def update(self, state, ip=None, ssid=None, password=None, seconds_left=None):
        """Update state and optionally ip / wifi creds / seconds_left in one call."""
        self.state = state
        if ip is not None:
            self.ip = ip
        if ssid is not None:
            self.ssid = ssid
        if password is not None:
            self.password = password
        if seconds_left is not None:
            self.seconds_left = seconds_left

    # ── Rendering ─────────────────────────────────────────────────────────

    def render(self, oled):
        oled.fill(0)

        if self.state == self.EXITING:
            # No countdown — just a centred farewell
            self._draw_centered(oled, ["Exiting..."], top_offset=0)
        else:
            # Countdown in top-left: [NNNs]
            oled.text("[" + str(self.seconds_left) + "s]", 0, 0)

            if self.state == self.LOADING:
                self._draw_centered(oled, ["Loading", "config..."])
            elif self.state == self.READY:
                ip_line   = self.ip       or "?"
                ssid_line = self.ssid     or "MiniSoul"
                pw_line   = self.password or "?"
                self._draw_centered(oled, [
                    "WiFi: " + ssid_line,
                    "PW: " + pw_line
                ])
            elif self.state == self.CONNECTED:
                ip_line = self.ip or "?"
                self._draw_centered(oled, [
                    "Connected!",
                    "Visit:",
                    "minisoul.local",
                    "or " + ip_line,
                ])
            elif self.state == self.SAVED:
                self._draw_centered(oled, ["New config", "saved!"])

        oled.show()

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _draw_centered(oled, lines, char_w=8, char_h=8, line_gap=2, top_offset=16):
        """Draw a list of text lines centred horizontally below top_offset."""
        screen_w = 128
        screen_h = 64
        line_h   = char_h + line_gap
        total_h  = len(lines) * line_h - line_gap
        # Start below the timer row; if content is taller, just clamp to top_offset
        y0 = max(top_offset, (screen_h - total_h) // 2)

        for i, line in enumerate(lines):
            x = max(0, (screen_w - len(line) * char_w) // 2)
            y = y0 + i * line_h
            oled.text(line, x, y)
