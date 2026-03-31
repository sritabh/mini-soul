"""
sim/button.py — Keyboard-backed drop-in for the hardware Button class.

Pressing SPACE, ENTER, or → triggers on_click / on_press.
Pressing ← triggers on_long_press (if provided).

The Button piggybacks on the ssd1306 module's pygame event pipeline so no
separate event loop is needed — keyboard events are delivered automatically
inside every oled.show() call.
"""

import pygame
import ssd1306 as _oled_mod


class Button:
    """
    Desktop keyboard-backed Button.

    Accepts both `on_press` (used in eyes_test.py) and `on_click`
    (used in the actual hardware Button class) for compatibility.
    """

    # Keys that count as a "click / on_press"
    CLICK_KEYS = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_RIGHT)
    # Key that counts as a "long press"
    LONG_PRESS_KEYS = (pygame.K_LEFT,)

    def __init__(self, pin_num=None, on_click=None, on_press=None,
                 on_long_press=None, on_hold=None):
        # Support both naming conventions
        self._on_click       = on_click or on_press
        self._on_long_press  = on_long_press
        self._on_hold        = on_hold
        _oled_mod.add_event_listener(self._handle)

    def _handle(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in self.CLICK_KEYS:
            if self._on_click:
                self._on_click()
        elif event.key in self.LONG_PRESS_KEYS:
            if self._on_long_press:
                self._on_long_press()
