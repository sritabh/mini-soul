"""
eyes/presets.py — Expression presets and EXPR_* name constants.
"""

from eyes.config import EyeConfig


# ---------------------------------------------------------------------------
# Expression presets  (right-eye config; left eye is auto-mirrored)
# ---------------------------------------------------------------------------
# Scaled relative to EYE_SIZE=40 (the reference used in the C++ original).

def _presets(eye_size):
    """Return a dict of expression-name → (right_cfg, left_cfg or None).

    If left_cfg is None the right_cfg is auto-mirrored for the left eye.
    Provide explicit left_cfg only for intentionally asymmetric expressions
    such as EXPR_SKEPTICAL and EXPR_CONFUSED.

    Slope convention (right eye):
      slope_top > 0  →  outer (right) top corner drops  →  sad / droopy family
      slope_top < 0  →  inner (left)  top corner drops  →  angry / focused family
    mirror() negates both slope signs automatically.
    """
    s = eye_size / 40.0   # scale vs. reference eye_size=40

    def sc(v):
        return int(v * s)

    def mk(w, h, ox=0, oy=0, st=0.0, sb=0.0, rt=8, rb=8):
        return EyeConfig(sc(w), sc(h), sc(ox), sc(oy), st, sb, sc(rt), sc(rb))

    p = {}

    # ------------------------------------------------------------------
    # Internal neutral state (not part of the 24 emotions but useful as
    # a reset / starting point).
    # ------------------------------------------------------------------
    p['normal']      = (mk(40, 40, rt=8,  rb=8),  None)

    # ------------------------------------------------------------------
    # Six basic expressions
    # ------------------------------------------------------------------

    # SADNESS: narrow, outer corners drooping, sharp top, rounded bottom
    p['sadness']     = (mk(40, 15, st= 0.50, rt=1,  rb=10), None)

    # ANGER: inner top corners pushed down hard, sharp top, large bottom radius
    p['anger']       = (mk(40, 18, ox=-3, st=-0.40, rt=1,  rb=12), None)

    # HAPPINESS: short arch/dome, flat-ish bottom, fully rounded top, shifted up
    p['happiness']   = (mk(40, 14, oy=-7, rt=10, rb=3),  None)

    # SURPRISE: large, nearly circular eyes — no inward offset to avoid overlap
    p['surprise']    = (mk(45, 45, rt=16, rb=16), None)

    # DISGUST: narrow, slight outer-corner drop (sneer), flat angular top
    p['disgust']     = (mk(40, 12, st= 0.15, rt=2,  rb=6),  None)

    # FEAR: wide open, more outer-corner droop for expressive scared look
    p['fear']        = (mk(44, 44, ox=-3, st= 0.25, rt=14, rb=10), None)

    # ------------------------------------------------------------------
    # Sub-faces of sadness
    # ------------------------------------------------------------------

    # PLEADING: large puppy-dog eyes, strong outer droop, shifted slightly down
    p['pleading']    = (mk(44, 32, oy= 3, st= 0.45, rt=12, rb=14), None)

    # VULNERABLE: dramatic outer droop on both top AND bottom edges (tearful)
    p['vulnerable']  = (mk(40, 28, st= 0.40, sb= 0.20, rt=4, rb=10), None)

    # DESPAIR: extreme outer drop, very narrow
    p['despair']     = (mk(40, 13, st= 0.65, rt=1,  rb=6),  None)

    # ------------------------------------------------------------------
    # Secondary middle row
    # ------------------------------------------------------------------

    # GUILTY: wide eye shifted down, top radius dominates height → strong arch = curved lid
    p['guilty']      = (mk(40, 20, oy= 5, st= 0.10, rt=14, rb= 6), None)

    # DISAPPOINTED: narrow, slight outer droop, centred (no lateral offset)
    p['disappointed'] = (mk(40, 13, st= 0.20, rt=2,  rb=10), None)

    # EMBARRASSED: short, eyes shifted DOWN (looking away), no slope
    p['embarrassed'] = (mk(40, 13, oy= 4, rt=3,  rb=10), None)

    # ------------------------------------------------------------------
    # Sub-faces of disgust and anger
    # ------------------------------------------------------------------

    # HORRIFIED: large eyes, inner corners slightly lower (alarmed/shocked tented top)
    p['horrified']   = (mk(46, 38, ox= 1, st=-0.18, sb= 0.08, rt=14, rb=12), None)

    # SKEPTICAL: intentionally asymmetric
    #   right eye squints with downward inner slope
    #   left  eye stays wide open
    p['skeptical']   = (mk(40, 22, oy=-5, st=-0.25, rt=2,  rb=8),
                        mk(40, 40,                   rt=8,  rb=8))

    # ANNOYED: asymmetric — right eye narrow flat-top, left eye just a thin slit
    #   mirrors C++ Preset_Annoyed (h=12) + Preset_Annoyed_Alt (h=5)
    p['annoyed']     = (mk(40, 12, rt=0,  rb=10),
                        mk(40,  5, rt=0,  rb=4))

    # ------------------------------------------------------------------
    # Sub-faces of surprise
    # ------------------------------------------------------------------

    # CONFUSED: intentionally asymmetric — each eye tilts a different way
    p['confused']    = (mk(46, 32, st= 0.25, rt=10, rb=14),
                        mk(40, 22, st=-0.20, rt=6,  rb=8))

    # AMAZED: maximum openness, perfectly round
    p['amazed']      = (mk(48, 48, rt=18, rb=18), None)

    # EXCITED: wide open, outer corners slightly lower, eyes slightly apart
    p['excited']     = (mk(46, 36, ox= 2, st= 0.15, rt=14, rb=14), None)

    # ------------------------------------------------------------------
    # "Bad" expressions
    # ------------------------------------------------------------------

    # FURIOUS: extreme anger, steep inner drop, tall
    p['furious']     = (mk(40, 30, ox=-2, st=-0.40, rt=2,  rb=8),  None)

    # SUSPICIOUS: asymmetric brow — right narrows, left differs
    p['suspicious']  = (mk(40, 22, st=-0.15, rt=6,  rb=3),
                        mk(40, 16, oy=-3, st= 0.15, rt=5,  rb=3))

    # REJECTED: outer corners collapse, very narrow
    p['rejected']    = (mk(40, 12, ox=-2, st= 0.55, rt=1,  rb=5),  None)

    # BORED: half-closed, eye floats to lower half of socket
    p['bored']       = (mk(40, 20, oy= 5, rt=8,  rb=14), None)

    # TIRED: narrow, both top and bottom slope same direction (drooping)
    p['tired']       = (mk(40, 10, oy=-2, st= 0.35, sb= 0.35, rt=3, rb=3), None)

    # ASLEEP: eyes reduced to a thin sliver
    p['asleep']      = (mk(40,  4, rt=2,  rb=2),  None)

    return p


# ---------------------------------------------------------------------------
# Expression name constants
# ---------------------------------------------------------------------------
# Six basic expressions
EXPR_SADNESS      = 'sadness'
EXPR_ANGER        = 'anger'
EXPR_HAPPINESS    = 'happiness'
EXPR_SURPRISE     = 'surprise'
EXPR_DISGUST      = 'disgust'
EXPR_FEAR         = 'fear'
# Sub-faces of sadness
EXPR_PLEADING     = 'pleading'
EXPR_VULNERABLE   = 'vulnerable'
EXPR_DESPAIR      = 'despair'
# Secondary middle row
EXPR_GUILTY       = 'guilty'
EXPR_DISAPPOINTED = 'disappointed'
EXPR_EMBARRASSED  = 'embarrassed'
# Sub-faces of disgust and anger
EXPR_HORRIFIED    = 'horrified'
EXPR_SKEPTICAL    = 'skeptical'
EXPR_ANNOYED      = 'annoyed'
# Sub-faces of surprise
EXPR_CONFUSED     = 'confused'
EXPR_AMAZED       = 'amazed'
EXPR_EXCITED      = 'excited'
# Bad expressions
EXPR_FURIOUS      = 'furious'
EXPR_SUSPICIOUS   = 'suspicious'
EXPR_REJECTED     = 'rejected'
EXPR_BORED        = 'bored'
EXPR_TIRED        = 'tired'
EXPR_ASLEEP       = 'asleep'
# Neutral (internal, not one of the 24 emotions)
EXPR_NORMAL       = 'normal'
