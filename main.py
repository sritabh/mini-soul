from ssd1306 import SSD1306_I2C
import rtc_utils
from clocks import ClockFace


oled = SSD1306_I2C(128, 64, rtc_utils.i2c)
clock = ClockFace(oled, face="digital_bold")
clock.run()
