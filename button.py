import time
from machine import Pin

DEBOUNCE_MS = 200  # ms to ignore after a press (covers mechanical bounce on release)

class Button:
    def __init__(self, pin_num, on_click=None):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
        self._on_click = on_click
        self._last_press_ms = 0
        self._pin.irq(trigger=Pin.IRQ_RISING, handler=self._isr)

    def _isr(self, pin):
        # Confirm the pin is actually HIGH — filters release-bounce spikes
        if pin.value() != 1:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_press_ms) >= DEBOUNCE_MS:
            self._last_press_ms = now
            if self._on_click:
                self._on_click()

if __name__ == "__main__":
    def handle_click():
        print("Button clicked!")

    button = Button(pin_num=2, on_click=handle_click)

    while True:
        time.sleep(1)
