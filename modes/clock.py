from display_manager import DisplayManager
import uasyncio as asyncio
from modes.base import InteractionMode


class ClockMode(InteractionMode):
    """Button-click triggered mode: shows the clock face for timeout_ms.

    Standalone — no knowledge of other modes.  Re-entry and settings
    transitions are managed externally by SleepController.
    """

    def __init__(self, dm: DisplayManager, timeout_ms=5000):
        super().__init__(dm)
        self._timeout_ms = timeout_ms

    async def run(self):
        self._dm.show_clock()
        display_task = asyncio.create_task(self._dm.run())
        try:
            await asyncio.sleep_ms(self._timeout_ms)
        finally:
            display_task.cancel()
