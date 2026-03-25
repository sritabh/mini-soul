import machine
import esp32
import time
import uasyncio as asyncio
from ssd1306 import SSD1306_I2C
import rtc_utils
from display_manager import DisplayManager
from button import Button

SLEEP_TIMEOUT_MS = 5000
TOUCH_PIN = 7

cause = machine.reset_cause()

oled = SSD1306_I2C(128, 64, rtc_utils.i2c)
dm   = DisplayManager(oled)

if cause == machine.DEEPSLEEP_RESET:
    wake = machine.wake_reason()
    if wake == machine.TOUCHPAD_WAKE:
        t = machine.TouchPad(machine.Pin(7))
        val = t.read()
        dm.show_text(f"T:{val}", show_for=3000)
        time.sleep_ms(3000)


_last_activity = time.ticks_ms()

def reset_sleep_timer():
    global _last_activity
    _last_activity = time.ticks_ms()


def handle_press():
    reset_sleep_timer()
    dm.show_text("Hello!", show_for=2000)

btn = Button(pin_num=2, on_single=handle_press)


def go_to_sleep():
    return
    machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP).irq(handler=None)
    t = machine.TouchPad(machine.Pin(7))
    t.config(30000)
    esp32.wake_on_touch(True)
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
