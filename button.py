import time
from machine import Pin


class Button:
    def __init__(self, pin_num,
                 on_single=None, on_long=None,
                 debounce_ms=50, long_press_ms=800):

        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
        self._on_single = on_single
        self._on_long = on_long
        self._debounce_ms = debounce_ms
        self._long_press_ms = long_press_ms

        self._press_time = 0
        self._last_edge_time = 0
        self._pending = None          # 'single' | 'long' | None — set in ISR, consumed in update()

        self._pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._irq)

    def _irq(self, pin):
        now = time.ticks_ms()

        # Debounce: ignore edges that arrive too soon after the last one
        if time.ticks_diff(now, self._last_edge_time) < self._debounce_ms:
            return
        self._last_edge_time = now

        if pin.value() == 1:          # Rising edge → button pressed
            self._press_time = now
        elif self._press_time > 0:    # Falling edge → button released
            duration = time.ticks_diff(now, self._press_time)
            self._press_time = 0
            # Only set flag here — don't call callbacks from ISR
            self._pending = 'long' if duration >= self._long_press_ms else 'single'

    def update(self):
        """Call this regularly from your main loop to fire callbacks safely."""
        if self._pending is None:
            return
        event, self._pending = self._pending, None  # consume atomically
        if event == 'long' and self._on_long:
            self._on_long()
        elif event == 'single' and self._on_single:
            self._on_single()

    def set_on_single(self, fn): self._on_single = fn
    def set_on_long(self, fn):   self._on_long = fn


if __name__ == "__main__":
    def handle_single(): print("Single!")
    def handle_long():   print("Long press!")

    btn = Button(pin_num=2, on_single=handle_single, on_long=handle_long)

    while True:
        btn.update()          # pump events — callbacks fire here, not in ISR
        time.sleep_ms(10)
