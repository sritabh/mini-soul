import uasyncio as asyncio
from modes.base import InteractionMode


class BehavioralMode(InteractionMode):
    """Touch-triggered mode: runs the face/emotion engine.

    Standalone — no knowledge of other modes.  Touch stabilisation after
    the timeout is handled by SleepController.

    Designed to grow: mood graphs, multi-step reactions, memory of past
    interactions, etc., all belong here.
    """

    def __init__(self, dm, timeout_ms=5000):
        super().__init__(dm)
        self._timeout_ms = timeout_ms

    async def run(self):
        self._dm.show_face()
        display_task = asyncio.create_task(self._dm.run())
        try:
            await asyncio.sleep_ms(self._timeout_ms)
        finally:
            display_task.cancel()
