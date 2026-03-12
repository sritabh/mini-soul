from machine import SoftI2C, Pin
from ds3231 import DS3231
from ssd1306 import SSD1306_I2C
import time
import urandom

i2c = SoftI2C(sda=Pin(8), scl=Pin(9))
rtc = DS3231(i2c)
oled = SSD1306_I2C(128, 64, i2c)

EEPROM_ADDR = 0x57
FLAG_ADDR = 0x0000
FLAG_VALUE = 0xAB

def eeprom_write(addr, value):
    i2c.writeto(EEPROM_ADDR, bytes([addr >> 8, addr & 0xFF, value]))
    time.sleep_ms(10)

def eeprom_read(addr):
    i2c.writeto(EEPROM_ADDR, bytes([addr >> 8, addr & 0xFF]))
    return i2c.readfrom(EEPROM_ADDR, 1)[0]

def is_time_set():
    return eeprom_read(FLAG_ADDR) == FLAG_VALUE

def mark_time_set():
    eeprom_write(FLAG_ADDR, FLAG_VALUE)

def init_rtc(force_set=False):
    if force_set or not is_time_set():
        rtc.set_datetime(2026, 3, 11, 22, 13, 0)
        mark_time_set()

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

def get_time_strings():
    yy, mo, dd, hh, mm, ss = rtc.datetime()
    period = "AM" if hh < 12 else "PM"
    hh12 = hh % 12 or 12
    time_str = "{:02d}:{:02d}:{:02d} {}".format(hh12, mm, ss, period)
    date_str = "{:02d}/{:02d}/{:04d}".format(dd, mo, yy)
    return time_str, date_str

def draw_frame(blinking=False):
    time_str, date_str = get_time_strings()
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
init_rtc(force_set=False)

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

