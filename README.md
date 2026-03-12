# Setting up board

1. Erase the flash memory of the board using the following command:

```bash
esptool.py --chip esp32s3 --port /dev/cu.usbmodem1101 erase_flash
```

2. Flash the firmware to the board using the following command:

```bash
esptool.py --chip esp32s3 --port /dev/cu.usbmodem1101 write_flash -z 0x0 ~/Downloads/ESP32_GENERIC_S3-20251209-v1.27.0.bin
```

3. Remote connection

```bash
pip3 install mpremote

mpremote connect /dev/cu.usbmodem1101
```


# Sample Programs

## Onboard LED

```python
from machine import Pin
from neopixel import NeoPixel
from time import sleep

np = NeoPixel(Pin(48), 1)

colors = [
    (255, 0, 0),    # Red
    (255, 165, 0),  # Orange
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (128, 0, 128),  # Purple
]

while True:
    for color in colors:
        np[0] = color
        np.write()
        sleep(0.5)


np[0] = (0, 0, 0)  # turn off
np.write()
```

## OLED Display

```python
from machine import SoftI2C, Pin
from ssd1306 import SSD1306_I2C

i2c = SoftI2C(sda=Pin(8), scl=Pin(9))
oled = SSD1306_I2C(128, 64, i2c)

oled.text("Hello!", 0, 0)
oled.show()
```


# Check RTC Memory

```python
from machine import SoftI2C, Pin

i2c = SoftI2C(sda=Pin(8), scl=Pin(9))

EEPROM_ADDR = 0x57
EEPROM_TOTAL = 4096  # AT24C32 = 4KB

def eeprom_read(addr):
    i2c.writeto(EEPROM_ADDR, bytes([addr >> 8, addr & 0xFF]))
    return i2c.readfrom(EEPROM_ADDR, 1)[0]

# Scan how many bytes are written (non 0xFF)
print("=== EEPROM Usage ===")
print("Scanning... (this takes a moment)")

used = 0
for addr in range(EEPROM_TOTAL):
    if eeprom_read(addr) != 0xFF:
        used += 1

free = EEPROM_TOTAL - used

print("EEPROM Total: {} bytes ({} KB)".format(EEPROM_TOTAL, EEPROM_TOTAL // 1024))
print("EEPROM Used:  {} bytes".format(used))
print("EEPROM Free:  {} bytes".format(free))
print("Used by clock flag: 1 byte at 0x0000")
```

## Check ESP32 memory

```python
import gc
import os

# --- ESP32 RAM ---
gc.collect()
ram_free = gc.mem_free()
ram_used = gc.mem_alloc()
ram_total = ram_free + ram_used

print("=== ESP32 Memory ===")
print("RAM Free:  {} bytes ({} KB)".format(ram_free, ram_free // 1024))
print("RAM Used:  {} bytes ({} KB)".format(ram_used, ram_used // 1024))
print("RAM Total: {} bytes ({} KB)".format(ram_total, ram_total // 1024))

# --- Flash Storage ---
fs = os.statvfs('/')
block_size  = fs[0]
total_blocks = fs[2]
free_blocks  = fs[3]

flash_total = block_size * total_blocks
flash_free  = block_size * free_blocks
flash_used  = flash_total - flash_free

print("\n=== Flash Storage ===")
print("Flash Free:  {} bytes ({} KB)".format(flash_free, flash_free // 1024))
print("Flash Used:  {} bytes ({} KB)".format(flash_used, flash_used // 1024))
print("Flash Total: {} bytes ({} KB)".format(flash_total, flash_total // 1024))
```
