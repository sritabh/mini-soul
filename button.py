import time
from machine import Pin


class Button:
    def __init__(self, pin_num, on_press=None, debounce_ms=300):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._on_press = on_press
        self._debounce_ms = debounce_ms
        self._is_pressed = False
        self._last_event_time = 0
        self._pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handler)

    def _handler(self, pin):
        now = time.ticks_ms()
        if pin.value() == 0:  # falling edge — pressed
            # Debounce only on press side; release bounce is blocked by is_pressed
            if not self._is_pressed and time.ticks_diff(now, self._last_event_time) > self._debounce_ms:
                self._is_pressed = True
                self._last_event_time = now
                if self._on_press:
                    self._on_press()
        else:  # rising edge — released, just re-arm; no time gate needed
            self._is_pressed = False

    def set_on_press(self, handler):
        self._on_press = handler


if __name__ == "__main__":
    def handle_press():
        print("Single click!")

    btn = Button(pin_num=2, on_press=handle_press)

    while True:
        print("doing other work...")
        time.sleep(1)
