"""Opening cutscene: how the survivor arrives in the world.

Self-contained so it doesn't touch the rest of the game. main.py creates an
Intro when a new game starts, calls update(dt) each frame while
state == "intro", and draw(app) from on_draw. When `done` turns True the game
switches to "playing".

Modes:
  "solo" - the world is paused while it plays.
  "host" - co-op host: plays as an overlay while the world keeps running.
  "join" - someone joining a co-op game: a later drop, the others are already down there.
"""
import math
import random

import arcade

from settings import SCREEN_HEIGHT as H, SCREEN_WIDTH as W

SUBJECT = 41  # the first subject of this cycle. Tally marks in the pod = everyone who came before you

# (start, end) of each shot, in seconds
RADIO = (0.0, 10.5)
DROP = (10.5, 23.0)
IMPACT = (23.0, 26.0)
DOORS = (26.0, 33.5)
NOTE = (33.5, 45.5)
TITLE = (45.5, 52.0)
LENGTH = TITLE[1]

def story(mode, n):
    """Radio lines, inner monologue, and title-card lines for each kind of arrival."""
    head = (0.8, "[ CHANNEL 7 -- CYCLE 41 ]")
    if mode == "join":
        radio = [head,
                 (2.2, f"> Subject {n} is stable."),
                 (4.0, "> Memory wipe complete. Nothing left but the name."),
                 (6.2, "> The others are already down there."),
                 (7.6, "> Then don't keep them waiting. Drop it.")]
        thoughts = ["You wake up moving.",
                    "Somewhere below, someone else woke up like this too.",
                    f"You remember one thing.  Your name:  {{name}}."]
        title = (f"Subject {n} released.   You are not alone.", "> ...let's see if they last longer together.")
    elif mode == "host":
        radio = [head,
                 (2.2, f"> Subject {n} is stable."),
                 (4.0, "> Memory wipe complete. Nothing left but the name."),
                 (6.2, "> Just the one?"),
                 (7.6, "> For now. The others go down after. Drop it.")]
        thoughts = ["You wake up moving.",
                    "You don't know where you are. You don't know how you got here.",
                    f"You remember one thing.  Your name:  {{name}}."]
        title = (f"Subject {n} released.   Day 1.", "> ...and the others go down after.")
    else:
        radio = [head,
                 (2.2, f"> Subject {n} is stable."),
                 (4.0, "> Memory wipe complete. Nothing left but the name."),
                 (6.2, "> Same as the others?"),
                 (7.6, "> Same as all of them. Drop it.")]
        thoughts = ["You wake up moving.",
                    "You don't know where you are. You don't know how you got here.",
                    f"You remember one thing.  Your name:  {{name}}."]
        title = (f"Subject {n} released.   Day 1.", "> ...let's see how long this one lasts.")
    return radio, thoughts, title

NOTE_LINES = [
    "YOU'RE NOT THE FIRST.",
    "THEY TAKE YOUR MEMORY, NOT YOUR WILL.",
    "",
    "GATHER WHAT YOU CAN WHILE IT'S LIGHT.",
    "BUILD BEFORE DARK. KEEP A FIRE BURNING.",
    "WHATEVER COMES AT NIGHT HATES THE FLAME.",
    "",
    "DON'T WASTE TIME LOOKING FOR A WAY OUT.",
    "                                     - R",
]


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def window(t, span, fade_in=0.8, fade_out=0.8):
    """1 while t is inside span, fading in and out at the edges."""
    a, b = span
    return clamp((t - a) / fade_in) * clamp((b - t) / fade_out)


def glow(x, y, r, rgb, alpha, steps=40):
    """Soft radial glow: stacked translucent circles, brightest in the middle."""
    for i in range(steps):
        k = 1 - i / steps
        arcade.draw_circle_filled(x, y, r * k, rgb + (int(alpha / steps * 1.6),))


def typed(text, t, start, cps=34):
    n = int((t - start) * cps)
    return text[:max(0, min(len(text), n))]


class Intro:
    def __init__(self, name, mode="solo", subject=SUBJECT):
        self.name = name
        self.mode = mode
        self.subject = subject
        self.radio, thoughts, self.title_lines = story(mode, subject)
        self.thoughts = [line.format(name=name) for line in thoughts]
        self.t = 0.0
        self.done = False
        self.played = set()
        rnd = random.Random(SUBJECT)
        self.trees = [(rnd.uniform(-40, W + 40), rnd.uniform(0.55, 1.15), rnd.uniform(0.6, 1.0))
                      for _ in range(22)]
        self.dust = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(8, 30)) for _ in range(60)]
        self.static = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(20, 160)) for _ in range(40)]

    # ------------------------------------------------------------------ control
    def skip(self):
        if self.t > 0.6:
            self.done = True

    def update(self, dt, app):
        self.t += dt
        cues = [(DROP[0] + 0.3, "travel", 0.25), (IMPACT[0], "boom", 0.6), (IMPACT[0] + 0.15, "hurt", 0.3),
                (DOORS[0] + 0.6, "place", 0.3), (TITLE[0] + 0.5, "roar", 0.18)]
        for at, snd, vol in cues:
            if self.t >= at and at not in self.played:
                self.played.add(at)
                try:
                    app.play(snd, vol)
                except Exception:
                    pass
        if self.t >= LENGTH:
            self.done = True

    # ------------------------------------------------------------------ drawing
    def draw(self, app):
        t = self.t
        arcade.draw_lrbt_rectangle_filled(0, W, 0, H, (0, 0, 0))
        if t < RADIO[1]:
            self.draw_radio(app, t)
        if DROP[0] <= t < IMPACT[1]:
            self.draw_drop(app, t)
        if DOORS[0] <= t < DOORS[1] + 0.8:
            self.draw_doors(app, t)
        if NOTE[0] - 0.8 <= t < NOTE[1]:
            self.draw_note(app, t)
        if t >= TITLE[0]:
            self.draw_title(app, t)
        self.draw_bars()
        if t > 0.6:
            a = int(110 + 50 * math.sin(t * 3))
            app.txt("intro_skip", "SPACE / A  to skip", W - 24, 22, (200, 200, 200, a), 11, anchor_x="right")

    def draw_bars(self):
        bar = 56
        arcade.draw_lrbt_rectangle_filled(0, W, 0, bar, (0, 0, 0))
        arcade.draw_lrbt_rectangle_filled(0, W, H - bar, H, (0, 0, 0))

    def draw_radio(self, app, t):
        k = window(t, RADIO, 0.4, 1.0)
        for x, y, w in self.static:
            if random.random() < 0.35:
                yy = (y + t * 300) % H
                arcade.draw_lrbt_rectangle_filled(x, x + w, yy, yy + 1, (120, 160, 130, int(40 * k)))
        y = H / 2 + 70
        for i, (start, line) in enumerate(self.radio):
            if t < start:
                break
            col = (150, 210, 160, int(255 * k)) if i else (90, 130, 100, int(220 * k))
            app.txt(f"intro_r{i}", typed(line, t, start), W / 2 - 300, y - i * 34, col, 15 if i else 12)
        if int(t * 2) % 2 == 0 and k > 0.5:
            arcade.draw_circle_filled(W / 2 - 316, y + 6, 4, (220, 60, 50, int(220 * k)))

    def draw_drop(self, app, t):
        k = window(t, (DROP[0], IMPACT[0] + 0.2), 1.2, 0.1)
        if k <= 0:
            return
        p = (t - DROP[0]) / (DROP[1] - DROP[0])
        speed = 260 + 900 * smooth(p)
        shake = 2 + 6 * p
        ox = random.uniform(-shake, shake)
        oy = random.uniform(-shake, shake)
        cx, cy = W / 2 + ox, H / 2 + oy
        # shaft walls rushing upward past the pod
        for i in range(26):
            y = (i * 46 + t * speed) % (H + 60) - 30
            a = int(90 * k)
            arcade.draw_line(0, y, cx - 190, y, (70, 74, 80, a), 2)
            arcade.draw_line(cx + 190, y, W, y, (70, 74, 80, a), 2)
        for x0 in (cx - 230, cx + 230):
            arcade.draw_line(x0, 0, x0, H, (40, 42, 48, int(200 * k)), 6)
        # pulsing warning light
        pulse = 0.5 + 0.5 * math.sin(t * 7)
        glow(cx, cy + 210, 260, (200, 30, 15), 90 * pulse * k)
        # the pod
        l, r, b, tp = cx - 150, cx + 150, cy - 170, cy + 170
        arcade.draw_lrbt_rectangle_filled(l, r, b, tp, (38, 40, 44, int(255 * k)))
        arcade.draw_lrbt_rectangle_outline(l, r, b, tp, (95, 98, 104, int(255 * k)), 4)
        arcade.draw_line(cx, b + 8, cx, tp - 8, (20, 20, 22, int(255 * k)), 3)
        for sx in (l + 12, r - 12):
            for sy in range(int(b) + 20, int(tp) - 10, 40):
                arcade.draw_circle_filled(sx, sy, 3, (110, 112, 118, int(255 * k)))
        arcade.draw_lrbt_rectangle_filled(cx - 60, cx + 60, tp - 52, tp - 22, (12, 12, 14, int(255 * k)))
        arcade.draw_circle_filled(cx, tp + 14, 10, (255, 60, 40, int((120 + 135 * pulse) * k)))
        remaining = max(0, int((IMPACT[0] - t) * 60))
        app.txt("intro_depth", f"DESCENT  {remaining:04d}", cx, tp - 44, (255, 90, 70, int(255 * k)), 13,
                anchor_x="center", bold=True)
        app.txt("intro_pod", f"S-{self.subject:02d}", cx, b + 26, (150, 150, 150, int(200 * k)), 20,
                anchor_x="center", bold=True)
        # inner monologue
        lines = list(zip((DROP[0] + 1.5, DROP[0] + 4.5, DROP[0] + 8.0), self.thoughts))
        for i, (start, line) in enumerate(lines):
            if t >= start:
                a = int(255 * clamp((t - start) / 0.6) * k)
                app.txt(f"intro_d{i}", line, W / 2, 140 - i * 30, (225, 225, 225, a), 15, anchor_x="center")
        # impact flash
        if t >= IMPACT[0]:
            f = 1 - clamp((t - IMPACT[0]) / 1.6)
            arcade.draw_lrbt_rectangle_filled(0, W, 0, H, (255, 250, 235, int(255 * f)))
            if t > IMPACT[0] + 1.6:
                arcade.draw_lrbt_rectangle_filled(0, W, 0, H, (0, 0, 0))

    def draw_doors(self, app, t):
        k = window(t, (DOORS[0], DOORS[1] + 0.8), 0.6, 0.8)
        open_k = smooth((t - DOORS[0] - 0.8) / 3.2)
        # the world outside: dawn sky over dark trees
        for i in range(12):
            y0 = i * H / 12
            c = 1 - i / 12
            arcade.draw_lrbt_rectangle_filled(0, W, y0, y0 + H / 12 + 1,
                                              (int(60 + 180 * c), int(70 + 130 * c), int(60 + 60 * c), int(255 * k)))
        glow(W / 2, H * 0.42, 420, (255, 236, 180), 230 * k)
        for x, s, shade in self.trees:
            h = 260 * s
            col = (int(20 * shade), int(36 * shade), int(22 * shade), int(255 * k))
            arcade.draw_triangle_filled(x - 60 * s, 80, x + 60 * s, 80, x, 80 + h, col)
            arcade.draw_triangle_filled(x - 45 * s, 80 + h * 0.35, x + 45 * s, 80 + h * 0.35, x, 100 + h, col)
        arcade.draw_lrbt_rectangle_filled(0, W, 0, 86, (18, 26, 16, int(255 * k)))
        for x, y, sp in self.dust:
            yy = (y + t * sp) % H
            arcade.draw_circle_filled(x, yy, 1.5, (255, 240, 200, int(90 * k * open_k)))
        # pod doors sliding apart
        gap = open_k * W / 2
        dc = (34, 36, 40, int(255 * k))
        if open_k < 1:
            arcade.draw_lrbt_rectangle_filled(0, W / 2 - gap, 0, H, dc)
            arcade.draw_lrbt_rectangle_filled(W / 2 + gap, W, 0, H, dc)
            arcade.draw_line(W / 2 - gap, 0, W / 2 - gap, H, (255, 240, 200, int(255 * k)), 3)
            arcade.draw_line(W / 2 + gap, 0, W / 2 + gap, H, (255, 240, 200, int(255 * k)), 3)
        if t > DOORS[0] + 3.6:
            a = int(255 * clamp((t - DOORS[0] - 3.6) / 0.8) * k)
            app.txt("intro_o1", "Trees. Sky. Silence.", W / 2, 130, (250, 250, 240, a), 16, anchor_x="center")
        if t > DOORS[0] + 5.2:
            a = int(255 * clamp((t - DOORS[0] - 5.2) / 0.8) * k)
            app.txt("intro_o2", "And scratched into the inside of the door...", W / 2, 100, (210, 210, 200, a), 13,
                    anchor_x="center")

    def draw_note(self, app, t):
        k = window(t, (NOTE[0] - 0.8, NOTE[1]), 0.8, 1.0)
        a = int(255 * k)
        arcade.draw_lrbt_rectangle_filled(0, W, 0, H, (30, 32, 36, a))
        # brushed-metal streaks
        for i in range(0, int(H), 7):
            arcade.draw_line(0, i, W, i, (40, 42, 47, a), 1)
        # tally marks: everyone who came before
        tallies = self.subject - 1
        shown = int(tallies * clamp((t - NOTE[0]) / 2.5))
        x0, y0 = W / 2 - 300, H - 150
        for i in range(shown):
            grp, j = divmod(i, 5)
            gx = x0 + (grp % 10) * 62    # 10 groups per row: room for every co-op subject
            gy = y0 - (grp // 10) * 56
            if j < 4:
                x = gx + j * 12
                arcade.draw_line(x, gy, x + 3, gy + 44, (175, 170, 160, a), 2)
            else:
                arcade.draw_line(gx - 6, gy + 8, gx + 46, gy + 36, (175, 170, 160, a), 2)
        # the message, scratched in one line at a time
        start = NOTE[0] + 2.4
        for i, line in enumerate(NOTE_LINES):
            st = start + i * 0.9
            if t < st or not line:
                continue
            app.txt(f"intro_n{i}", typed(line, t, st, 40), W / 2 - 300, H - 210 - i * 30,
                    (215, 208, 192, a), 15, bold=True)

    def draw_title(self, app, t):
        k = window(t, (TITLE[0], TITLE[1] + 5), 1.4, 1.0)
        out = clamp((TITLE[1] - t) / 1.2)
        a = int(255 * k * out)
        glow_k = 0.6 + 0.4 * math.sin(t * 2.2)
        glow(W / 2, H / 2 + 20, 340, (255, 150, 50), 60 * glow_k * k * out)
        app.txt("intro_t1", "LAST LIGHT", W / 2, H / 2, (255, 214, 140, a), 64, anchor_x="center", bold=True)
        if t > TITLE[0] + 1.5:
            b = int(255 * clamp((t - TITLE[0] - 1.5) / 0.8) * out)
            app.txt("intro_t2", self.title_lines[0], W / 2, H / 2 - 50,
                    (200, 200, 200, b), 15, anchor_x="center")
        if t > TITLE[0] + 3.0:
            b = int(255 * clamp((t - TITLE[0] - 3.0) / 0.6) * out)
            app.txt("intro_t3", self.title_lines[1], W / 2, 90,
                    (150, 210, 160, b), 12, anchor_x="center")
