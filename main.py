# main.py
import machine
import esp32
import time
from ssd1306 import SSD1306_I2C
import rtc_utils
from display_manager import DisplayManager
from machine import TouchPad, Pin, lightsleep, wake_reason
import uasyncio as asyncio

SLEEP_TIMEOUT_MS    = 5000
TOUCH_POLL_MS       = 400

BUTTON_PIN          = 2
TOUCH_PIN           = 4
TOUCH_THRESHOLD_PCT = 1.2

oled = SSD1306_I2C(128, 64, rtc_utils.i2c)
dm   = DisplayManager(oled)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=button, level=esp32.WAKEUP_ANY_HIGH)

touch_pad = TouchPad(Pin(TOUCH_PIN))
time.sleep(1) # Needed for stable touch readings after boot
_touch_baseline  = touch_pad.read()
_touch_threshold = int(_touch_baseline * TOUCH_THRESHOLD_PCT)
print(f"Touch baseline={_touch_baseline}  threshold={_touch_threshold}")

def is_touched():
    return touch_pad.read() > _touch_threshold


async def run_awake_phase(wake):
    if wake == "touch":
        dm.show_text("Woke up!", "(touch)", show_for=2000)  # reverts to clock after 2s
    else:
        dm.show_clock()
    display_task = asyncio.create_task(dm.run())
    await asyncio.sleep_ms(SLEEP_TIMEOUT_MS)
    display_task.cancel()
    dm.off()


def run_sleep_phase():
    """Poll via lightsleep until button or touch wakes us. Returns wake reason."""
    while True:
        lightsleep(TOUCH_POLL_MS)
        reason = wake_reason()
        if reason == machine.EXT0_WAKE:
            return "button"
        if is_touched():
            return "touch"


while True:
    wake = run_sleep_phase()                # lightsleep owns CPU while display is off
    asyncio.run(run_awake_phase(wake))      # asyncio owns CPU while display is on
