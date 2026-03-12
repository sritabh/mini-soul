import time
from machine import Pin

btn = Pin(2, Pin.IN, Pin.PULL_UP)

last_release_time = 0
DEBOUNCE_MS = 200  # tune this if needed

def on_release(pin):
    global last_release_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_release_time) > DEBOUNCE_MS:
        last_release_time = now
        print("Single click!")

btn.irq(trigger=Pin.IRQ_RISING, handler=on_release)

while True:
    print("doing other work...")
    time.sleep(1)
