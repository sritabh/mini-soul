from machine import Pin
from ssd1306 import SSD1306_I2C
import time
import urandom
import rtc_utils

oled = SSD1306_I2C(128, 64, rtc_utils.i2c)

def draw_oval(cx, cy, rx, ry, col=1):
    for y in range(-ry, ry + 1):
        for x in range(-rx, rx + 1):
            if (x * x * ry * ry + y * y * rx * rx) <= (rx * rx * ry * ry):
                oled.pixel(cx + x, cy + y, col)

def draw_eyes(blinking=False):
    lx, ly = 36, 22   # left eye center
    rx, ry = 92, 22   # right eye center
    eye_rx = 10        # narrow width
    eye_ry = 16        # tall height

    if blinking:
        oled.hline(lx - eye_rx, ly, eye_rx * 2, 1)
        oled.hline(rx - eye_rx, ry, eye_rx * 2, 1)
    else:
        draw_oval(lx, ly, eye_rx, eye_ry)
        draw_oval(rx, ry, eye_rx, eye_ry)
        # Pupils — small filled circle
        draw_oval(lx, ly, 3, 4)
        draw_oval(rx, ry, 3, 4)


def draw_frame(blinking=False):
    time_str, date_str = rtc_utils.get_time_strings()
    oled.fill(0)
    draw_eyes(blinking=blinking)
    oled.hline(0, 44, 128, 1)

    # center text: (128 - len * 8) // 2
    time_x = (128 - len(time_str) * 8) // 2
    date_x = (128 - len(date_str) * 8) // 2

    oled.text(time_str, time_x, 48)
    oled.text(date_str, date_x, 57)
    oled.show()

# --- Boot ---
rtc_utils.init_rtc(force_set=False, new_time=(2026, 3, 11, 22, 13, 0))

# --- Main loop ---
tick = 0
next_blink = urandom.getrandbits(4) + 3

while True:
    draw_frame(blinking=False)
    time.sleep(1)
    tick += 1

    if tick >= next_blink:
        draw_frame(blinking=True)
        time.sleep_ms(150)
        draw_frame(blinking=False)
        tick = 0
        next_blink = urandom.getrandbits(4) + 3
