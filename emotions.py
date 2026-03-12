from machine import SoftI2C, Pin
from ssd1306 import SSD1306_I2C
import time
import urandom

i2c = SoftI2C(sda=Pin(8), scl=Pin(9))
oled = SSD1306_I2C(128, 64, i2c)

W, H = 128, 64
EYE_Y = 22

# --- Drawing Primitives ---

def draw_oval(cx, cy, rx, ry, col=1):
    for y in range(-ry, ry + 1):
        for x in range(-rx, rx + 1):
            if (x * x * ry * ry + y * y * rx * rx) <= (rx * rx * ry * ry):
                oled.pixel(cx + x, cy + y, col)

def draw_arc(cx, cy, rx, ry, top=True, col=1):
    for x in range(-rx, rx + 1):
        y = int(ry * (1 - (x / rx) ** 2) ** 0.5)
        if top:
            oled.pixel(cx + x, cy - y, col)
        else:
            oled.pixel(cx + x, cy + y, col)

def draw_line(x0, y0, x1, y1, col=1):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        oled.pixel(x0, y0, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

# --- Eye Shapes ---

def eyes_normal(lx, rx):
    draw_oval(lx, EYE_Y, 10, 16)
    draw_oval(rx, EYE_Y, 10, 16)
    draw_oval(lx, EYE_Y, 3, 4)
    draw_oval(rx, EYE_Y, 3, 4)

def eyes_happy(lx, rx):
    # Squinted upward arcs
    for x in range(-10, 11):
        y = int(8 * (1 - (x / 10) ** 2) ** 0.5)
        oled.pixel(lx + x, EYE_Y + y, 1)
        oled.pixel(rx + x, EYE_Y + y, 1)
    oled.hline(lx - 10, EYE_Y, 21, 1)
    oled.hline(rx - 10, EYE_Y, 21, 1)

def eyes_sad(lx, rx):
    draw_oval(lx, EYE_Y + 4, 10, 13)
    draw_oval(rx, EYE_Y + 4, 10, 13)
    draw_oval(lx, EYE_Y + 4, 3, 4)
    draw_oval(rx, EYE_Y + 4, 3, 4)
    # Angled brows pointing down inward
    draw_line(lx - 10, EYE_Y - 12, lx + 4, EYE_Y - 8, 1)
    draw_line(rx - 4,  EYE_Y - 8,  rx + 10, EYE_Y - 12, 1)

def eyes_surprised(lx, rx):
    # Wide open circles
    draw_oval(lx, EYE_Y, 13, 13)
    draw_oval(rx, EYE_Y, 13, 13)
    draw_oval(lx, EYE_Y, 4, 4)
    draw_oval(rx, EYE_Y, 4, 4)

def eyes_angry(lx, rx):
    draw_oval(lx, EYE_Y, 10, 14)
    draw_oval(rx, EYE_Y, 10, 14)
    draw_oval(lx, EYE_Y, 3, 4)
    draw_oval(rx, EYE_Y, 3, 4)
    # Brows angled down outward
    draw_line(lx - 10, EYE_Y - 10, lx + 6, EYE_Y - 16, 1)
    draw_line(rx - 6,  EYE_Y - 16, rx + 10, EYE_Y - 10, 1)

def eyes_sleepy(lx, rx):
    # Half closed — bottom half of oval covered
    draw_oval(lx, EYE_Y, 10, 16)
    draw_oval(rx, EYE_Y, 10, 16)
    oled.fill_rect(lx - 11, EYE_Y, 22, 18, 0)  # cover bottom half
    oled.fill_rect(rx - 11, EYE_Y, 22, 18, 0)
    draw_oval(lx, EYE_Y, 3, 3)
    draw_oval(rx, EYE_Y, 3, 3)

def eyes_curious(lx, rx):
    # One eye normal, one raised/bigger
    draw_oval(lx, EYE_Y, 10, 16)
    draw_oval(lx, EYE_Y, 3, 4)
    draw_oval(rx, EYE_Y - 4, 12, 18)  # raised and wider
    draw_oval(rx, EYE_Y - 4, 4, 5)
    # One raised brow
    draw_line(rx - 10, EYE_Y - 24, rx + 10, EYE_Y - 20, 1)

def eyes_awkward(lx, rx):
    draw_oval(lx, EYE_Y, 10, 16)
    draw_oval(rx, EYE_Y, 10, 16)
    # pupils shifted to corner
    draw_oval(lx + 5, EYE_Y + 5, 3, 4)
    draw_oval(rx + 5, EYE_Y + 5, 3, 4)
    # one flat brow
    oled.hline(rx - 10, EYE_Y - 18, 20, 1)

# --- Mouth Shapes ---

def mouth_normal(my):
    oled.hline(48, my, 32, 1)

def mouth_happy(my):
    draw_arc(64, my - 4, 18, 10, top=False)

def mouth_sad(my):
    draw_arc(64, my + 8, 18, 10, top=True)

def mouth_surprised(my):
    draw_oval(64, my, 7, 9)

def mouth_angry(my):
    # Flat tight line with downturned corners
    oled.hline(48, my, 32, 1)
    draw_line(48, my, 44, my + 4, 1)
    draw_line(80, my, 84, my + 4, 1)

def mouth_sleepy(my):
    # Slight open oval
    draw_oval(64, my, 8, 5)

def mouth_curious(my):
    # Slight smile one side
    draw_arc(64, my - 2, 14, 6, top=False)
    oled.pixel(50, my - 2, 1)

def mouth_awkward(my):
    # Wavy uncertain line
    for x in range(48, 80):
        y = my + (1 if (x // 4) % 2 == 0 else -1)
        oled.pixel(x, y, 1)

# --- Emotion Renderer ---

EMOTIONS = [
    "normal", "happy", "sad", "surprised",
    "angry", "sleepy", "curious", "awkward"
]

EYE_FUNCS = {
    "normal":    eyes_normal,
    "happy":     eyes_happy,
    "sad":       eyes_sad,
    "surprised": eyes_surprised,
    "angry":     eyes_angry,
    "sleepy":    eyes_sleepy,
    "curious":   eyes_curious,
    "awkward":   eyes_awkward,
}

MOUTH_FUNCS = {
    "normal":    mouth_normal,
    "happy":     mouth_happy,
    "sad":       mouth_sad,
    "surprised": mouth_surprised,
    "angry":     mouth_angry,
    "sleepy":    mouth_sleepy,
    "curious":   mouth_curious,
    "awkward":   mouth_awkward,
}

def draw_emotion(name):
    oled.fill(0)
    lx, rx = 36, 92
    my = 52
    EYE_FUNCS[name](lx, rx)
    MOUTH_FUNCS[name](my)
    oled.show()

def transition(from_e, to_e, steps=6):
    # Blink close → switch → blink open
    for i in range(steps):
        oled.fill(0)
        # Shrink eyes vertically
        ry = max(1, 16 - (i * 3))
        draw_oval(36, EYE_Y, 10, ry)
        draw_oval(92, EYE_Y, 10, ry)
        oled.show()
        time.sleep_ms(30)

    draw_emotion(to_e)

    for i in range(steps):
        oled.fill(0)
        ry = min(16, 1 + (i * 3))
        draw_oval(36, EYE_Y, 10, ry)
        draw_oval(92, EYE_Y, 10, ry)
        oled.show()
        time.sleep_ms(30)

    draw_emotion(to_e)

# --- Demo loop ---
current = "normal"
draw_emotion(current)
time.sleep(2)

while True:
    next_e = EMOTIONS[urandom.getrandbits(3) % len(EMOTIONS)]
    if next_e != current:
        print("->", next_e)
        transition(current, next_e)
        current = next_e
    time.sleep(4)
