import time
from machine import Pin


class Button:
    def __init__(self, pin_num, on_press=None, on_double_click=None, on_long_press=None,
                 debounce_ms=50, double_click_ms=400, long_press_ms=800):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._on_press = on_press
        self._on_double_click = on_double_click
        self._on_long_press = on_long_press
        self._debounce_ms = debounce_ms
        self._double_click_ms = double_click_ms
        self._long_press_ms = long_press_ms

        self._is_pressed = False
        self._press_start = 0
        self._last_release_time = 0
        self._pending_single = False  # True after a single click, waiting for possible double

        self._pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handler)

    def _handler(self, pin):
        now = time.ticks_ms()

        if not self._is_pressed:
            # Press edge — debounce against last release
            if time.ticks_diff(now, self._last_release_time) < self._debounce_ms:
                return
            # Flush a stale pending single click (double-click window has passed)
            if self._pending_single and \
                    time.ticks_diff(now, self._last_release_time) > self._double_click_ms:
                self._pending_single = False
                if self._on_press:
                    self._on_press()
            self._is_pressed = True
            self._press_start = now
        else:
            # Release edge — debounce against press start
            if time.ticks_diff(now, self._press_start) < self._debounce_ms:
                return
            self._is_pressed = False
            duration = time.ticks_diff(now, self._press_start)

            if duration >= self._long_press_ms:
                # Long press — skip click logic entirely
                self._pending_single = False
                self._last_release_time = now
                if self._on_long_press:
                    self._on_long_press()
                return

            # Short press: single or double click
            elapsed_since_last = time.ticks_diff(now, self._last_release_time)
            self._last_release_time = now

            if self._on_double_click:
                if self._pending_single and elapsed_since_last <= self._double_click_ms:
                    # Second click within window → double click, cancel buffered single
                    self._pending_single = False
                    self._on_double_click()
                else:
                    # First click — buffer it, don't fire yet
                    self._pending_single = True
            else:
                # No double-click handler — fire single immediately
                if self._on_press:
                    self._on_press()

    def tick(self):
        """Call this regularly from your main loop to flush a pending single click."""
        if self._pending_single and not self._is_pressed:
            if time.ticks_diff(time.ticks_ms(), self._last_release_time) > self._double_click_ms:
                self._pending_single = False
                if self._on_press:
                    self._on_press()

    def set_on_press(self, handler):
        self._on_press = handler

    def set_on_double_click(self, handler):
        self._on_double_click = handler

    def set_on_long_press(self, handler):
        self._on_long_press = handler


if __name__ == "__main__":
    def handle_press():
        print("Single click!")

    def handle_double():
        print("Double click!")

    def handle_long():
        print("Long press!")

    btn = Button(pin_num=2, on_press=handle_press,
                 on_double_click=handle_double, on_long_press=handle_long)

    while True:
        btn.tick()
        time.sleep_ms(10)
