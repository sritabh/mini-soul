from machine import I2C
import struct

DS3231_ADDR = 0x68

class DS3231:
    def __init__(self, i2c):
        self.i2c = i2c

    def _bcd2dec(self, bcd):
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def _dec2bcd(self, dec):
        return (dec // 10) << 4 | (dec % 10)

    def datetime(self):
        data = self.i2c.readfrom_mem(DS3231_ADDR, 0x00, 7)
        ss = self._bcd2dec(data[0])
        mm = self._bcd2dec(data[1])
        hh = self._bcd2dec(data[2] & 0x3F)
        dd = self._bcd2dec(data[4])
        mo = self._bcd2dec(data[5] & 0x1F)
        yy = self._bcd2dec(data[6]) + 2000
        return (yy, mo, dd, hh, mm, ss)

    def set_datetime(self, yy, mo, dd, hh, mm, ss):
        self.i2c.writeto_mem(DS3231_ADDR, 0x00, bytes([
            self._dec2bcd(ss),
            self._dec2bcd(mm),
            self._dec2bcd(hh),
            0,
            self._dec2bcd(dd),
            self._dec2bcd(mo),
            self._dec2bcd(yy - 2000)
        ]))
