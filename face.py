"""
face.py — High-level Face controller with an async runner task.

Randomly cycles through all available expressions, keeping transitions and
auto-blink smooth via a continuous async render loop.
"""

import random
import uasyncio as asyncio

from eyes.controller import Eyes
from eyes.presets import (
    EXPR_NORMAL,
    EXPR_SADNESS, EXPR_ANGER, EXPR_HAPPINESS,
    EXPR_SURPRISE, EXPR_DISGUST, EXPR_FEAR,
    EXPR_PLEADING, EXPR_VULNERABLE, EXPR_DESPAIR,
    EXPR_GUILTY, EXPR_DISAPPOINTED, EXPR_EMBARRASSED,
    EXPR_HORRIFIED, EXPR_SKEPTICAL, EXPR_ANNOYED,
    EXPR_CONFUSED, EXPR_AMAZED, EXPR_EXCITED,
    EXPR_FURIOUS, EXPR_SUSPICIOUS, EXPR_REJECTED,
    EXPR_BORED, EXPR_TIRED, EXPR_ASLEEP,
)

EXPRESSIONS = [
    EXPR_NORMAL,
    EXPR_SADNESS,      EXPR_ANGER,        EXPR_HAPPINESS,
    EXPR_SURPRISE,     EXPR_DISGUST,      EXPR_FEAR,
    EXPR_PLEADING,     EXPR_VULNERABLE,   EXPR_DESPAIR,
    EXPR_GUILTY,       EXPR_DISAPPOINTED, EXPR_EMBARRASSED,
    EXPR_HORRIFIED,    EXPR_SKEPTICAL,    EXPR_ANNOYED,
    EXPR_CONFUSED,     EXPR_AMAZED,       EXPR_EXCITED,
    EXPR_FURIOUS,      EXPR_SUSPICIOUS,   EXPR_REJECTED,
    EXPR_BORED,        EXPR_TIRED,        EXPR_ASLEEP,
]

_FRAME_MS = 30   # render interval (~33 fps keeps transitions buttery smooth)


class Face:
    """
    High-level face controller with an async runner task.

    Parameters
    ----------
    oled          — SSD1306_I2C instance
    transition_ms — morph duration between expressions (ms, default 400)
    hold_ms       — how long each random expression is displayed (ms, default 2500)
    blink_interval_ms — auto-blink interval (ms, default 3500)
    """

    def __init__(self, oled, transition_ms=400, hold_ms=2500, blink_interval_ms=3500):
        self.oled    = oled
        self.hold_ms = hold_ms
        self.eyes    = Eyes(
            oled,
            transition_ms=transition_ms,
            auto_blink=True,
            blink_interval_ms=blink_interval_ms,
        )
        self._running = False
        self._task    = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_expression(self, expr, duration_ms=None):
        """Immediately queue a transition to the given expression."""
        self.eyes.set_expression(expr, duration_ms=duration_ms)

    def start(self):
        """Schedule the async runner as a background task."""
        self._running = True
        self._task = asyncio.create_task(self.run())

    def stop(self):
        """Cancel the background runner task."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None

    # ------------------------------------------------------------------
    # Async runner
    # ------------------------------------------------------------------

    async def run(self):
        """
        Randomly cycle through all expressions forever.

        Each expression is held for *hold_ms* milliseconds while the render
        loop runs every *_FRAME_MS* ms so transitions and blinks stay smooth.
        Yields control to other tasks between every frame.
        """
        self._running = True
        while self._running:
            expr = random.choice(EXPRESSIONS)
            print("Face expression:", expr)
            self.eyes.set_expression(expr)

            elapsed = 0
            while elapsed < self.hold_ms:
                self.eyes.draw()
                self.oled.show()
                await asyncio.sleep_ms(_FRAME_MS)
                elapsed += _FRAME_MS


if __name__ == "__main__":
    from machine import SoftI2C, Pin
    from ssd1306 import SSD1306_I2C

    i2c  = SoftI2C(sda=Pin(8), scl=Pin(9))
    oled = SSD1306_I2C(128, 64, i2c)

    face = Face(oled, transition_ms=400, hold_ms=2500, blink_interval_ms=3500)
    asyncio.run(face.run())
