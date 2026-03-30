# main.py
import machine
import esp32
import time
import rtc_utils
from display_manager import DisplayManager
from machine import TouchPad, Pin, lightsleep, wake_reason
import uasyncio as asyncio

SLEEP_TIMEOUT_MS    = 5000
TOUCH_POLL_MS       = 400

BUTTON_PIN          = 2
TOUCH_PIN           = 4
TOUCH_THRESHOLD_PCT = 1.2

dm = DisplayManager(rtc_utils.i2c)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=button, level=esp32.WAKEUP_ANY_HIGH)

touch_pad = TouchPad(Pin(TOUCH_PIN))
time.sleep(1) # Needed for stable touch readings after boot
_touch_baseline  = touch_pad.read()
_touch_threshold = int(_touch_baseline * TOUCH_THRESHOLD_PCT)
print(f"Touch baseline={_touch_baseline}  threshold={_touch_threshold}")

def is_touched():
    return touch_pad.read() > _touch_threshold


async def handle_on_touch():
    """Show animated face with random expressions for the awake duration."""
    dm.show_face()
    display_task = asyncio.create_task(dm.run())
    await asyncio.sleep_ms(SLEEP_TIMEOUT_MS)
    display_task.cancel()


async def handle_on_click():
    """Show clock face for the awake duration."""
    dm.show_clock()
    display_task = asyncio.create_task(dm.run())
    await asyncio.sleep_ms(SLEEP_TIMEOUT_MS)
    display_task.cancel()


async def run_awake_phase(wake):
    dm.awake_from_sleep()  # re-init OLED and VCC after lightsleep
    if wake == "touch":
        await handle_on_touch()
    else:
        await handle_on_click()


def run_sleep_phase():
    """Poll via lightsleep until button or touch wakes us. Returns wake reason."""
    while True:
        lightsleep(TOUCH_POLL_MS)
        reason = wake_reason()
        if reason == machine.EXT0_WAKE:
            return "button"
        if is_touched():
            return "touch"


# On first boot treat it as a button wake so the display comes on immediately
asyncio.run(run_awake_phase("button"))

while True:
    wake = run_sleep_phase()                # lightsleep owns CPU while display is off
    asyncio.run(run_awake_phase(wake))      # asyncio owns CPU while display is on
