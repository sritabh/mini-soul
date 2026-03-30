import time
from machine import Pin, Timer

DEBOUNCE_MS = 200  # ms to ignore after a press (covers mechanical bounce on release)
LONG_PRESS_MS = 600  # ms to consider a long press (if still held after this)
MIN_WEIGHT_BEFORE_RELEASE_MS = 50  # ms of continuous press before we consider it a valid press (ignore quick taps)
HOLD_PRESS_MS = 3000  # ms to consider a 3-second hold press

class Button:
    _next_timer_id = 0  # class-level counter so each instance gets a unique hardware timer

    def __init__(self, pin_num, on_click=None, on_long_press=None, on_hold=None):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
        self._on_click = on_click
        self._on_long_press = on_long_press
        self._on_hold = on_hold
        self._last_clicked_timestamp = 0
        self._pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._isr)
        self._currently_pressed = False
        self._press_hold_timer = None
        self._temp_count = 0
        self._hold_timer = Timer(Button._next_timer_id)
        Button._next_timer_id += 1
        self._hold_active = False  # True once the 3s timer fires, suppresses click/long-press

    def _on_hold_fired(self, t):
        self._hold_active = True
        if self._on_hold:
            self._on_hold()

    def _isr(self, pin):
        self._temp_count += 1
        val = pin.value()
        if val == 1:
            if self._currently_pressed:
                return
            self._currently_pressed = True
            self._hold_active = False
            self._press_hold_timer = time.ticks_ms()
            # Schedule 3-second hold job; deinit() cancels it if released early
            self._hold_timer.init(period=HOLD_PRESS_MS, mode=Timer.ONE_SHOT,
                                  callback=self._on_hold_fired)
        else:
            if not self._currently_pressed:
                return
            self._currently_pressed = False
            self._hold_timer.deinit()  # cancel if released before 3 s
            if self._hold_active:
                # hold already fired — don't also trigger long-press or click
                self._press_hold_timer = None
                return
            now = time.ticks_ms()
            if time.ticks_diff(now, self._press_hold_timer) >= LONG_PRESS_MS:
                if self._on_long_press:
                    self._on_long_press()
            elif time.ticks_diff(now, self._last_clicked_timestamp) >= DEBOUNCE_MS and time.ticks_diff(now, self._press_hold_timer) >= MIN_WEIGHT_BEFORE_RELEASE_MS:
                self._last_clicked_timestamp = now
                if self._on_click:
                    self._on_click()
            self._press_hold_timer = None

if __name__ == "__main__":
    def handle_click():
        print("Button clicked!")
    def handle_long_press():
        print("Button long-pressed!")

    def handle_hold():
        print("Button held for 3 seconds!")

    button = Button(pin_num=2, on_click=handle_click, on_long_press=handle_long_press, on_hold=handle_hold)

    while True:
        time.sleep(1)
