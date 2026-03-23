"""
eyes — Animated robot eyes for SSD1306 OLED (MicroPython).

Public API re-exported from this package so that existing code using
    from eyes import Eyes, EXPR_HAPPINESS, ...
continues to work without any changes.

Sub-modules
-----------
eyes.config     — DisplayConfig, EyeConfig
eyes.presets    — _presets(), EXPR_* constants
eyes.anim       — lerp_eye_config(), apply_blink(), timing constants
eyes.draw       — draw_eye(), low-level helpers
eyes.controller — Eyes class
"""

from eyes.config import DisplayConfig, EyeConfig

from eyes.presets import (
    _presets,
    # Six basic expressions
    EXPR_SADNESS,
    EXPR_ANGER,
    EXPR_HAPPINESS,
    EXPR_SURPRISE,
    EXPR_DISGUST,
    EXPR_FEAR,
    # Sub-faces of sadness
    EXPR_PLEADING,
    EXPR_VULNERABLE,
    EXPR_DESPAIR,
    # Secondary middle row
    EXPR_GUILTY,
    EXPR_DISAPPOINTED,
    EXPR_EMBARRASSED,
    # Sub-faces of disgust and anger
    EXPR_HORRIFIED,
    EXPR_SKEPTICAL,
    EXPR_ANNOYED,
    # Sub-faces of surprise
    EXPR_CONFUSED,
    EXPR_AMAZED,
    EXPR_EXCITED,
    # Bad expressions
    EXPR_FURIOUS,
    EXPR_SUSPICIOUS,
    EXPR_REJECTED,
    EXPR_BORED,
    EXPR_TIRED,
    EXPR_ASLEEP,
    # Neutral / internal
    EXPR_NORMAL,
)

from eyes.anim import lerp_eye_config, apply_blink
from eyes.draw import draw_eye
from eyes.controller import Eyes
