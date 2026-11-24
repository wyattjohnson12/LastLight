# Last Light

A top-down survival game: gather by day, build by dusk, survive the night.
Craft at a workbench, smelt iron, wear armor, tame pets, share a team storage bin,
explore the caves, and survive a boss every third night. Play solo, online co-op over
Wi-Fi, or split-screen on one computer. Keyboard + mouse or an Xbox controller.

## First time setup

1. Install **Python 3** from <https://www.python.org/downloads/>
   (Windows: tick **"Add Python to PATH"** in the installer).
2. Open Terminal (Mac) or Command Prompt (Windows) and run:

   ```
   git clone https://github.com/wyattjohnson12/LastLight.git
   cd LastLight
   pip3 install -r requirements.txt
   ```
   (Windows: use `pip` instead of `pip3`.)

## Play

```
cd LastLight
python3 main.py
```
(Windows: `python main.py`)

## Get the newest version

```
cd LastLight
git pull
```
That's it - run the game again and you have every update.

## Playing together

- **Online co-op (same Wi-Fi):** one person picks **Host co-op game**, everyone else picks
  **Join co-op game** - the host's game shows up in the list. Click **Allow** if your computer
  asks about network connections. Everyone should `git pull` first so you're on the same version.
- **Local co-op (one screen):** pick **Local co-op**. Press **A** on a controller or **ENTER**
  on the keyboard to join, then **START** / **ENTER** to begin.

## Controls

| Action | Keyboard + mouse | Controller |
|---|---|---|
| Move / aim | WASD / mouse | Left stick / right stick |
| Attack, chop, mine, hunt | Left click | A or RT |
| Build, eat, tame | Right click | LT |
| Hotbar | 1-8, mouse wheel | LB / RB |
| Backpack, crafting, armor | TAB | Y |
| Storage, cave entrance, drink | E | B |
| Quick eat / drink | Q | B |
| Pet orders | F | D-pad down |
| Rest | SHIFT | hold X |
| Pause / help | ESC | Menu |
