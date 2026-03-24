from ssd1306 import SSD1306_I2C
import uasyncio as asyncio
import rtc_utils
from display_manager import DisplayManager


oled = SSD1306_I2C(128, 64, rtc_utils.i2c)
dm   = DisplayManager(oled)


async def main():
    dm.show_clock()
    await dm.run()


asyncio.run(main())
