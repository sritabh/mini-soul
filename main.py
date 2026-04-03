# main.py
import esp32
import time
import rtc_utils
from machine import TouchPad, Pin
import uasyncio as asyncio

from display_manager import DisplayManager
from button import Button
from sleep_controller import SleepController, WakeEvent
from modes.behavioral import BehavioralMode
from modes.clock import ClockMode
from modes.settings import SettingsMode

SLEEP_TIMEOUT_MS    = 5000
TOUCH_POLL_MS       = 400
BUTTON_PIN          = 2
TOUCH_PIN           = 4
TOUCH_THRESHOLD_PCT = 1.2


dm = DisplayManager(rtc_utils.i2c)

touch_pad        = TouchPad(Pin(TOUCH_PIN))
time.sleep(1)    # Needed for stable touch readings after boot
_touch_baseline  = touch_pad.read()
_touch_threshold = int(_touch_baseline * TOUCH_THRESHOLD_PCT)
print(f"Touch baseline={_touch_baseline}  threshold={_touch_threshold}")

sleep_ctrl = SleepController(touch_pad, _touch_threshold, poll_ms=TOUCH_POLL_MS)

_next_mode    = None
_current_task = None

def _on_button_click():
    global _next_mode
    _next_mode = ClockMode(dm, timeout_ms=SLEEP_TIMEOUT_MS)
    if _current_task is not None:
        _current_task.cancel()

def _on_button_hold():
    global _next_mode
    _next_mode = SettingsMode(dm)
    if _current_task is not None:
        _current_task.cancel()

btn = Button(pin_num=BUTTON_PIN, on_click=_on_button_click, on_hold=_on_button_hold)
esp32.wake_on_ext0(pin=btn._pin, level=esp32.WAKEUP_ANY_HIGH)

async def run_awake_phase(initial_wake):
    global _next_mode, _current_task

    dm.awake_from_sleep()

    if initial_wake == WakeEvent.TOUCH:
        mode = BehavioralMode(dm, timeout_ms=SLEEP_TIMEOUT_MS)
    else:
        mode = ClockMode(dm, timeout_ms=SLEEP_TIMEOUT_MS)

    while True:
        _next_mode = None
        _current_task = asyncio.create_task(mode.run())
        try:
            await _current_task
        except asyncio.CancelledError:
            pass

        if _next_mode is not None:
            mode = _next_mode
            _next_mode = None
            continue

        break  # mode finished naturally → go to sleep

    if initial_wake == WakeEvent.TOUCH:
        while sleep_ctrl.is_touched():
            await asyncio.sleep_ms(100)

asyncio.run(run_awake_phase(WakeEvent.BUTTON))

while True:
    wake = sleep_ctrl.wait_for_wake()       # lightsleep owns CPU
    asyncio.run(run_awake_phase(wake))      # asyncio owns CPU
