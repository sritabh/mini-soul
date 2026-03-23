from machine import SoftI2C, Pin
from ssd1306 import SSD1306_I2C
import time
import math

i2c = SoftI2C(sda=Pin(8), scl=Pin(9))
oled = SSD1306_I2C(128, 64, i2c)

W, H = 128, 64
RADIUS = 6

x = float(RADIUS)
y = float(H // 2)
vx = 3.0
vy = 1.5

def draw_circle(cx, cy, r, col=1):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                oled.pixel(int(cx) + dx, int(cy) + dy, col)

while True:
    t0 = time.ticks_ms()

    # Erase
    draw_circle(x, y, RADIUS, 0)

    # Move
    x += vx
    y += vy

    # Bounce
    if x - RADIUS <= 0 or x + RADIUS >= W:
        vx = -vx
        x = max(RADIUS, min(W - RADIUS, x))
    if y - RADIUS <= 0 or y + RADIUS >= H:
        vy = -vy
        y = max(RADIUS, min(H - RADIUS, y))

    # Draw
    draw_circle(x, y, RADIUS, 1)
    oled.show()

    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    print("Frame time: {}ms (~{}fps)".format(elapsed, 1000 // max(elapsed, 1)))
