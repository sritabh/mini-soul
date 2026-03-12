from machine import SoftI2C, Pin
from ds3231 import DS3231
import time

i2c = SoftI2C(sda=Pin(8), scl=Pin(9))
rtc = DS3231(i2c)

EEPROM_ADDR = 0x57 # RTC EEPROM memory
FLAG_ADDR = 0x0000
FLAG_VALUE = 0xAB

def eeprom_write(addr, value):
    i2c.writeto(EEPROM_ADDR, bytes([addr >> 8, addr & 0xFF, value]))
    time.sleep_ms(10)

def eeprom_read(addr):
    i2c.writeto(EEPROM_ADDR, bytes([addr >> 8, addr & 0xFF]))
    return i2c.readfrom(EEPROM_ADDR, 1)[0]

def is_time_set():
    val = eeprom_read(FLAG_ADDR)
    print("EEPROM flag:", hex(val))
    return val == FLAG_VALUE

def mark_time_set():
    eeprom_write(FLAG_ADDR, FLAG_VALUE)
    print("Flag written:", hex(eeprom_read(FLAG_ADDR)))

def init_rtc(force_set=False):
    if force_set or not is_time_set():
        print("Setting time...")
        rtc.set_datetime(2026, 3, 7, 22, 20, 35)
        mark_time_set()
        print("Time set and flag saved.")
    else:
        print("Time already set, skipping.")

init_rtc(force_set=False)

while True:
    yy, mo, dd, hh, mm, ss = rtc.datetime()
    period = "AM" if hh < 12 else "PM"
    hh12 = hh % 12 or 12
    print("{}/{}/{} {:02d}:{:02d}:{:02d} {}".format(
        yy, mo, dd, hh12, mm, ss, period
    ))
    time.sleep(1)
