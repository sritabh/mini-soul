import machine
import esp32
import time
import uasyncio as asyncio
from ssd1306 import SSD1306_I2C
import rtc_utils
from display_manager import DisplayManager

SLEEP_TIMEOUT_MS = 5000

cause = machine.reset_cause()

oled = SSD1306_I2C(128, 64, rtc_utils.i2c)
dm   = DisplayManager(oled)

if cause == machine.DEEPSLEEP_RESET:
    wake = machine.wake_reason()
    if wake == machine.EXT1_WAKE:        # Changed from EXT0_WAKE to EXT1_WAKE
        dm.show_text("Awake!", show_for=2000)

# Create pin ONCE at top level
wake1 = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_DOWN)

_last_activity = time.ticks_ms()

def reset_sleep_timer():
    global _last_activity
    _last_activity = time.ticks_ms()

def go_to_sleep():
    esp32.wake_on_ext1(pins=(wake1,), level=esp32.WAKEUP_ANY_HIGH)  # Changed to ext1
    time.sleep_ms(200)
    dm.off()
    machine.deepsleep()

async def main():
    dm.show_clock()

    async def sleep_watcher():
        while True:
            if time.ticks_diff(time.ticks_ms(), _last_activity) >= SLEEP_TIMEOUT_MS:
                go_to_sleep()
            await asyncio.sleep_ms(500)

    await asyncio.gather(dm.run(), sleep_watcher())

asyncio.run(main())
