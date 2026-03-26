from machine import Pin, TouchPad, lightsleep, wake_reason
from neopixel import NeoPixel
from time import sleep
import esp32
import machine

np = NeoPixel(Pin(48), 1)

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

# --- Touch setup ---
t = TouchPad(Pin(4))
sleep(1)
baseline = t.read()
touch_threshold = int(baseline * 1.2)
print(f"baseline={baseline} touch_threshold={touch_threshold}")

def is_touched():
    return t.read() > touch_threshold

# --- Button setup ---
wake1 = Pin(2, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=wake1, level=esp32.WAKEUP_ANY_HIGH)

# --- First boot ---
set_color(255, 0, 255)  # PURPLE
sleep(3)
set_color(0, 0, 0)
sleep(0.1)

while True:
    lightsleep(100)  # Short poll interval to catch touch

    if is_touched():
        set_color(0, 255, 0)    # GREEN = touch
        sleep(2)
        set_color(0, 0, 0)
    elif wake_reason() == machine.EXT0_WAKE:
        set_color(0, 0, 255)    # BLUE = button
        sleep(2)
        set_color(0, 0, 0)
