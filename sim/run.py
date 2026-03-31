"""
sim/run.py — Desktop OLED simulator.

Run from the project root:

    python sim/run.py

Keys
----
SPACE / ENTER / →   next expression  (emulates physical button press)
←                   previous expression
Q / ESC             quit

The window shows the 128×64 OLED display scaled 4× (512×256 px) plus a
status bar below with the current expression name and keyboard hint.
"""

import sys
import os

# ── Path setup ─────────────────────────────────────────────────────────────
# sim/ must be first so our stub modules shadow the MicroPython ones.
# Project root is second so the eyes/ package is importable.
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _here)
sys.path.insert(1, _root)

# ── MicroPython time shims ─────────────────────────────────────────────────
# Must happen BEFORE any import that touches `time.ticks_ms`.
import time as _time
_time.ticks_ms   = lambda: int(_time.monotonic() * 1000)
_time.ticks_diff = lambda a, b: a - b
_time.sleep_ms   = lambda ms: _time.sleep(ms / 1000)

# ── Now it's safe to import project code ──────────────────────────────────
import pygame
pygame.init()

from ssd1306 import SSD1306_I2C, SCALE, BG_COLOR, ON_COLOR  # sim version
from button  import Button                                    # sim version
from eyes.controller import Eyes
from eyes.presets import (
    EXPR_NORMAL,
    EXPR_SADNESS,     EXPR_ANGER,        EXPR_HAPPINESS,
    EXPR_SURPRISE,    EXPR_DISGUST,      EXPR_FEAR,
    EXPR_PLEADING,    EXPR_VULNERABLE,   EXPR_DESPAIR,
    EXPR_GUILTY,      EXPR_DISAPPOINTED, EXPR_EMBARRASSED,
    EXPR_HORRIFIED,   EXPR_SKEPTICAL,    EXPR_ANNOYED,
    EXPR_CONFUSED,    EXPR_AMAZED,       EXPR_EXCITED,
    EXPR_FURIOUS,     EXPR_SUSPICIOUS,   EXPR_REJECTED,
    EXPR_BORED,       EXPR_TIRED,        EXPR_ASLEEP,
)

import time

# ── Display (OLED + status bar) ────────────────────────────────────────────
OLED_W, OLED_H = 128, 64
BAR_H          = 28            # pixels below OLED for the status bar

# Resize the existing pygame window to include the status bar.
win_w = OLED_W * SCALE
win_h = OLED_H * SCALE + BAR_H
oled  = SSD1306_I2C(OLED_W, OLED_H)            # creates the base window
pygame.display.set_mode((win_w, win_h))         # extend it for the status bar
screen = pygame.display.get_surface()

font_big   = pygame.font.SysFont("monospace", 14, bold=True)
font_small = pygame.font.SysFont("monospace", 11)

# ── Expressions ───────────────────────────────────────────────────────────
SEQUENCE = [
    (EXPR_NORMAL,       "Normal"),
    (EXPR_SADNESS,      "Sadness"),
    (EXPR_ANGER,        "Anger"),
    (EXPR_HAPPINESS,    "Happiness"),
    (EXPR_SURPRISE,     "Surprise"),
    (EXPR_DISGUST,      "Disgust"),
    (EXPR_FEAR,         "Fear"),
    (EXPR_PLEADING,     "Pleading"),
    (EXPR_VULNERABLE,   "Vulnerable"),
    (EXPR_DESPAIR,      "Despair"),
    (EXPR_GUILTY,       "Guilty"),
    (EXPR_DISAPPOINTED, "Disappointed"),
    (EXPR_EMBARRASSED,  "Embarrassed"),
    (EXPR_HORRIFIED,    "Horrified"),
    (EXPR_SKEPTICAL,    "Skeptical"),
    (EXPR_ANNOYED,      "Annoyed"),
    (EXPR_CONFUSED,     "Confused"),
    (EXPR_AMAZED,       "Amazed"),
    (EXPR_EXCITED,      "Excited"),
    (EXPR_FURIOUS,      "Furious"),
    (EXPR_SUSPICIOUS,   "Suspicious"),
    (EXPR_REJECTED,     "Rejected"),
    (EXPR_BORED,        "Bored"),
    (EXPR_TIRED,        "Tired"),
    (EXPR_ASLEEP,       "Asleep"),
]

HOLD_MS      = 2500   # ms before auto-advancing to the next expression
MID_BLINK_MS = 1200   # ms into each hold to fire a forced blink

# ── Eyes setup ────────────────────────────────────────────────────────────
eyes = Eyes(oled, transition_ms=400, auto_blink=True, blink_interval_ms=3500)

idx            = 0
expr, label    = SEQUENCE[idx]
last_switch_ms = time.ticks_ms()
mid_blinked    = False

eyes.set_expression(expr)
print(f"[sim] Expression {idx + 1}/{len(SEQUENCE)}: {label}")
pygame.display.set_caption(f"OLED Sim  {OLED_W}×{OLED_H}  —  {label}")


def _go_to(new_idx: int) -> None:
    global idx, expr, label, last_switch_ms, mid_blinked
    idx            = new_idx % len(SEQUENCE)
    expr, label    = SEQUENCE[idx]
    last_switch_ms = time.ticks_ms()
    mid_blinked    = False
    eyes.set_expression(expr)
    print(f"[sim] Expression {idx + 1}/{len(SEQUENCE)}: {label}")
    pygame.display.set_caption(f"OLED Sim  {OLED_W}×{OLED_H}  —  {label}")


def on_btn_press():
    _go_to(idx + 1)


def on_prev():
    _go_to(idx - 1)


# Register ← key as "previous" via a second Button (long_press slot)
btn_next = Button(pin_num=2, on_press=on_btn_press)
btn_prev = Button(pin_num=3, on_long_press=on_prev)


def _draw_status_bar(name: str, index: int, total: int) -> None:
    """Draw the info strip below the scaled OLED area."""
    bar_y  = OLED_H * SCALE
    bar_rect = pygame.Rect(0, bar_y, win_w, BAR_H)
    screen.fill((30, 30, 30), bar_rect)

    label_surf  = font_big.render(f"{name}  ({index}/{total})", True, (200, 200, 200))
    hint_surf   = font_small.render("SPACE/→ next   ← prev   Q quit", True, (100, 100, 100))

    screen.blit(label_surf, (6, bar_y + 3))
    screen.blit(hint_surf,  (6, bar_y + 16))


# ── Also handle Q/ESC directly so the status bar events are caught too ─────
import ssd1306 as _oled_mod

def _quit_listener(event):
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
        pygame.quit()
        sys.exit(0)

_oled_mod.add_event_listener(_quit_listener)

# ── Main loop ─────────────────────────────────────────────────────────────
clock = pygame.time.Clock()

while True:
    now     = time.ticks_ms()
    elapsed = time.ticks_diff(now, last_switch_ms)

    # Mid-hold forced blink (once per expression)
    if not mid_blinked and elapsed >= MID_BLINK_MS:
        eyes.blink()
        mid_blinked = True

    # # Auto-advance to next expression
    # if elapsed >= HOLD_MS:
    #     _go_to(idx + 1)

    eyes.draw()
    oled.show()   # renders OLED buffer + dispatches pygame events

    _draw_status_bar(label, idx + 1, len(SEQUENCE))
    pygame.display.flip()

    clock.tick(60)
