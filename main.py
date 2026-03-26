# main.py
import machine
import esp32
import time
from ssd1306 import SSD1306_I2C
import rtc_utils
from clocks import ClockFace
from machine import TouchPad, Pin, lightsleep, wake_reason

SLEEP_TIMEOUT_MS    = 5000
TOUCH_POLL_MS       = 100

BUTTON_PIN          = 2
TOUCH_PIN           = 4
TOUCH_THRESHOLD_PCT = 1.2

oled  = SSD1306_I2C(128, 64, rtc_utils.i2c)
clock = ClockFace(oled, face="digital_bold")

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=button, level=esp32.WAKEUP_ANY_HIGH)

touch_pad = TouchPad(Pin(TOUCH_PIN))
time.sleep(1)
_touch_baseline  = touch_pad.read()
_touch_threshold = int(_touch_baseline * TOUCH_THRESHOLD_PCT)
print(f"Touch baseline={_touch_baseline}  threshold={_touch_threshold}")

_display_on    = False
_last_activity = time.ticks_ms()

def is_touched():
    return touch_pad.read() > _touch_threshold

def turn_display_on():
    global _display_on, _last_activity
    _display_on    = True
    _last_activity = time.ticks_ms()
    clock.tick()

def turn_display_off():
    global _display_on
    _display_on = False
    oled.fill(0)
    oled.show()

while True:
    lightsleep(TOUCH_POLL_MS)

    reason = wake_reason()

    if reason == machine.EXT0_WAKE or is_touched():
        turn_display_on()
    elif _display_on:
        clock.tick()

    if _display_on and time.ticks_diff(time.ticks_ms(), _last_activity) >= SLEEP_TIMEOUT_MS:
        turn_display_off()
