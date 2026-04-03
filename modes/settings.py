import uasyncio as asyncio
from modes.base import InteractionMode
from ui_screens import SettingsScreen
from http_server import HttpServer

_SETTINGS_TIMEOUT_S = 300   # seconds before auto-exit
_SAVED_LINGER_S     = 3     # seconds to show "saved!" before exiting
_EXITING_MS         = 1500  # ms to show "Exiting..." on button-cancel


class SettingsMode(InteractionMode):
    """Hold-triggered mode: starts the HTTP configuration server.

    Lifecycle
    ---------
    1. Immediately show "Loading config..." while the hotspot comes up.
    2. Once the AP is up, show "Visit: minisoul.local / or <ip>" with a
       countdown timer in the top-left corner.
    3. When a client connects, show "Connected!".
    4. When config is saved, show "New config saved!" then exit to clock
       after _SAVED_LINGER_S seconds.
    5. If the button is pressed (CancelledError), show "Exiting..." briefly
       then return cleanly so main.py picks up the next ClockMode.
    6. If the 300-second timeout expires, return so the device goes to sleep.

    In all exit paths the HTTP server is stopped and the hotspot torn down.
    """

    def __init__(self, dm, timeout_s=_SETTINGS_TIMEOUT_S):
        super().__init__(dm)
        self._timeout_s = timeout_s

    async def run(self):
        screen = SettingsScreen(seconds_total=self._timeout_s)
        self._dm.show_screen(screen)

        server = HttpServer(
            on_started   = lambda ip, ssid, pw: screen.update(SettingsScreen.READY, ip=ip, ssid=ssid, password=pw),
            on_connected = lambda addr: screen.update(SettingsScreen.CONNECTED),
            on_saved     = lambda cfg:  screen.update(SettingsScreen.SAVED),
        )

        display_task = asyncio.create_task(self._dm.run())
        server_task  = asyncio.create_task(server.run_server())

        try:
            for remaining in range(self._timeout_s, 0, -1):
                screen.seconds_left = remaining
                await asyncio.sleep(1)

                if screen.state == SettingsScreen.SAVED:
                    # Linger so the user can read the confirmation, then exit
                    await asyncio.sleep(_SAVED_LINGER_S)
                    break

        except asyncio.CancelledError:
            # Button was pressed — show a brief "Exiting..." before returning
            screen.update(SettingsScreen.EXITING)
            await asyncio.sleep_ms(_EXITING_MS)
            # Do NOT re-raise: let main.py see a clean return and pick up
            # the _next_mode = ClockMode that the button ISR already set.

        finally:
            server.stop()
            server_task.cancel()
            display_task.cancel()
