"""
art_bees.py - painted-in-code art for bees: the bee itself, beehives hanging in trees,
and the honey icon. Same style (and same assets/ override) as art.py.
Importing this module registers the bee with art_extra.animal() and honey with art.icon().
"""
import random

import art
import art_extra
from art import _ball, _canvas, _circle, _finish, _line, _poly, _shadow, _tex

HONEY = (236, 170, 40)


# --------------------------------------------------------------------------- the bee (faces right)
def _bee_img():
    img = _canvas(30, 30)
    _shadow(img, (8, 12, 24, 26), alpha=50, blur=2)
    for side in (-1, 1):   # see-through wings
        _ball(img, (9, 15 + side * 7 - 4, 17, 15 + side * 7 + 4), (225, 240, 255, 150), outline=False)
    _ball(img, (6, 10, 22, 20), HONEY + (255,))
    for x in (10, 15):     # stripes
        _line(img, [(x, 10.6), (x, 19.4)], (40, 30, 20, 255), 2.2)
    _ball(img, (19, 11, 26, 19), (50, 40, 30, 255))
    _circle(img, 24, 13.5, 0.9, (255, 255, 255, 255))
    _circle(img, 24, 16.5, 0.9, (255, 255, 255, 255))
    _poly(img, [(6, 14), (2.5, 15), (6, 16)], (40, 30, 20, 255))   # stinger
    return _finish(img, 30, 30)


art_extra.ANIMAL_ART["bee"] = (_bee_img, 7)


# --------------------------------------------------------------------------- beehive hanging in a tree
def _hive_img(full):
    rnd = random.Random(31)
    img = _canvas(40, 46)
    _shadow(img, (6, 12, 36, 44), alpha=70, blur=2)
    _line(img, [(20, 2), (20, 9)], (96, 66, 36, 255), 2.4)   # the branch it hangs from
    body = (206, 160, 76) if full else (150, 124, 84)
    for i, (y0, y1, w) in enumerate([(8, 20, 10), (16, 30, 14), (25, 38, 13), (33, 43, 8)]):
        _ball(img, (20 - w, y0, 20 + w, y1), body + (255,), soft=1.2)
    _ball(img, (16, 30, 24, 37), (60, 40, 20, 255), outline=False)   # entrance hole
    if full:
        for _ in range(3):   # honey dripping out
            x = rnd.uniform(12, 28)
            _line(img, [(x, 30), (x, 36 + rnd.uniform(0, 5))], HONEY + (230,), 1.8)
            _circle(img, x, 40, 1.6, HONEY + (255,))
    return _finish(img, 40, 46)


HIVE_HIT = [(-12, -14), (12, -14), (12, 14), (-12, 14)]


def hive(full=True):
    return _tex("hive_full" if full else "hive_empty", lambda: _hive_img(full), HIVE_HIT)


# --------------------------------------------------------------------------- honey icon
def _honey_icon(img):
    _ball(img, (10, 14, 38, 44), (210, 150, 40, 255))
    _ball(img, (13, 18, 35, 42), (246, 190, 60, 230), outline=False)
    _ball(img, (14, 8, 34, 16), (150, 110, 70, 255))          # lid
    _line(img, [(17, 22), (17, 34)], (255, 236, 170, 200), 2)  # shine


art.ICON_MAKERS["honey"] = _honey_icon


def all_textures():
    """Used by --export-art."""
    art_extra.animal("bee")
    hive(True)
    hive(False)
    art.icon("honey")
