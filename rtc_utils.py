from machine import SoftI2C, Pin
from ds3231 import DS3231
import time

EEPROM_ADDR = 0x57
FLAG_ADDR = 0x0000
FLAG_VALUE = 0xAB

# Power up RTC module before initialising I2C
_rtc_pwr = Pin(6, Pin.OUT, value=1)
time.sleep_ms(10)  # allow rail to stabilise

i2c = SoftI2C(sda=Pin(8), scl=Pin(9))
rtc = DS3231(i2c)


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


def init_rtc(force_set=False, new_time=None):
    if force_set or not is_time_set():
        if new_time:
            rtc.set_datetime(*new_time)
        else:
            rtc.set_datetime(2026, 3, 11, 22, 13, 0)
        mark_time_set()


_MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
_DAYS   = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']


def _day_of_week(y, m, d):
    t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    if m < 3:
        y -= 1
    return (y + y // 4 - y // 100 + y // 400 + t[m - 1] + d) % 7


def get_time_raw():
    """Return (yy, mo, dd, hh, mm, ss, dow, mon, hh12, period)."""
    yy, mo, dd, hh, mm, ss = rtc.datetime()
    period = "AM" if hh < 12 else "PM"
    hh12   = hh % 12 or 12
    dow    = _DAYS[_day_of_week(yy, mo, dd)]
    mon    = _MONTHS[mo - 1]
    return yy, mo, dd, hh, mm, ss, dow, mon, hh12, period


def get_time_strings():
    yy, mo, dd, hh, mm, ss = rtc.datetime()
    period = "AM" if hh < 12 else "PM"
    hh12 = hh % 12 or 12
    time_str = "{:02d}:{:02d}:{:02d} {}".format(hh12, mm, ss, period)
    date_str = "{:02d}/{:02d}/{:04d}".format(dd, mo, yy)
    return time_str, date_str
