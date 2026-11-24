"""
art_gear.py - what armor and clothing look like ON the survivor.

Each worn item is a 64x64 overlay that lines up with the survivor sprite (which faces right):
  * cloaks are drawn BEHIND the survivor and trail out the back
  * body armor is drawn over the shoulders (with a hole so the head shows through)
  * helmets cover the top/back of the head but leave the face visible
Same painted style and assets/ override as art.py (e.g. assets/gear_iron_armor.png).
"""
import random

from PIL import ImageDraw, ImageFilter

from art import S, _ball, _canvas, _circle, _finish, _line, _poly, _rrect, _shade, _tex

HEAD_HOLE = (23, 21, 45, 43)     # the survivor's head, slightly padded


def _cut_head(img):
    """Punch the head out of a shoulder overlay so the face isn't covered."""
    ImageDraw.Draw(img).ellipse([v * S for v in HEAD_HOLE], fill=(0, 0, 0, 0))


# --------------------------------------------------------------------------- body armor
def _body(base, trim, style):
    def make():
        img = _canvas(64, 64)
        _ball(img, (15, 13, 45, 51), base + (255,))
        if style == "leather":
            for y in (22, 42):            # straps over the shoulders
                _line(img, [(17, y), (30, y)], _shade(trim, 0.7) + (255,), 2.2)
            _circle(img, 19, 22, 1.6, (200, 170, 90, 255))
            _circle(img, 19, 42, 1.6, (200, 170, 90, 255))
        elif style == "iron":
            for y0 in (13, 39):           # pauldrons
                _ball(img, (22, y0, 38, y0 + 12), _shade(base, 1.15) + (255,))
            for x, y in ((18, 20), (18, 44), (26, 16), (26, 48), (34, 16), (34, 48)):
                _circle(img, x, y, 1.1, (230, 232, 238, 255))
        elif style == "chitin":
            for k in range(4):            # overlapping shell plates
                x = 16 + k * 5
                _poly(img, [(x, 14), (x + 6, 14), (x + 8, 32), (x + 6, 50), (x, 50), (x + 2, 32)],
                      _shade(base, 0.85 + k * 0.08) + (255,), _shade(base, 0.45) + (255,), 0.8)
            for y0 in (12, 41):
                _poly(img, [(24, y0), (36, y0 + 2), (30, y0 + 9)], trim + (255,))
        elif style == "titan":
            for y0 in (11, 39):           # huge stone pauldrons
                _ball(img, (20, y0, 40, y0 + 14), _shade(base, 1.1) + (255,))
            rnd = random.Random(3)
            for _ in range(7):            # glowing cracks
                x, y = rnd.uniform(17, 36), rnd.uniform(15, 49)
                _line(img, [(x, y), (x + rnd.uniform(-4, 4), y + rnd.uniform(-5, 5))], trim + (255,), 1.6)
        _cut_head(img)
        return _finish(img, 64, 64)
    return make


BODY = {
    "leather_tunic": _body((150, 100, 56), (110, 72, 40), "leather"),
    "iron_armor": _body((150, 156, 168), (90, 94, 104), "iron"),
    "chitin_armor": _body((104, 146, 58), (200, 230, 120), "chitin"),
    "titan_plate": _body((104, 90, 76), (255, 150, 40), "titan"),
}


# --------------------------------------------------------------------------- helmets
def _helmet(base, style):
    def make():
        img = _canvas(64, 64)
        if style == "cap":
            _ball(img, (22, 21, 40, 43), base + (255,))
            _line(img, [(24, 32), (38, 32)], _shade(base, 0.6) + (230,), 1.2)    # stitched seam
            for y in (26, 38):
                _circle(img, 31, y, 0.9, (220, 200, 160, 255))
        else:   # iron helm with a nose guard and a crest
            _ball(img, (21, 20, 41, 44), base + (255,))
            _rrect(img, (38, 30, 45, 34), 1, _shade(base, 1.2) + (255,), _shade(base, 0.5) + (255,), 0.8)
            _line(img, [(23, 32), (39, 32)], _shade(base, 1.35) + (255,), 2)
            for y in (24, 40):
                _circle(img, 27, y, 1, (230, 232, 238, 255))
        return _finish(img, 64, 64)
    return make


HEAD = {
    "leather_cap": _helmet((140, 92, 50), "cap"),
    "iron_helmet": _helmet((160, 166, 178), "helm"),
}


# --------------------------------------------------------------------------- cloaks (drawn behind)
def _cloak(base, trim, glow=None):
    def make():
        img = _canvas(64, 64)
        if glow:
            g = _canvas(64, 64)
            _poly(g, [(30, 10), (30, 54), (4, 60), (0, 32), (4, 4)], glow + (120,))
            img.alpha_composite(g.filter(ImageFilter.GaussianBlur(4 * S)))
        pts = [(32, 11), (32, 53), (14, 58), (6, 54), (2, 32), (6, 10), (14, 6)]
        _poly(img, pts, base + (255,), _shade(base, 0.45) + (255,), 1.4)
        _poly(img, [(32, 14), (32, 50), (16, 52), (10, 32), (16, 12)], _shade(base, 1.15) + (200,))   # fold
        for k in range(6):            # ragged / furry hem along the back edge
            y = 9 + k * 9
            _line(img, [(5, y), (1, y + 3)], trim + (255,), 1.6)
        _circle(img, 31, 32, 2.4, trim + (255,))     # clasp
        return _finish(img, 64, 64)
    return make


CLOAK = {
    "fur_cloak": _cloak((132, 134, 142), (210, 212, 220)),
    "frost_cloak": _cloak((160, 205, 245), (240, 250, 255), glow=(120, 200, 255)),
}


def gear(item):
    """Texture for a worn item, or None if it has no look of its own."""
    for table in (BODY, HEAD, CLOAK):
        if item in table:
            return _tex(f"gear_{item}", table[item])
    return None
