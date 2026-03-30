import time
from machine import Pin

DEBOUNCE_MS = 200  # ms to ignore after a press (covers mechanical bounce on release)

class Button:
    def __init__(self, pin_num, on_click=None):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
        self._on_click = on_click
        self._last_press_ms = 0
        self._pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._isr)
        self._currently_pressed = False

    def _isr(self, pin):
        val = pin.value()
        if val == 1:
            if self._currently_pressed:
                return
            # print("Button pressed!", time.ticks_ms())
            self._currently_pressed = True
        else:
            if not self._currently_pressed:
                return
            self._currently_pressed = False
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
