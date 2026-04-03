import uasyncio as asyncio
from modes.base import InteractionMode

_SETTINGS_DISPLAY_MS = 5000


class SettingsMode(InteractionMode):
    """Hold-triggered mode: placeholder until settings are implemented.

    Currently just shows a "[Settings]" text screen for a few seconds, then
    returns so the device goes back to sleep.  The HTTP server / QR flow will
    be wired in here later.
    """

    def __init__(self, dm, timeout_ms=_SETTINGS_DISPLAY_MS):
        super().__init__(dm)
        self._timeout_ms = timeout_ms

    async def run(self):
        self._dm.show_text("[Settings]")
        await asyncio.sleep_ms(self._timeout_ms)
