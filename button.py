import time
from machine import Pin


class Button:
    def __init__(self, pin_num,
                 on_single=None, on_long=None,
                 debounce_ms=50, long_press_ms=800):

        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._on_single = on_single
        self._on_long = on_long
        self._debounce_ms = debounce_ms
        self._long_press_ms = long_press_ms
        self._press_time = 0
        self._last_edge_time = 0

        self._pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._irq)

    def _irq(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_edge_time) < self._debounce_ms:
            return
        self._last_edge_time = now

        if pin.value() == 0:       # press
            self._press_time = now
        else:                      # release
            duration = time.ticks_diff(now, self._press_time)
            if duration >= self._long_press_ms:
                if self._on_long:
                    self._on_long()
            else:
                if self._on_single:
                    self._on_single()

    def set_on_single(self, fn): self._on_single = fn
    def set_on_long(self, fn):   self._on_long = fn


if __name__ == "__main__":
    def handle_single(): print("Single!")
    def handle_long():   print("Long press!")

    btn = Button(pin_num=2, on_single=handle_single, on_long=handle_long)

    while True:
        time.sleep_ms(100)
