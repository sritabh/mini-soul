"""
eyes_demo.py — Cycles through all expressions to verify rendering on the OLED.

Flash to the ESP32 and it will rotate through each expression every 2 seconds.
"""

from machine import SoftI2C, Pin
from ssd1306 import SSD1306_I2C
import time

from eyes import (
    Eyes,
    EXPR_NORMAL, EXPR_HAPPY, EXPR_SAD, EXPR_ANGRY,
    EXPR_SURPRISED, EXPR_SLEEPY, EXPR_FURIOUS,
    EXPR_FEARFUL, EXPR_SUSPICIOUS, EXPR_ANNOYED,
)

# --- Hardware setup (match your wiring) ---
i2c  = SoftI2C(sda=Pin(8), scl=Pin(9))
oled = SSD1306_I2C(128, 64, i2c)

eyes = Eyes(oled)

# Expression sequence to cycle through
SEQUENCE = [
    (EXPR_NORMAL,     "Normal"),
    (EXPR_HAPPY,      "Happy"),
    (EXPR_SAD,        "Sad"),
    (EXPR_ANGRY,      "Angry"),
    (EXPR_SURPRISED,  "Surprised"),
    (EXPR_SLEEPY,     "Sleepy"),
    (EXPR_FURIOUS,    "Furious"),
    (EXPR_FEARFUL,    "Fearful"),
    (EXPR_SUSPICIOUS, "Suspicious"),
    (EXPR_ANNOYED,    "Annoyed"),
]

HOLD_MS = 2000   # how long to display each expression

idx = 0
while True:
    expr, label = SEQUENCE[idx]
    print("Expression:", label)

    eyes.set_expression(expr)
    eyes.draw()
    oled.show()

    time.sleep_ms(HOLD_MS)
    idx = (idx + 1) % len(SEQUENCE)
