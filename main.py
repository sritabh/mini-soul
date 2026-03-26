# main.py
import machine
import esp32
import time
from ssd1306 import SSD1306_I2C
import rtc_utils
from clocks import ClockFace
from machine import TouchPad, Pin, lightsleep, wake_reason
import uasyncio as asyncio

SLEEP_TIMEOUT_MS    = 5000
TOUCH_POLL_MS       = 400
CLOCK_TICK_MS       = 1000

BUTTON_PIN          = 2
TOUCH_PIN           = 4
TOUCH_THRESHOLD_PCT = 1.2

oled  = SSD1306_I2C(128, 64, rtc_utils.i2c)
clock = ClockFace(oled, face="digital_bold")

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=button, level=esp32.WAKEUP_ANY_HIGH)

touch_pad = TouchPad(Pin(TOUCH_PIN))
time.sleep(1) # Needed for stable touch readings after boot
_touch_baseline  = touch_pad.read()
_touch_threshold = int(_touch_baseline * TOUCH_THRESHOLD_PCT)
print(f"Touch baseline={_touch_baseline}  threshold={_touch_threshold}")

def is_touched():
    return touch_pad.read() > _touch_threshold

def turn_display_off():
    oled.fill(0)
    oled.show()


async def clock_runner(stop_event):
    """Tick the clock every second until stop_event is set."""
    while not stop_event.is_set():
        clock.tick()
        await asyncio.sleep_ms(CLOCK_TICK_MS)

async def timeout_runner(stop_event):
    """Set stop_event after SLEEP_TIMEOUT_MS."""
    await asyncio.sleep_ms(SLEEP_TIMEOUT_MS)
    stop_event.set()

async def run_awake_phase():
    stop_event = asyncio.Event()

    clock_task   = asyncio.create_task(clock_runner(stop_event))
    timeout_task = asyncio.create_task(timeout_runner(stop_event))

    await stop_event.wait()

    clock_task.cancel()
    timeout_task.cancel()

    turn_display_off()


def run_sleep_phase():
    """Poll via lightsleep until button or touch wakes us."""
    while True:
        lightsleep(TOUCH_POLL_MS)
        reason = wake_reason()
        if reason == machine.EXT0_WAKE or is_touched():
            return  # hand control back to awake phase


while True:
    asyncio.run(run_awake_phase())   # asyncio owns CPU while display is on
    run_sleep_phase()                # lightsleep owns CPU while display is off
