"""
eyes_demo.py — Cycles through all 24 expressions with smooth transitions.

Flash eyes.py + eyes_demo.py to the ESP32. The demo rotates through every
emotion every 2 seconds, morphing smoothly between them.
"""

from machine import SoftI2C, Pin
from ssd1306 import SSD1306_I2C
import time

from eyes import (
    Eyes,
    EXPR_NORMAL,
    # Six basic
    EXPR_SADNESS, EXPR_ANGER, EXPR_HAPPINESS,
    EXPR_SURPRISE, EXPR_DISGUST, EXPR_FEAR,
    # Sub-faces of sadness
    EXPR_PLEADING, EXPR_VULNERABLE, EXPR_DESPAIR,
    # Middle row
    EXPR_GUILTY, EXPR_DISAPPOINTED, EXPR_EMBARRASSED,
    # Sub-faces of disgust / anger
    EXPR_HORRIFIED, EXPR_SKEPTICAL, EXPR_ANNOYED,
    # Sub-faces of surprise
    EXPR_CONFUSED, EXPR_AMAZED, EXPR_EXCITED,
    # Bad expressions
    EXPR_FURIOUS, EXPR_SUSPICIOUS, EXPR_REJECTED,
    EXPR_BORED, EXPR_TIRED, EXPR_ASLEEP,
)

# --- Hardware setup (match your wiring) ---
i2c  = SoftI2C(sda=Pin(8), scl=Pin(9))
oled = SSD1306_I2C(128, 64, i2c)

# transition_ms controls morph duration between expressions
eyes = Eyes(oled, transition_ms=400)

# Ordered sequence matching the image layout
SEQUENCE = [
    (EXPR_NORMAL,       "Normal"),
    # Six basic
    (EXPR_SADNESS,      "Sadness"),
    (EXPR_ANGER,        "Anger"),
    (EXPR_HAPPINESS,    "Happiness"),
    (EXPR_SURPRISE,     "Surprise"),
    (EXPR_DISGUST,      "Disgust"),
    (EXPR_FEAR,         "Fear"),
    # Sub-faces of sadness
    (EXPR_PLEADING,     "Pleading"),
    (EXPR_VULNERABLE,   "Vulnerable"),
    (EXPR_DESPAIR,      "Despair"),
    # Middle
    (EXPR_GUILTY,       "Guilty"),
    (EXPR_DISAPPOINTED, "Disappointed"),
    (EXPR_EMBARRASSED,  "Embarrassed"),
    # Sub disgust/anger
    (EXPR_HORRIFIED,    "Horrified"),
    (EXPR_SKEPTICAL,    "Skeptical"),
    (EXPR_ANNOYED,      "Annoyed"),
    # Sub surprise
    (EXPR_CONFUSED,     "Confused"),
    (EXPR_AMAZED,       "Amazed"),
    (EXPR_EXCITED,      "Excited"),
    # Bad
    (EXPR_FURIOUS,      "Furious"),
    (EXPR_SUSPICIOUS,   "Suspicious"),
    (EXPR_REJECTED,     "Rejected"),
    (EXPR_BORED,        "Bored"),
    (EXPR_TIRED,        "Tired"),
    (EXPR_ASLEEP,       "Asleep"),
]

HOLD_MS = 2000   # hold each expression this long before switching

# Kick off the first expression
idx = 0
expr, label = SEQUENCE[idx]
print("Expression:", label)
eyes.set_expression(expr)
last_switch_ms = time.ticks_ms()

# --- Main loop: render every frame; switch expression on a timer ---
while True:
    now = time.ticks_ms()

    if time.ticks_diff(now, last_switch_ms) >= HOLD_MS:
        idx = (idx + 1) % len(SEQUENCE)
        expr, label = SEQUENCE[idx]
        print("Expression:", label)
        eyes.set_expression(expr)
        last_switch_ms = now

    eyes.draw()
    oled.show()
