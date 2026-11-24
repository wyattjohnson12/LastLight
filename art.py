"""
art.py - every graphic in the game, painted in code with Pillow.

Each texture is drawn at 3x size and scaled down, which gives soft, anti-aliased
"painted" edges. Want to swap in your own art (e.g. images from Higgsfield)?
Drop a PNG with the same name into the assets/ folder, e.g. assets/zombie_walker.png,
and it will be used instead of the generated one.
"""
import math
import os
import random

import arcade
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 3  # supersampling factor
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_cache = {}


# --------------------------------------------------------------------------- helpers
def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def _shade(c, f):
    """f < 1 darkens, f > 1 lightens."""
    if f < 1:
        return tuple(int(v * f) for v in c[:3]) + tuple(c[3:])
    return tuple(int(v + (255 - v) * (f - 1)) for v in c[:3]) + tuple(c[3:])


def _canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def _finish(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def _shadow(img, box, alpha=80, blur=4):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([v * S for v in box], fill=(10, 15, 10, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur * S))
    img.alpha_composite(layer)


def _ball(img, box, base, light=(-0.35, -0.4), steps=16, outline=True, soft=1.0):
    """A shaded ellipse lit from the top-left: the core of the painted look."""
    x0, y0, x1, y1 = [v * S for v in box]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    dark, lite = _shade(base, 0.55), _shade(base, 1.35)
    for i in range(steps):
        t = i / (steps - 1)
        col = _lerp(dark, base, t * 2) if t < 0.5 else _lerp(base, lite, (t - 0.5) * 2)
        k = 1 - t * 0.82
        ox, oy = cx + light[0] * rx * t, cy + light[1] * ry * t
        d.ellipse([ox - rx * k, oy - ry * k, ox + rx * k, oy + ry * k], fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(1.3 * S * soft))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([x0, y0, x1, y1], fill=255)
    clipped = Image.new("RGBA", img.size, (0, 0, 0, 0))
    clipped.paste(layer, (0, 0), mask)
    img.alpha_composite(clipped)
    if outline:
        ImageDraw.Draw(img).ellipse([x0, y0, x1, y1], outline=_shade(base[:3], 0.35) + (230,), width=int(1.4 * S))


def _poly(img, pts, fill, outline=None, width=1.4):
    d = ImageDraw.Draw(img)
    p = [(x * S, y * S) for x, y in pts]
    d.polygon(p, fill=fill)
    if outline:
        d.line(p + [p[0]], fill=outline, width=int(width * S), joint="curve")


def _line(img, pts, fill, width):
    ImageDraw.Draw(img).line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")


def _circle(img, x, y, r, fill, outline=None, width=1.2):
    ImageDraw.Draw(img).ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=fill,
                                outline=outline, width=int(width * S) if outline else 0)


def _rrect(img, box, r, fill, outline=None, width=1.4):
    ImageDraw.Draw(img).rounded_rectangle([v * S for v in box], r * S, fill=fill, outline=outline,
                                          width=int(width * S) if outline else 0)


def _tex(name, maker, hit_box=None):
    """Return a cached arcade Texture; prefer assets/<name>.png if the user supplied one."""
    if name in _cache:
        return _cache[name]
    path = os.path.join(ASSET_DIR, name + ".png")
    img = Image.open(path).convert("RGBA") if os.path.exists(path) else maker()
    kw = {"hash": "ll_" + name}
    if hit_box:
        kw["hit_box_points"] = hit_box
    t = arcade.Texture(img, **kw)
    _cache[name] = t
    return t


def save_all(folder):
    """Export every generated texture as PNG (handy as a template for custom art)."""
    os.makedirs(folder, exist_ok=True)
    for name, t in _cache.items():
        t.image.save(os.path.join(folder, name + ".png"))


# --------------------------------------------------------------------------- ground
def _grass_tile(seed):
    rnd = random.Random(seed)
    n = 256
    img = Image.new("RGBA", (n, n), (74, 116, 50, 255))
    blobs = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(blobs)
    palette = [(66, 106, 44), (84, 128, 56), (92, 134, 58), (70, 112, 48), (98, 128, 60)]
    for _ in range(140):
        r = rnd.randint(8, 34)
        x, y = rnd.randint(0, n), rnd.randint(0, n)
        col = rnd.choice(palette) + (rnd.randint(60, 140),)
        for ox in (-n, 0, n):            # draw wrapped so tiles repeat seamlessly
            for oy in (-n, 0, n):
                d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=col)
    blobs = blobs.filter(ImageFilter.GaussianBlur(9))
    img.alpha_composite(blobs)
    d = ImageDraw.Draw(img)
    for _ in range(420):  # grass strokes
        x, y = rnd.randint(2, n - 3), rnd.randint(4, n - 2)
        h = rnd.randint(3, 7)
        lean = rnd.randint(-2, 2)
        col = rnd.choice([(52, 88, 34), (112, 150, 66), (60, 98, 40), (124, 160, 74)]) + (rnd.randint(110, 200),)
        d.line([(x, y), (x + lean, y - h)], fill=col, width=1)
    for _ in range(rnd.randint(2, 6)):  # tiny flowers
        x, y = rnd.randint(6, n - 6), rnd.randint(6, n - 6)
        col = rnd.choice([(240, 230, 140), (240, 240, 245), (220, 150, 200), (250, 190, 90)])
        for a in range(5):
            ang = a * math.tau / 5
            d.ellipse([x + math.cos(ang) * 2 - 1.3, y + math.sin(ang) * 2 - 1.3,
                       x + math.cos(ang) * 2 + 1.3, y + math.sin(ang) * 2 + 1.3], fill=col)
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(250, 200, 60))
    return img


def grass(i):
    return _tex(f"ground_grass_{i}", lambda: _grass_tile(1000 + i))


def _tuft_img(seed):
    rnd = random.Random(seed)
    img = _canvas(28, 22)
    for _ in range(9):
        x = rnd.uniform(6, 22)
        h = rnd.uniform(8, 16)
        col = rnd.choice([(58, 96, 38), (96, 140, 60), (120, 156, 70)]) + (255,)
        _line(img, [(x, 20), (x + rnd.uniform(-4, 4), 20 - h)], col, 1.6)
    return _finish(img, 28, 22)


def tuft(i):
    return _tex(f"decor_tuft_{i}", lambda: _tuft_img(50 + i))


def _pebble_img(seed):
    rnd = random.Random(seed)
    img = _canvas(22, 16)
    for _ in range(3):
        x, y, r = rnd.uniform(5, 16), rnd.uniform(5, 11), rnd.uniform(2.5, 4.5)
        _ball(img, (x - r, y - r * 0.8, x + r, y + r * 0.8), (140, 138, 130, 255), outline=False)
    return _finish(img, 22, 16)


def pebbles(i):
    return _tex(f"decor_pebbles_{i}", lambda: _pebble_img(80 + i))


# --------------------------------------------------------------------------- nature
def _tree_img(seed, palette):
    rnd = random.Random(seed)
    w = h = 150
    img = _canvas(w, h)
    _shadow(img, (30, 40, 140, 140), alpha=95, blur=6)
    _ball(img, (65, 65, 85, 85), (96, 64, 38, 255))  # trunk peeking out
    clusters = []
    for _ in range(7):
        a = rnd.uniform(0, math.tau)
        dist = rnd.uniform(10, 30)
        clusters.append((75 + math.cos(a) * dist, 75 + math.sin(a) * dist, rnd.uniform(26, 36)))
    clusters.sort(key=lambda c: c[1])
    for cx, cy, r in clusters:
        _ball(img, (cx - r, cy - r, cx + r, cy + r), rnd.choice(palette) + (255,), soft=1.6)
    for _ in range(14):  # leafy highlights
        x, y = rnd.uniform(40, 100), rnd.uniform(35, 95)
        _circle(img, x, y, rnd.uniform(2, 4), _shade(palette[0], 1.5) + (110,))
    return _finish(img, w, h)


TREE_PALETTES = [
    [(58, 112, 52), (70, 128, 58), (50, 100, 46)],
    [(44, 94, 60), (56, 110, 70), (38, 84, 52)],
    [(104, 120, 44), (122, 132, 48), (88, 108, 40)],
]
TRUNK_HIT = [(-14, -14), (14, -14), (14, 14), (-14, 14)]


def tree(i):
    return _tex(f"tree_{i}", lambda: _tree_img(200 + i, TREE_PALETTES[i % 3]), TRUNK_HIT)


def _stump_img():
    img = _canvas(44, 44)
    _shadow(img, (8, 12, 42, 42), alpha=70)
    _ball(img, (8, 8, 36, 36), (120, 82, 50, 255))
    _circle(img, 22, 22, 9, (170, 128, 84, 255))
    ImageDraw.Draw(img).ellipse([16 * S, 16 * S, 28 * S, 28 * S], outline=(120, 84, 52, 255), width=S)
    return _finish(img, 44, 44)


def stump():
    return _tex("tree_stump", _stump_img, [(-12, -12), (12, -12), (12, 12), (-12, 12)])


def _rock_img(seed):
    rnd = random.Random(seed)
    w, h = 70, 62
    img = _canvas(w, h)
    _shadow(img, (8, 16, 68, 62), alpha=90, blur=4)
    pts = []
    n = 9
    for k in range(n):
        a = k / n * math.tau
        r = rnd.uniform(22, 29)
        pts.append((35 + math.cos(a) * r, 30 + math.sin(a) * r * 0.82))
    base = rnd.choice([(128, 126, 120), (118, 114, 108), (136, 130, 118)])
    _poly(img, pts, base + (255,), _shade(base, 0.4) + (255,), 1.6)
    # facets: light top-left, dark bottom-right
    top = [p for p in pts if p[1] < 30 or p[0] < 30]
    _poly(img, [(35, 26)] + top[:5], _shade(base, 1.25) + (150,))
    bot = [p for p in pts if p[1] > 32]
    if len(bot) >= 2:
        _poly(img, [(38, 32)] + bot, _shade(base, 0.72) + (170,))
    for _ in range(4):  # cracks
        x, y = rnd.uniform(22, 48), rnd.uniform(18, 40)
        _line(img, [(x, y), (x + rnd.uniform(-6, 6), y + rnd.uniform(3, 7))], _shade(base, 0.5) + (200,), 1)
    for _ in range(5):  # moss
        _circle(img, rnd.uniform(20, 46), rnd.uniform(10, 22), rnd.uniform(1.5, 3), (96, 130, 60, 200))
    return _finish(img, w, h)


ROCK_HIT = [(-24, -18), (24, -18), (26, 8), (0, 22), (-26, 8)]


def rock(i):
    return _tex(f"rock_{i}", lambda: _rock_img(300 + i), ROCK_HIT)


def _bush_img(berries):
    rnd = random.Random(7 if berries else 8)
    img = _canvas(60, 56)
    _shadow(img, (8, 16, 58, 56), alpha=80)
    for cx, cy, r in [(22, 30, 15), (38, 30, 15), (30, 20, 16), (30, 34, 14)]:
        _ball(img, (cx - r, cy - r, cx + r, cy + r), rnd.choice([(54, 110, 48), (62, 122, 54)]) + (255,), soft=1.4)
    if berries:
        for _ in range(11):
            x, y = rnd.uniform(16, 44), rnd.uniform(12, 42)
            _circle(img, x, y, 3.2, (196, 34, 64, 255), (110, 16, 36, 255), 0.8)
            _circle(img, x - 1, y - 1, 1, (255, 190, 200, 255))
    return _finish(img, 60, 56)


BUSH_HIT = [(-16, -14), (16, -14), (16, 12), (-16, 12)]


def bush(berries=True):
    return _tex("bush_berries" if berries else "bush_empty", lambda: _bush_img(berries), BUSH_HIT)


def _pond_img(seed):
    rnd = random.Random(seed)
    w, h = 220, 160
    img = _canvas(w, h)
    _ball(img, (4, 6, 216, 156), (176, 160, 112, 255), outline=False, soft=2)     # sandy shore
    layer = _canvas(w, h)
    _ball(layer, (16, 16, 204, 144), (52, 118, 170, 255), light=(0.2, 0.25), outline=False, soft=2.5)
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.ellipse([16 * S, 16 * S, 204 * S, 144 * S], outline=(36, 86, 120, 255), width=2 * S)
    for _ in range(7):  # ripples
        x, y = rnd.uniform(50, 170), rnd.uniform(40, 120)
        rw = rnd.uniform(10, 22)
        d.arc([(x - rw) * S, (y - rw * 0.4) * S, (x + rw) * S, (y + rw * 0.4) * S], 200, 340,
              fill=(170, 214, 236, 170), width=int(1.2 * S))
    for _ in range(3):  # lily pads
        x, y = rnd.uniform(40, 180), rnd.uniform(36, 124)
        d.pieslice([(x - 8) * S, (y - 8) * S, (x + 8) * S, (y + 8) * S], 30, 340, fill=(74, 140, 66, 255))
        if rnd.random() < 0.6:
            _circle(img, x + 2, y - 2, 2.4, (240, 170, 200, 255))
    return _finish(img, w, h)


POND_HIT = [(-92, 0), (-70, -46), (0, -60), (70, -46), (92, 0), (70, 46), (0, 60), (-70, 46)]


def pond(i):
    return _tex(f"pond_{i}", lambda: _pond_img(400 + i), POND_HIT)


# --------------------------------------------------------------------------- characters (face +x / right)
JACKETS = [(58, 104, 112), (150, 62, 58), (96, 120, 58), (176, 138, 52)]   # teal, red, green, gold
HAIR = [(84, 54, 34), (40, 32, 28), (150, 96, 50), (60, 40, 30)]


def _survivor_img(i=0):
    jacket, hair = JACKETS[i % 4], HAIR[i % 4]
    img = _canvas(64, 64)
    _shadow(img, (12, 16, 56, 58), alpha=80, blur=3)
    _rrect(img, (10, 20, 24, 44), 5, (122, 86, 52, 255), (64, 44, 26, 255))          # backpack
    _line(img, [(20, 22), (28, 26)], (70, 50, 30, 255), 2)
    _line(img, [(20, 42), (28, 38)], (70, 50, 30, 255), 2)
    _ball(img, (16, 14, 44, 50), jacket + (255,))                                    # jacket/shoulders
    _ball(img, (38, 12, 50, 24), (226, 182, 146, 255))                                   # hands
    _ball(img, (38, 40, 50, 52), (226, 182, 146, 255))
    _ball(img, (24, 22, 44, 42), (226, 182, 146, 255))                                   # head
    ImageDraw.Draw(img).chord([23 * S, 21 * S, 43 * S, 43 * S], 90, 270, fill=hair + (255,))  # hair (back)
    _circle(img, 41, 28, 1.3, (40, 30, 30, 255))                                          # eyes
    _circle(img, 41, 36, 1.3, (40, 30, 30, 255))
    return _finish(img, 64, 64)


PLAYER_HIT = [(-12, -12), (12, -12), (12, 12), (-12, 12)]


def player(i=0):
    """Survivor sprite. i = 0..3 picks the jacket colour for each co-op player."""
    name = "player" if i % 4 == 0 else f"player{i % 4 + 1}"
    return _tex(name, lambda: _survivor_img(i), PLAYER_HIT)


def _zombie_img(skin, shirt, size, bulk):
    img = _canvas(size, size)
    c = size / 2
    _shadow(img, (c - 20 * bulk, c - 16 * bulk, c + 24 * bulk, c + 26 * bulk), alpha=80, blur=3)
    # outstretched arms
    for side in (-1, 1):
        y = c + side * 12 * bulk
        _line(img, [(c - 2, y), (c + 22 * bulk, y + side * 1.5)], _shade(shirt, 0.5) + (255,), 9 * bulk)
        _line(img, [(c - 2, y), (c + 22 * bulk, y + side * 1.5)], shirt + (255,), 7 * bulk)
        _ball(img, (c + 18 * bulk, y - 5 * bulk, c + 28 * bulk, y + 5 * bulk), skin + (255,))
    _ball(img, (c - 14 * bulk, c - 18 * bulk, c + 12 * bulk, c + 18 * bulk), shirt + (255,))   # torso
    rnd = random.Random(size)
    for _ in range(4):  # torn holes / stains
        _circle(img, c + rnd.uniform(-8, 6) * bulk, c + rnd.uniform(-12, 12) * bulk,
                rnd.uniform(1.5, 3) * bulk, (80, 24, 24, 200))
    _ball(img, (c - 8 * bulk, c - 10 * bulk, c + 10 * bulk, c + 10 * bulk), skin + (255,))     # head
    _circle(img, c - 2 * bulk, c - 3 * bulk, 3 * bulk, _shade(skin, 0.7) + (180,))            # rot patch
    for side in (-1, 1):  # glowing eyes
        _circle(img, c + 6 * bulk, c + side * 4 * bulk, 1.8 * bulk, (255, 70, 50, 255))
        _circle(img, c + 6 * bulk, c + side * 4 * bulk, 0.8 * bulk, (255, 220, 160, 255))
    return _finish(img, size, size)


ZOMBIE_LOOK = {
    "walker": ((120, 156, 104), (96, 78, 64), 64, 1.0),
    "runner": ((176, 184, 150), (60, 76, 110), 60, 0.88),
    "brute": ((128, 120, 150), (70, 50, 46), 92, 1.45),
}


def zombie(kind):
    skin, shirt, size, bulk = ZOMBIE_LOOK[kind]
    hb = 12 * bulk
    return _tex(f"zombie_{kind}", lambda: _zombie_img(skin, shirt, size, bulk),
                [(-hb, -hb), (hb, -hb), (hb, hb), (-hb, hb)])


# --------------------------------------------------------------------------- structures
def _wood_wall_img():
    img = _canvas(40, 40)
    _shadow(img, (2, 6, 40, 42), alpha=70, blur=2)
    for k in range(4):
        y0 = 2 + k * 9
        col = [(150, 104, 62), (138, 94, 56), (160, 112, 66), (144, 98, 58)][k]
        _rrect(img, (2, y0, 38, y0 + 8.5), 2, col + (255,), (84, 56, 32, 255), 1)
        _line(img, [(6, y0 + 3), (20, y0 + 4)], _shade(col, 0.78) + (200,), 0.8)
        _line(img, [(24, y0 + 5), (34, y0 + 4)], _shade(col, 0.78) + (200,), 0.8)
    for x in (8, 32):
        for k in range(4):
            _circle(img, x, 6 + k * 9, 1, (60, 60, 64, 255))
    return _finish(img, 40, 40)


def _stone_wall_img():
    rnd = random.Random(5)
    img = _canvas(40, 40)
    _shadow(img, (2, 6, 40, 42), alpha=80, blur=2)
    _rrect(img, (1, 1, 39, 39), 3, (90, 88, 84, 255))
    for row in range(4):
        off = 0 if row % 2 == 0 else -6
        x = off
        while x < 40:
            w = rnd.uniform(10, 14)
            col = rnd.choice([(146, 142, 134), (128, 126, 120), (156, 150, 140)])
            bl, br = max(2, x + 1), min(38, x + w)
            if br - bl > 3:
                _rrect(img, (bl, 2 + row * 9.2, br, 10 + row * 9.2), 2,
                       col + (255,), _shade(col, 0.55) + (255,), 0.8)
            x += w + 1
    return _finish(img, 40, 40)


BLOCK_HIT = [(-19, -19), (19, -19), (19, 19), (-19, 19)]  # 1px inset so walls can touch


def wood_wall():
    return _tex("build_wood_wall", _wood_wall_img, BLOCK_HIT)


def stone_wall():
    return _tex("build_stone_wall", _stone_wall_img, BLOCK_HIT)


def _spikes_img():
    img = _canvas(40, 40)
    _rrect(img, (3, 3, 37, 37), 4, (110, 78, 46, 230), (66, 44, 24, 255), 1)
    for gx in range(3):
        for gy in range(3):
            x, y = 10 + gx * 10, 10 + gy * 10
            _poly(img, [(x - 4, y + 4), (x + 4, y + 4), (x, y - 5)], (196, 196, 204, 255), (80, 80, 90, 255), 0.8)
    return _finish(img, 40, 40)


def spikes():
    return _tex("build_spike_trap", _spikes_img)


def _campfire_img():
    img = _canvas(52, 52)
    _shadow(img, (6, 10, 50, 52), alpha=70)
    for k in range(8):
        a = k / 8 * math.tau
        x, y = 26 + math.cos(a) * 17, 26 + math.sin(a) * 17
        _ball(img, (x - 5, y - 4.5, x + 5, y + 4.5), (130, 126, 120, 255))
    _line(img, [(14, 18), (38, 34)], (96, 62, 36, 255), 6)
    _line(img, [(14, 34), (38, 18)], (110, 72, 42, 255), 6)
    _circle(img, 26, 26, 7, (60, 30, 20, 255))
    return _finish(img, 52, 52)


def campfire():
    return _tex("build_campfire", _campfire_img, [(-18, -18), (18, -18), (18, 18), (-18, 18)])


def _flame_img(seed):
    rnd = random.Random(seed)
    img = _canvas(40, 48)
    glow = _canvas(40, 48)
    _circle(glow, 20, 28, 15, (255, 140, 40, 120))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(4 * S)))
    for col, sc in [((240, 90, 30), 1.0), ((255, 160, 40), 0.72), ((255, 236, 150), 0.42)]:
        tip = 6 + rnd.uniform(-3, 3)
        sway = rnd.uniform(-3, 3)
        pts = [(20 - 11 * sc, 36), (20 - 7 * sc + sway / 2, 26), (20 + sway, 36 - 30 * sc + tip * (1 - sc)),
               (20 + 7 * sc + sway / 2, 26), (20 + 11 * sc, 36), (20, 40)]
        _poly(img, pts, col + (240,))
    return _finish(img.filter(ImageFilter.GaussianBlur(0.6 * S)), 40, 48)


def flame(i):
    return _tex(f"fx_flame_{i}", lambda: _flame_img(600 + i))


def _hut_img():
    rnd = random.Random(11)
    w = h = 128
    img = _canvas(w, h)
    _shadow(img, (8, 14, 128, 128), alpha=100, blur=5)
    # thatched roof: two halves split by a ridge
    _poly(img, [(6, 6), (122, 6), (122, 64), (6, 64)], (170, 136, 74, 255))
    _poly(img, [(6, 64), (122, 64), (122, 122), (6, 122)], (138, 108, 56, 255))
    for _ in range(320):
        x = rnd.uniform(8, 120)
        y = rnd.uniform(8, 120)
        top = y < 64
        col = rnd.choice([(196, 160, 92), (150, 118, 62), (182, 146, 82)]) if top else \
            rnd.choice([(150, 116, 60), (120, 92, 46), (136, 104, 54)])
        _line(img, [(x, y), (x + rnd.uniform(-1.5, 1.5), y + (7 if top else -7))], col + (200,), 1)
    _rrect(img, (2, 58, 126, 70), 4, (104, 74, 40, 255), (64, 44, 22, 255), 1.2)          # ridge beam
    ImageDraw.Draw(img).rectangle([6 * S, 6 * S, 122 * S, 122 * S], outline=(84, 60, 30, 255), width=2 * S)
    _rrect(img, (88, 18, 104, 34), 2, (120, 116, 110, 255), (60, 58, 56, 255), 1)          # chimney
    _circle(img, 96, 26, 4, (40, 36, 34, 255))
    return _finish(img, w, h)


def hut():
    return _tex("build_hut", _hut_img, [(-60, -60), (60, -60), (60, 60), (-60, 60)])


# --------------------------------------------------------------------------- item icons (tools point right)
def _icon(draw_fn, size=48):
    img = _canvas(size, size)
    draw_fn(img)
    return _finish(img, size, size)


def _wood_icon(img):
    for dy, col in [(8, (120, 82, 46)), (-4, (140, 96, 54))]:
        _rrect(img, (6, 18 + dy, 40, 30 + dy), 6, col + (255,), (70, 46, 24, 255))
        _ball(img, (34, 18 + dy, 44, 30 + dy), (196, 154, 100, 255))
        _circle(img, 39, 24 + dy, 2.2, (150, 108, 64, 255))


def _stone_icon(img):
    _ball(img, (8, 16, 30, 38), (130, 128, 122, 255))
    _ball(img, (20, 10, 42, 34), (150, 146, 138, 255))


def _berries_icon(img):
    _poly(img, [(20, 8), (34, 6), (28, 14)], (70, 140, 60, 255))
    for x, y in [(16, 22), (28, 20), (22, 32), (34, 31), (12, 33)]:
        _circle(img, x, y, 7, (196, 34, 64, 255), (110, 16, 36, 255), 1)
        _circle(img, x - 2, y - 2, 2, (255, 190, 200, 255))


def _fiber_icon(img):
    for k in range(6):
        x = 14 + k * 4
        _line(img, [(x, 42), (x + (k - 3) * 2.5, 8)], [(96, 150, 60), (120, 170, 70)][k % 2] + (255,), 2.2)
    _rrect(img, (12, 26, 38, 31), 2, (170, 130, 80, 255))


def _water_icon(img):
    _rrect(img, (19, 4, 29, 12), 2, (120, 84, 50, 255))
    _ball(img, (10, 10, 38, 44), (80, 160, 220, 255))
    _circle(img, 19, 22, 3, (220, 240, 255, 200))


def _club_icon(img):
    _line(img, [(4, 26), (28, 24)], (110, 74, 42, 255), 5)
    _ball(img, (24, 14, 46, 34), (136, 92, 52, 255))
    for x, y in [(30, 16), (40, 20), (34, 32)]:
        _circle(img, x, y, 1.6, (90, 90, 96, 255))


def _axe_icon(img):
    _line(img, [(4, 26), (40, 24)], (118, 80, 46, 255), 4)
    _poly(img, [(30, 22), (44, 10), (46, 26), (36, 28)], (150, 148, 142, 255), (70, 70, 72, 255))
    _line(img, [(28, 21), (34, 27)], (180, 160, 110, 255), 2)


def _pick_icon(img):
    _line(img, [(4, 26), (38, 24)], (118, 80, 46, 255), 4)
    pts = [(30, 6), (40, 16), (46, 30), (40, 42), (34, 26)]
    _poly(img, pts, (150, 148, 142, 255), (70, 70, 72, 255))


def _spear_icon(img):
    _line(img, [(2, 26), (36, 24)], (126, 88, 50, 255), 3)
    _poly(img, [(34, 18), (47, 24), (34, 30), (37, 24)], (156, 154, 150, 255), (70, 70, 72, 255))
    _line(img, [(30, 21), (33, 28)], (200, 180, 120, 255), 2)


def _bandage_icon(img):
    _rrect(img, (8, 16, 40, 32), 6, (236, 230, 214, 255), (150, 140, 120, 255))
    _rrect(img, (20, 16, 28, 32), 1, (200, 60, 60, 255))


def _stew_icon(img):
    _ball(img, (6, 18, 42, 42), (120, 78, 44, 255))
    _ball(img, (10, 18, 38, 30), (196, 104, 60, 255), outline=False)
    for x in (16, 24, 32):
        _line(img, [(x, 14), (x + 2, 8)], (230, 230, 230, 140), 1.5)


def _heart_icon(img):
    _circle(img, 17, 18, 9, (220, 60, 70, 255))
    _circle(img, 31, 18, 9, (220, 60, 70, 255))
    _poly(img, [(9, 21), (39, 21), (24, 40)], (220, 60, 70, 255))
    _circle(img, 15, 15, 3, (255, 180, 180, 255))


def _drop_icon(img):
    _poly(img, [(24, 6), (36, 26), (12, 26)], (80, 160, 230, 255))
    _circle(img, 24, 30, 12, (80, 160, 230, 255))
    _circle(img, 20, 28, 3, (220, 240, 255, 230))


def _bolt_icon(img):
    _poly(img, [(28, 4), (12, 26), (22, 26), (18, 44), (36, 20), (26, 20)], (250, 210, 70, 255), (160, 110, 20, 255))


def _sun_icon(img):
    for k in range(8):
        a = k / 8 * math.tau
        _line(img, [(24 + math.cos(a) * 12, 24 + math.sin(a) * 12), (24 + math.cos(a) * 20, 24 + math.sin(a) * 20)],
              (250, 200, 80, 255), 3)
    _ball(img, (13, 13, 35, 35), (250, 200, 70, 255))


def _moon_icon(img):
    _circle(img, 24, 24, 15, (220, 226, 250, 255))
    _circle(img, 32, 18, 13, (0, 0, 0, 0))
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([18 * S, 5 * S, 44 * S, 31 * S], fill=255)
    img.putalpha(ImageChops.subtract(img.getchannel("A"), m))


ICON_MAKERS = {
    "wood": _wood_icon, "stone": _stone_icon, "berries": _berries_icon, "fiber": _fiber_icon,
    "water": _water_icon, "club": _club_icon, "axe": _axe_icon, "pickaxe": _pick_icon,
    "spear": _spear_icon, "bandage": _bandage_icon, "stew": _stew_icon,
    "heart": _heart_icon, "drop": _drop_icon, "bolt": _bolt_icon, "sun": _sun_icon, "moon": _moon_icon,
}
STRUCTURE_ICONS = {"wood_wall": wood_wall, "stone_wall": stone_wall, "spike_trap": spikes,
                   "campfire": campfire, "hut": hut}


def icon(name):
    if name in STRUCTURE_ICONS:
        return STRUCTURE_ICONS[name]()
    return _tex(f"icon_{name}", lambda: _icon(ICON_MAKERS[name]))


def held(name):
    """Tool icon as held in the hand (same art, used for the swing animation)."""
    return icon(name)


# --------------------------------------------------------------------------- lighting
def _radial(size):
    """0 in the centre rising to 255 exactly at the circle's edge (and beyond)."""
    # Pillow's radial_gradient only reaches ~181 at the square's edge midpoint, so rescale it.
    g = Image.radial_gradient("L").point(lambda v: min(255, int(v * 255 / 181)))
    return g.resize((size, size), Image.BICUBIC)


def _darkness_img(w, h, radius):
    """Big dark sheet with a soft see-through circle in the middle (the player's light)."""
    mask = Image.new("L", (w, h), 255)
    grad = _radial(radius * 2)
    grad = grad.point(lambda v: 0 if v < 110 else min(255, int((v - 110) * 255 / 145)))
    box = (w // 2 - radius, h // 2 - radius)
    hole = Image.new("L", (w, h), 255)
    hole.paste(grad, box)
    mask = ImageChops.darker(mask, hole)
    img = Image.new("RGBA", (w, h), (8, 10, 30, 255))
    img.putalpha(mask)
    return img


def darkness(w, h, radius=230):
    return _tex(f"fx_darkness_{w}x{h}_{radius}", lambda: _darkness_img(w, h, radius))


def _glow_img(r, col):
    g = _radial(r * 2)
    a = g.point(lambda v: int(((255 - v) / 255) ** 1.6 * 255))
    img = Image.new("RGBA", (r * 2, r * 2), col + (255,))
    img.putalpha(a.point(lambda v: int(v * 0.85)))
    return img


def glow(r=170, col=(255, 150, 60)):
    return _tex(f"fx_glow_{r}_{col}", lambda: _glow_img(r, col))
