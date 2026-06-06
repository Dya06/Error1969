"""Level 1: looping lunar overworld map, ship-part collection, and The Watcher.

This replaces the old maze-style Level 1 with a screen-by-screen overworld.
The map is inspired by classic screen-transition horror games:
- 4x4 sector map
- walking out of one screen moves to another sector
- world wraps around at the map edges
- collect 5 ship parts
- return to Crash Site after all parts are collected
"""

import pygame
import random
import math

from settings import *
from utils import *
from core.particles import spawn_particles, update_particles
from graphics.sprites import *


# ─────────────────────────────────────────────
#  MAP SETTINGS
# ─────────────────────────────────────────────

MAP_COLS = 4
MAP_ROWS = 4

PLAY_TOP = 55
PLAY_BOTTOM = SCREEN_H
PLAY_LEFT = 0
PLAY_RIGHT = SCREEN_W

PLAYER_RADIUS = 11
WATCHER_RADIUS = 22

# Player starts at D2 = col 1, row 3
START_SECTOR = (1, 3)

# Crash site is also D2
CRASH_SITE_SECTOR = (1, 3)


# ─────────────────────────────────────────────
#  PART DATA
# ─────────────────────────────────────────────

PART_TYPES = {
    "ENGINE CORE": 0,
    "FUEL CELL": 1,
    "NAV MODULE": 2,
    "COMMS ARRAY": 3,
    "LIFE SUPPORT": 4,
}


# ─────────────────────────────────────────────
#  SECTOR DATA
#  Coordinates: (col, row)
# ─────────────────────────────────────────────

SECTOR_DATA = {
    (0, 0): {
        "code": "A1",
        "name": "SILENT PLAIN",
        "theme": "plain",
        "part": None,
        "part_pos": None,
        "danger": 0.10,
        "obstacles": [
            {"kind": "rock", "x": 150, "y": 170, "w": 60, "h": 42},
            {"kind": "rock", "x": 530, "y": 300, "w": 90, "h": 55},
            {"kind": "small_rocks", "x": 330, "y": 440, "w": 100, "h": 60},
        ],
    },
    (1, 0): {
        "code": "A2",
        "name": "SIGNAL RIDGE",
        "theme": "signal",
        "part": None,
        "part_pos": None,
        "danger": 0.15,
        "obstacles": [
            {"kind": "antenna", "x": 360, "y": 185, "w": 70, "h": 125},
            {"kind": "rock", "x": 130, "y": 370, "w": 80, "h": 50},
            {"kind": "rock", "x": 610, "y": 390, "w": 85, "h": 48},
        ],
    },
    (2, 0): {
        "code": "A3",
        "name": "BROKEN ROVER",
        "theme": "rover",
        "part": None,
        "part_pos": None,
        "danger": 0.18,
        "obstacles": [
            {"kind": "rover", "x": 330, "y": 285, "w": 150, "h": 78},
            {"kind": "rock", "x": 100, "y": 180, "w": 70, "h": 45},
            {"kind": "small_rocks", "x": 580, "y": 420, "w": 120, "h": 60},
        ],
    },
    (3, 0): {
        "code": "A4",
        "name": "BLACK CRATER",
        "theme": "crater",
        "part": None,
        "part_pos": None,
        "danger": 0.35,
        "obstacles": [
            {"kind": "crater", "x": 400, "y": 330, "r": 115},
            {"kind": "rock", "x": 140, "y": 170, "w": 70, "h": 45},
            {"kind": "rock", "x": 620, "y": 470, "w": 70, "h": 45},
        ],
    },

    (0, 1): {
        "code": "B1",
        "name": "BONE FIELD",
        "theme": "bones",
        "part": None,
        "part_pos": None,
        "danger": 0.22,
        "obstacles": [
            {"kind": "helmet", "x": 250, "y": 330, "w": 55, "h": 55},
            {"kind": "rock", "x": 540, "y": 200, "w": 90, "h": 60},
            {"kind": "small_rocks", "x": 440, "y": 460, "w": 120, "h": 50},
        ],
    },
    (1, 1): {
        "code": "B2",
        "name": "WATCHER ZONE",
        "theme": "watcher",
        "part": None,
        "part_pos": None,
        "danger": 0.60,
        "obstacles": [
            {"kind": "eye_mark", "x": 365, "y": 270, "w": 110, "h": 80},
            {"kind": "rock", "x": 130, "y": 420, "w": 80, "h": 50},
            {"kind": "rock", "x": 610, "y": 170, "w": 75, "h": 50},
        ],
    },
    (2, 1): {
        "code": "B3",
        "name": "FUEL WRECK",
        "theme": "fuel",
        "part": "FUEL CELL",
        "part_pos": (570, 400),
        "danger": 0.30,
        "obstacles": [
            {"kind": "fuel_tank", "x": 250, "y": 290, "w": 180, "h": 70},
            {"kind": "pipe", "x": 455, "y": 245, "w": 90, "h": 32},
            {"kind": "rock", "x": 120, "y": 445, "w": 75, "h": 45},
        ],
    },
    (3, 1): {
        "code": "B4",
        "name": "DEAD BEACON",
        "theme": "beacon",
        "part": None,
        "part_pos": None,
        "danger": 0.18,
        "obstacles": [
            {"kind": "beacon", "x": 385, "y": 250, "w": 65, "h": 120},
            {"kind": "rock", "x": 150, "y": 390, "w": 85, "h": 52},
            {"kind": "rock", "x": 600, "y": 405, "w": 80, "h": 48},
        ],
    },

    (0, 2): {
        "code": "C1",
        "name": "GLASS ROCKS",
        "theme": "glass",
        "part": None,
        "part_pos": None,
        "danger": 0.20,
        "obstacles": [
            {"kind": "crystal", "x": 185, "y": 220, "w": 85, "h": 105},
            {"kind": "crystal", "x": 520, "y": 355, "w": 100, "h": 120},
            {"kind": "rock", "x": 340, "y": 460, "w": 70, "h": 45},
        ],
    },
    (1, 2): {
        "code": "C2",
        "name": "NAVIGATION RUINS",
        "theme": "nav",
        "part": "NAV MODULE",
        "part_pos": (570, 220),
        "danger": 0.28,
        "obstacles": [
            {"kind": "console", "x": 300, "y": 290, "w": 145, "h": 80},
            {"kind": "panel", "x": 120, "y": 420, "w": 120, "h": 45},
            {"kind": "rock", "x": 610, "y": 400, "w": 85, "h": 55},
        ],
    },
    (2, 2): {
        "code": "C3",
        "name": "EMPTY PLAIN",
        "theme": "empty",
        "part": None,
        "part_pos": None,
        "danger": 0.25,
        "obstacles": [
            {"kind": "small_rocks", "x": 220, "y": 260, "w": 100, "h": 55},
            {"kind": "small_rocks", "x": 560, "y": 390, "w": 110, "h": 55},
        ],
    },
    (3, 2): {
        "code": "C4",
        "name": "LIFE SUPPORT FIELD",
        "theme": "life",
        "part": "LIFE SUPPORT",
        "part_pos": (245, 410),
        "danger": 0.32,
        "obstacles": [
            {"kind": "oxygen_tank", "x": 430, "y": 245, "w": 135, "h": 70},
            {"kind": "pipe", "x": 190, "y": 300, "w": 120, "h": 32},
            {"kind": "rock", "x": 620, "y": 455, "w": 85, "h": 48},
        ],
    },

    (0, 3): {
        "code": "D1",
        "name": "COMMS DISH",
        "theme": "comms",
        "part": "COMMS ARRAY",
        "part_pos": (545, 365),
        "danger": 0.24,
        "obstacles": [
            {"kind": "dish", "x": 285, "y": 255, "w": 170, "h": 145},
            {"kind": "rock", "x": 115, "y": 445, "w": 75, "h": 48},
            {"kind": "panel", "x": 565, "y": 220, "w": 115, "h": 48},
        ],
    },
    (1, 3): {
        "code": "D2",
        "name": "CRASH SITE",
        "theme": "crash",
        "part": None,
        "part_pos": None,
        "danger": 0.12,
        "obstacles": [
            {"kind": "ship", "x": 320, "y": 300, "w": 150, "h": 120},
            {"kind": "debris", "x": 145, "y": 415, "w": 120, "h": 55},
            {"kind": "debris", "x": 575, "y": 420, "w": 110, "h": 52},
        ],
    },
    (2, 3): {
        "code": "D3",
        "name": "ENGINE PIT",
        "theme": "engine",
        "part": "ENGINE CORE",
        "part_pos": (590, 405),
        "danger": 0.34,
        "obstacles": [
            {"kind": "engine_crater", "x": 350, "y": 330, "r": 90},
            {"kind": "wreckage", "x": 150, "y": 250, "w": 120, "h": 65},
            {"kind": "rock", "x": 610, "y": 190, "w": 80, "h": 48},
        ],
    },
    (3, 3): {
        "code": "D4",
        "name": "SHADOW FIELD",
        "theme": "shadow",
        "part": None,
        "part_pos": None,
        "danger": 0.45,
        "obstacles": [
            {"kind": "shadow_rock", "x": 180, "y": 230, "w": 100, "h": 95},
            {"kind": "shadow_rock", "x": 565, "y": 365, "w": 120, "h": 110},
            {"kind": "eye_mark", "x": 370, "y": 430, "w": 105, "h": 70},
        ],
    },
}


# ─────────────────────────────────────────────
#  SMALL HELPERS
# ─────────────────────────────────────────────

def sector_label(col, row):
    letters = "ABCD"
    return f"{letters[row]}{col + 1}"


def rect_from_obstacle(ob):
    """Return a pygame.Rect for rectangular obstacles."""
    return pygame.Rect(ob["x"], ob["y"], ob["w"], ob["h"])


def is_circle_obstacle(ob):
    return "r" in ob


class Level1:
    """Looping lunar overworld level."""

    HUD_H = PLAY_TOP

    def __init__(self):
        # ── Sector / map ───────────────────────────────
        self.sector_col, self.sector_row = START_SECTOR
        self.visited_sectors = {START_SECTOR}
        self.sector_flash_timer = 120

        # ── Player ────────────────────────────────────
        self.px = SCREEN_W // 2
        self.py = SCREEN_H - 150
        self.speed = 3.0
        self.player_frame = 0
        self.facing = 1

        # ── Ship parts ────────────────────────────────
        self.parts_total = 5
        self.collected_parts = set()
        self.flash_msg = ""
        self.flash_timer = 0

        # ── State ─────────────────────────────────────
        self.player_hp = 10
        self.player_max = 10
        self.done = False
        self.lose = False
        self.t = 0
        self.immune_timer = 0

        # ── Watcher state ─────────────────────────────
        self.watcher_sector = (1, 1)  # B2
        self.watcher_x = 120
        self.watcher_y = 160
        self.watcher_frame = 0
        self.watcher_speed = 1.1
        self.watcher_sector_timer = 0
        self.watcher_sector_delay = 330
        self.watcher_visible = False
        self.heartbeat_timer = 0

        # ── Jumpscare ─────────────────────────────────
        self.jumpscare_active = False
        self.jumpscare_timer = 0
        self.jumpscare_scale = 0.0
        self.JUMPSCARE_DUR = 120

        # ── Transition / screen movement ──────────────
        self.transition_timer = 0
        self.transition_max = 16

        # ── Sounds ────────────────────────────────────
        self._init_sounds()

        # ── Image Assets & Sprites (No hardcoded graphics) ──
        try:
            self.world_map_img = pygame.transform.scale(
                pygame.image.load("assets/images/level1_bg.png").convert(),
                (3200, 2400)
            )
        except Exception as e:
            print(f"[ERROR] Failed to load level1_bg.png: {e}")
            self.world_map_img = None

        def load_colorkey_img(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img.set_colorkey((0, 0, 0))
                return img
            except Exception as e:
                print(f"[WARNING] Failed to load sprite {path}: {e}")
                return None

        self.watcher_img = load_colorkey_img("assets/images/watcher.png")
        self.rock_img = load_colorkey_img("assets/images/rock.png")
        self.crater_img = load_colorkey_img("assets/images/crater.png")
        self.debris_img = load_colorkey_img("assets/images/debris.png")

        # Load astronaut walking frames from Level 2
        self.astro_frames = []
        for i in range(10):
            path = f"assets/images/monsters/astronaut/ASTRO{i}.png"
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (40, 40))
                self.astro_frames.append(img)
            except Exception as e:
                print(f"[ERROR] Failed to load ASTRO{i}.png: {e}")
        self.astro_anim_speed = 6

    # ─────────────────────────────────────────────
    #  SOUND
    # ─────────────────────────────────────────────

    def _init_sounds(self):
        self.snd_collect = self._gen_tone(880, 0.12, shape="square")
        self.snd_heartbeat = self._gen_tone(60, 0.18, shape="pulse")
        self.snd_jumpscare = self._gen_noise(0.5)

    def _gen_tone(self, freq, duration, shape="sine", volume=0.3):
        try:
            import numpy as np
            sr = 44100
            n = int(sr * duration)
            t = np.linspace(0, duration, n, endpoint=False)

            if shape == "square":
                wave = np.sign(np.sin(2 * np.pi * freq * t))
            elif shape == "pulse":
                wave = np.where(np.sin(2 * np.pi * freq * t) > 0.7, 1.0, -0.3)
            else:
                wave = np.sin(2 * np.pi * freq * t)

            wave = (wave * volume * 32767).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

    def _gen_noise(self, duration, volume=0.8):
        try:
            import numpy as np
            sr = 44100
            n = int(sr * duration)
            wave = (np.random.uniform(-1, 1, n) * volume * 32767).astype(np.int16)

            for i in range(1, n):
                wave[i] = int(wave[i] * 0.3 + wave[i - 1] * 0.7)

            stereo = np.column_stack([wave, wave])
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

    def _play(self, snd):
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    # ─────────────────────────────────────────────
    #  BASIC STATE
    # ─────────────────────────────────────────────

    def current_sector(self):
        return self.sector_col, self.sector_row

    def sector_info(self):
        return SECTOR_DATA[self.current_sector()]

    def all_parts_collected(self):
        return len(self.collected_parts) >= self.parts_total

    # ─────────────────────────────────────────────
    #  INPUT / UPDATE
    # ─────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.done = True

    def update(self):
        if self.jumpscare_active:
            self._update_jumpscare()
            return

        self.t += 1
        self.player_frame += 1
        self.watcher_frame += 1

        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.sector_flash_timer > 0:
            self.sector_flash_timer -= 1

        if self.transition_timer > 0:
            self.transition_timer -= 1

        if self.immune_timer > 0:
            self.immune_timer -= 1

        self._update_player()
        self._update_part_collection()
        self._update_watcher()

    def _update_player(self):
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        if dx and dy:
            dx *= 0.707
            dy *= 0.707

        if dx:
            self.facing = dx

        new_x = self.px + dx * self.speed
        new_y = self.py + dy * self.speed

        new_x, new_y = self._move_with_obstacle_collision(new_x, new_y)

        self.px = new_x
        self.py = new_y

        self._check_screen_transition()

    def _move_with_obstacle_collision(self, new_x, new_y):
        """Simple collision against sector obstacles."""
        current_x = self.px
        current_y = self.py

        # Move X first
        if not self._collides_with_obstacle(new_x, current_y, PLAYER_RADIUS):
            current_x = new_x

        # Then Y
        if not self._collides_with_obstacle(current_x, new_y, PLAYER_RADIUS):
            current_y = new_y

        return current_x, current_y

    def _collides_with_obstacle(self, x, y, radius):
        """Check player/watcher circle collision with current sector obstacles."""
        for ob in self.sector_info()["obstacles"]:
            if is_circle_obstacle(ob):
                d = math.hypot(x - ob["x"], y - ob["y"])
                if d < radius + ob["r"]:
                    return True
            else:
                rect = rect_from_obstacle(ob).inflate(radius * 2, radius * 2)
                if rect.collidepoint(x, y):
                    return True

        return False

    def _check_screen_transition(self):
        moved = False
        entered_from = None

        if self.px < PLAY_LEFT:
            self.sector_col = (self.sector_col - 1) % MAP_COLS
            self.px = PLAY_RIGHT - 20
            moved = True
            entered_from = "right"

        elif self.px > PLAY_RIGHT:
            self.sector_col = (self.sector_col + 1) % MAP_COLS
            self.px = PLAY_LEFT + 20
            moved = True
            entered_from = "left"

        if self.py < PLAY_TOP:
            self.sector_row = (self.sector_row - 1) % MAP_ROWS
            self.py = PLAY_BOTTOM - 25
            moved = True
            entered_from = "bottom"

        elif self.py > PLAY_BOTTOM:
            self.sector_row = (self.sector_row + 1) % MAP_ROWS
            self.py = PLAY_TOP + 25
            moved = True
            entered_from = "top"

        if moved:
            self.visited_sectors.add(self.current_sector())
            self.sector_flash_timer = 120
            self.transition_timer = self.transition_max
            self._maybe_spawn_watcher_on_entry(entered_from)

    # ─────────────────────────────────────────────
    #  PART COLLECTION
    # ─────────────────────────────────────────────

    def _update_part_collection(self):
        info = self.sector_info()
        part_name = info["part"]

        if part_name is None:
            # Finish condition: all parts collected and player returns to Crash Site.
            if self.all_parts_collected() and self.current_sector() == CRASH_SITE_SECTOR:
                if math.hypot(self.px - 400, self.py - 330) < 110:
                    self.flash_msg = "REPAIR SEQUENCE READY!"
                    self.flash_timer = 90
                    self.done = True
            return

        if part_name in self.collected_parts:
            return

        part_x, part_y = info["part_pos"]

        if math.hypot(self.px - part_x, self.py - part_y) < 28:
            self.collected_parts.add(part_name)
            self.flash_msg = f"{part_name} RECOVERED!"
            self.flash_timer = 110

            spawn_particles(
                int(part_x),
                int(part_y),
                GOLD,
                22,
                3,
                50
            )

            self._play(self.snd_collect)

            # Make Watcher angrier
            self.watcher_speed = 1.1 + 0.12 * len(self.collected_parts)
            self.watcher_sector_delay = max(150, 330 - len(self.collected_parts) * 35)

            if self.all_parts_collected():
                self.flash_msg = "ALL PARTS FOUND! RETURN TO CRASH SITE!"
                self.flash_timer = 160

    # ─────────────────────────────────────────────
    #  WATCHER
    # ─────────────────────────────────────────────

    def _update_watcher(self):
        current = self.current_sector()
        watcher_same_sector = self.watcher_sector == current
        watcher_nearby = self._sector_distance(self.watcher_sector, current) <= 1

        self.watcher_sector_timer += 1

        if self.watcher_sector_timer >= self.watcher_sector_delay:
            self.watcher_sector_timer = 0
            self._move_watcher_sector_towards_player()

        if watcher_same_sector:
            self.watcher_visible = True
            self._chase_player()
        else:
            self.watcher_visible = False

        # Heartbeat when nearby or same sector
        self.heartbeat_timer -= 1

        if watcher_nearby:
            interval = 45 if not watcher_same_sector else 18
            if self.heartbeat_timer <= 0:
                self._play(self.snd_heartbeat)
                self.heartbeat_timer = interval

    def _sector_distance(self, a, b):
        """Wrapped Manhattan distance between two sectors."""
        ax, ay = a
        bx, by = b

        dx = abs(ax - bx)
        dy = abs(ay - by)

        dx = min(dx, MAP_COLS - dx)
        dy = min(dy, MAP_ROWS - dy)

        return dx + dy

    def _move_watcher_sector_towards_player(self):
        """Move Watcher one sector closer to player, considering wrap-around."""
        wc, wr = self.watcher_sector
        pc, pr = self.current_sector()

        # Determine shortest wrapped horizontal direction
        right_steps = (pc - wc) % MAP_COLS
        left_steps = (wc - pc) % MAP_COLS

        # Determine shortest wrapped vertical direction
        down_steps = (pr - wr) % MAP_ROWS
        up_steps = (wr - pr) % MAP_ROWS

        possible_moves = []

        if wc != pc:
            if right_steps <= left_steps:
                possible_moves.append(((wc + 1) % MAP_COLS, wr))
            else:
                possible_moves.append(((wc - 1) % MAP_COLS, wr))

        if wr != pr:
            if down_steps <= up_steps:
                possible_moves.append((wc, (wr + 1) % MAP_ROWS))
            else:
                possible_moves.append((wc, (wr - 1) % MAP_ROWS))

        if possible_moves:
            self.watcher_sector = random.choice(possible_moves)

        # If it enters the player's current sector, spawn it away from the player
        if self.watcher_sector == self.current_sector():
            self._spawn_watcher_far_from_player()

    def _maybe_spawn_watcher_on_entry(self, entered_from):
        """If Watcher is already in this sector, spawn it fairly away from player."""
        if self.watcher_sector == self.current_sector():
            self._spawn_watcher_far_from_player()

    def _spawn_watcher_far_from_player(self):
        """Spawn Watcher at the farthest corner from player."""
        corners = [
            (70, PLAY_TOP + 70),
            (SCREEN_W - 70, PLAY_TOP + 70),
            (70, SCREEN_H - 70),
            (SCREEN_W - 70, SCREEN_H - 70),
        ]

        best = max(corners, key=lambda p: math.hypot(p[0] - self.px, p[1] - self.py))
        self.watcher_x, self.watcher_y = best

    def _chase_player(self):
        dx = self.px - self.watcher_x
        dy = self.py - self.watcher_y
        dist = math.hypot(dx, dy)

        if dist > 1:
            nx = self.watcher_x + (dx / dist) * self.watcher_speed
            ny = self.watcher_y + (dy / dist) * self.watcher_speed

            # Watcher can glide slightly through tight areas, but avoid big obstacles
            if not self._collides_with_obstacle(nx, ny, WATCHER_RADIUS):
                self.watcher_x = nx
                self.watcher_y = ny
            else:
                # If blocked, try simple axis movement
                if not self._collides_with_obstacle(nx, self.watcher_y, WATCHER_RADIUS):
                    self.watcher_x = nx
                if not self._collides_with_obstacle(self.watcher_x, ny, WATCHER_RADIUS):
                    self.watcher_y = ny

        if dist < 34 and not self.jumpscare_active:
            self._trigger_jumpscare()

    def _trigger_jumpscare(self):
        self.jumpscare_active = True
        self.jumpscare_timer = 0
        self.jumpscare_scale = 0.0
        self._play(self.snd_jumpscare)

    def _update_jumpscare(self):
        self.jumpscare_timer += 1
        t = self.jumpscare_timer

        if t < 40:
            self.jumpscare_scale = t / 40
        elif t < 80:
            self.jumpscare_scale = 1.0
        else:
            self.jumpscare_scale = max(0.0, 1.0 - (t - 80) / 40)

        if self.jumpscare_timer >= self.JUMPSCARE_DUR:
            self.jumpscare_active = False
            self.player_hp = 0
            self.lose = True

    # ─────────────────────────────────────────────
    #  DRAWING
    # ─────────────────────────────────────────────

    def draw(self, surf):
        if self.jumpscare_active:
            self._draw_jumpscare(surf)
            return

        self._draw_sector_background(surf)
        self._draw_sector_details(surf)
        self._draw_obstacles(surf)
        self._draw_part(surf)

        if self.watcher_visible:
            self._draw_watcher(surf)

        # Draw player astronaut using image frames
        if self.astro_frames:
            frame_index = (self.player_frame // self.astro_anim_speed) % len(self.astro_frames)
            img = self.astro_frames[frame_index]
            if self.facing == -1:
                img = pygame.transform.flip(img, True, False)
            rect = img.get_rect(center=(int(self.px), int(self.py)))
            surf.blit(img, rect)
        else:
            draw_astronaut(surf, int(self.px), int(self.py), self.player_frame, self.facing)

        update_particles(surf)

        self._draw_danger_overlay(surf)
        self._draw_hud(surf)
        self._draw_sector_title(surf)
        self._draw_flash_message(surf)
        self._draw_transition_overlay(surf)

    def _draw_sector_background(self, surf):
        col, row = self.current_sector()
        if self.world_map_img:
            # Draw segment of the larger moon world map background image
            sub_img = self.world_map_img.subsurface(pygame.Rect(col * 800, row * 600, 800, 600))
            surf.blit(sub_img, (0, 0))
        else:
            surf.fill((34, 34, 42))

        # Star strip above playfield / sky feel
        pygame.draw.rect(surf, (4, 4, 12), (0, 0, SCREEN_W, PLAY_TOP))

        # Sector border lines like screen tiles / Faith-ish framing
        pygame.draw.rect(surf, (70, 70, 85), (0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP), 1)

    def _draw_sector_details(self, surf):
        info = self.sector_info()
        theme = info["theme"]

        # Footprints/tracks
        rng = random.Random((self.sector_col + 1) * 123 + (self.sector_row + 1) * 456)
        for _ in range(8):
            x = rng.randint(80, SCREEN_W - 80)
            y = rng.randint(PLAY_TOP + 70, SCREEN_H - 70)
            pygame.draw.ellipse(surf, (55, 55, 65), (x, y, 7, 3))
            pygame.draw.ellipse(surf, (50, 50, 60), (x + 12, y + 7, 7, 3))

        # Atmospheric colored glows (ambient light indicators)
        if theme == "crater":
            glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 0, 120, 50), (400, 330), 150)
            surf.blit(glow, (0, 0))

        elif theme == "engine":
            glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 100, 0, 45), (350, 330), 130)
            surf.blit(glow, (0, 0))

        elif theme == "life":
            glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 180, 80, 35), (400, 300), 160)
            surf.blit(glow, (0, 0))

        elif theme == "fuel":
            glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 180, 220, 30), (350, 320), 150)
            surf.blit(glow, (0, 0))

    def _draw_obstacles(self, surf):
        for ob in self.sector_info()["obstacles"]:
            self._draw_obstacle(surf, ob)

    def _draw_obstacle(self, surf, ob):
        kind = ob["kind"]

        if is_circle_obstacle(ob):
            x, y, r = ob["x"], ob["y"], ob["r"]
            rect = pygame.Rect(x - r, y - r, r * 2, r * 2)
            if kind in ("crater", "engine_crater") and self.crater_img:
                scaled_img = pygame.transform.scale(self.crater_img, (rect.w, rect.h))
                surf.blit(scaled_img, rect.topleft)
            else:
                if kind in ("crater", "engine_crater"):
                    fill = (10, 10, 16) if kind == "crater" else (35, 16, 8)
                    rim = (90, 90, 105) if kind == "crater" else (160, 80, 30)
                    pygame.draw.circle(surf, rim, (x, y), r)
                    pygame.draw.circle(surf, fill, (x, y), int(r * 0.78))
                else:
                    pygame.draw.circle(surf, (65, 65, 75), (x, y), r)
            return

        rect = rect_from_obstacle(ob)

        if kind in ("rock", "small_rocks", "shadow_rock"):
            if self.rock_img:
                scaled_img = pygame.transform.scale(self.rock_img, (rect.w, rect.h))
                surf.blit(scaled_img, rect.topleft)
            else:
                pygame.draw.ellipse(surf, (55, 55, 66), rect)
        else:
            if self.debris_img:
                scaled_img = pygame.transform.scale(self.debris_img, (rect.w, rect.h))
                surf.blit(scaled_img, rect.topleft)
            else:
                pygame.draw.rect(surf, (70, 70, 78), rect)

    def _draw_part(self, surf):
        info = self.sector_info()
        part_name = info["part"]

        if part_name is None or part_name in self.collected_parts:
            return

        x, y = info["part_pos"]
        part_type = PART_TYPES.get(part_name, 0)

        # Glow
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.08)
        glow_r = int(26 + 8 * pulse)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 220, 60, 70), (glow_r, glow_r), glow_r)
        surf.blit(glow, (x - glow_r, y - glow_r))

        # Existing detailed part drawer
        draw_ship_part(surf, x, y, part_type)

        if math.hypot(self.px - x, self.py - y) < 75:
            draw_text(
                surf,
                f"RECOVER {part_name}",
                font_tiny,
                GOLD,
                x,
                y - 45
            )

    def _draw_watcher(self, surf):
        wx = int(self.watcher_x)
        wy = int(self.watcher_y)
        t = self.watcher_frame * 0.05
        bob = int(4 * math.sin(t))
        if self.watcher_img:
            scaled_img = pygame.transform.scale(self.watcher_img, (44, 44))
            rect = scaled_img.get_rect(center=(wx, wy + bob))
            surf.blit(scaled_img, rect)
        else:
            draw_watcher(surf, wx, wy, self.watcher_frame)

    def _draw_danger_overlay(self, surf):
        current = self.current_sector()
        dist = self._sector_distance(self.watcher_sector, current)

        if dist <= 1:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            alpha = 40 if dist == 1 else 85
            overlay.fill((80, 0, 120, alpha))
            surf.blit(overlay, (0, 0))

        if self.watcher_visible:
            d = math.hypot(self.px - self.watcher_x, self.py - self.watcher_y)
            if d < 180:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                alpha = int(clamp((180 - d) / 180 * 120, 0, 120))
                overlay.fill((130, 0, 0, alpha))
                surf.blit(overlay, (0, 0))

                pulse = int(200 + 55 * math.sin(self.t * 0.2))
                draw_text(
                    surf,
                    "IT'S HERE",
                    font_med,
                    (pulse, 30, 30),
                    SCREEN_W // 2,
                    SCREEN_H // 2 + 95
                )

    def _draw_hud(self, surf):
        hud = pygame.Surface((SCREEN_W, PLAY_TOP), pygame.SRCALPHA)
        hud.fill((6, 8, 18, 235))
        surf.blit(hud, (0, 0))

        pygame.draw.line(surf, (90, 90, 120), (0, PLAY_TOP), (SCREEN_W, PLAY_TOP), 2)

        info = self.sector_info()

        # Left objective panel
        pygame.draw.rect(surf, (18, 20, 34), (12, 9, 230, 36), border_radius=8)
        pygame.draw.rect(surf, (90, 90, 120), (12, 9, 230, 36), 1, border_radius=8)

        draw_text_left(surf, "LEVEL 1", font_tiny, (120, 120, 150), 24, 14)

        objective = "RETURN TO CRASH SITE" if self.all_parts_collected() else "RECOVER SHIP PARTS"
        draw_text_left(surf, objective, font_small, MOON_GREY, 24, 27)

        # Centre sector
        draw_text(
            surf,
            f"SECTOR {info['code']} // {info['name']}",
            font_small,
            (170, 170, 190),
            SCREEN_W // 2,
            16
        )

        # Parts counter
        pygame.draw.rect(surf, (30, 24, 10), (SCREEN_W // 2 - 80, 28, 160, 18), border_radius=6)
        pygame.draw.rect(surf, GOLD, (SCREEN_W // 2 - 80, 28, 160, 18), 1, border_radius=6)

        draw_text(
            surf,
            f"PARTS {len(self.collected_parts)}/{self.parts_total}",
            font_tiny,
            GOLD,
            SCREEN_W // 2,
            37
        )

        # Health bar
        draw_hp_bar(
            surf,
            SCREEN_W - 190,
            15,
            165,
            20,
            self.player_hp,
            self.player_max,
            "SUIT"
        )

        # Sector minimap
        self._draw_sector_minimap(surf)

    def _draw_sector_minimap(self, surf):
        size = 9
        gap = 3
        start_x = SCREEN_W - 78
        start_y = 6

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                x = start_x + col * (size + gap)
                y = start_y + row * (size + gap)
                sector = (col, row)

                if sector == self.current_sector():
                    colr = CYAN
                elif sector == self.watcher_sector:
                    colr = PURPLE
                elif sector in self.visited_sectors:
                    colr = (80, 80, 100)
                else:
                    colr = (20, 20, 30)

                pygame.draw.rect(surf, colr, (x, y, size, size))
                pygame.draw.rect(surf, (120, 120, 150), (x, y, size, size), 1)

    def _draw_sector_title(self, surf):
        if self.sector_flash_timer <= 0:
            return

        info = self.sector_info()
        alpha = min(255, self.sector_flash_timer * 3)

        draw_text(
            surf,
            f"SECTOR {info['code']}",
            font_large,
            (220, 220, 230),
            SCREEN_W // 2,
            SCREEN_H // 2 - 35,
            alpha
        )

        draw_text(
            surf,
            info["name"],
            font_med,
            (170, 170, 190),
            SCREEN_W // 2,
            SCREEN_H // 2 + 5,
            alpha
        )

    def _draw_flash_message(self, surf):
        if self.flash_timer <= 0:
            return

        alpha = min(255, self.flash_timer * 3)
        draw_text(
            surf,
            self.flash_msg,
            font_med,
            YELLOW,
            SCREEN_W // 2,
            SCREEN_H // 2 - 90,
            alpha
        )

    def _draw_transition_overlay(self, surf):
        if self.transition_timer <= 0:
            return

        ratio = self.transition_timer / self.transition_max
        alpha = int(160 * ratio)

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surf.blit(overlay, (0, 0))

    def _draw_jumpscare(self, surf):
        t = self.jumpscare_timer
        scale = self.jumpscare_scale

        if t < 10:
            surf.fill((180, 0, 0))
        else:
            surf.fill((0, 0, 0))

        cx, cy = SCREEN_W // 2, SCREEN_H // 2 - 30
        size = int(scale * 260)

        if size > 10:
            for ar in range(size + 60, size, -20):
                alpha = max(0, int(80 * (1 - (ar - size) / 60) * scale))
                s = pygame.Surface((ar * 2, ar * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (120, 0, 160, alpha), (ar, ar), ar)
                surf.blit(s, (cx - ar, cy - ar))

            pygame.draw.circle(surf, (230, 220, 220), (cx, cy), size)
            iris_wobble = int(8 * math.sin(t * 0.4))
            pygame.draw.circle(surf, PURPLE, (cx + iris_wobble, cy), int(size * 0.6))
            pygame.draw.circle(surf, BLACK, (cx + iris_wobble, cy), int(size * 0.35))
            pygame.draw.circle(
                surf,
                WHITE,
                (cx + iris_wobble - size // 6, cy - size // 6),
                max(1, size // 10)
            )

            for i in range(12):
                angle = i * math.pi / 6 + t * 0.05
                ex = int(cx + size * math.cos(angle))
                ey = int(cy + size * math.sin(angle))
                pygame.draw.line(surf, BLOOD_RED, (cx, cy), (ex, ey), 2)

        if t > 20:
            text_alpha = min(255, (t - 20) * 8)
            pulse = int(220 + 35 * math.sin(t * 0.3))

            draw_text(
                surf,
                "IT FOUND YOU",
                font_huge,
                (pulse, 0, 0),
                SCREEN_W // 2,
                SCREEN_H - 120,
                text_alpha
            )

            draw_text(
                surf,
                "THE WATCHER SEES ALL",
                font_med,
                (180, 0, 0),
                SCREEN_W // 2,
                SCREEN_H - 60,
                text_alpha
            )

        if t > 80:
            fade_alpha = int((t - 80) / 40 * 255)
            fs = pygame.Surface((SCREEN_W, SCREEN_H))
            fs.fill(BLACK)
            fs.set_alpha(clamp(fade_alpha, 0, 255))
            surf.blit(fs, (0, 0))
