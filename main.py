# main.py
import machine
import esp32
import time
import struct
from machine import TouchPad, Pin, deepsleep, wake_reason, reset_cause, RTC
import uasyncio as asyncio

SLEEP_MS            = 400       # deep sleep poll interval (ms)
AWAKE_TIMEOUT_MS    = 5000

BUTTON_PIN          = 2
TOUCH_PIN           = 4
TOUCH_THRESHOLD_PCT = 1.2

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=button, level=esp32.WAKEUP_ANY_HIGH)

touch_pad = TouchPad(Pin(TOUCH_PIN))
rtc = RTC()

# Calibrate touch baseline on first boot; persist across deep sleeps via RTC memory.
if reset_cause() != machine.DEEPSLEEP_RESET:
    time.sleep(1)  # stabilise touch readings after power-on
    _baseline  = touch_pad.read()
    _threshold = int(_baseline * TOUCH_THRESHOLD_PCT)
    rtc.memory(struct.pack('II', _baseline, _threshold))
    print(f"First boot: baseline={_baseline}, threshold={_threshold}")
else:
    _baseline, _threshold = struct.unpack('II', rtc.memory()[:8])
    print(f"Deep sleep wake: baseline={_baseline}, threshold={_threshold}")


def is_touched():
    return touch_pad.read() > _threshold


async def run_awake_phase(wake):
    # Import here so the display is never initialised during touch-poll wakes.
    import rtc_utils
    from display_manager import DisplayManager
    dm = DisplayManager(rtc_utils.i2c)
    if wake == "touch":
        dm.show_text("Woke up!", "(touch)", show_for=2000)  # reverts to clock after 2s
    else:
        dm.show_clock()
    display_task = asyncio.create_task(dm.run())
    await asyncio.sleep_ms(AWAKE_TIMEOUT_MS)
    display_task.cancel()
    dm._vcc.value(0)  # cut OLED power before entering deep sleep


# Determine why we woke and act accordingly.
_reason = wake_reason()

if reset_cause() != machine.DEEPSLEEP_RESET or _reason == machine.EXT0_WAKE:
    # First boot or button press: bring up the clock face.
    asyncio.run(run_awake_phase("button"))
elif _reason == machine.TIMER_WAKE and is_touched():
    # Periodic timer wake with a touch detected.
    asyncio.run(run_awake_phase("touch"))

deepsleep(SLEEP_MS)
