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

PLAYER_RADIUS = 18
WATCHER_RADIUS = 30

# Player starts at B4 = col 3, row 1
START_SECTOR = (3, 1)

# Crash site is the starting sector B4
CRASH_SITE_SECTOR = START_SECTOR


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
#  OBSTACLE MAPPING
# ─────────────────────────────────────────────

OBSTACLE_MAPPING = {
    # Blue Barrel
    "fuel_tank": "blue_barrel",
    "pipe": "blue_barrel",
    "oxygen_tank": "blue_barrel",
    "beacon": "blue_barrel",
    "helmet": "blue_barrel",
    "crater": "blue_barrel",
    "engine_crater": "blue_barrel",
    
    # Green Crate
    "console": "green_crate",
    "panel": "green_crate",
    "rover": "green_crate",
    "antenna": "green_crate",
    "rock": "green_crate",
    "small_rocks": "green_crate",
    "shadow_rock": "green_crate",
    
    # Orange Barrier
    "dish": "orange_barrier",
    "wreckage": "orange_barrier",
    "debris": "orange_barrier",
    "crystal": "orange_barrier",
    "eye_mark": "orange_barrier",

    # Crashed Spaceship Wreckage
    "ship": "crashed_ship",
    "crashed_ship": "crashed_ship",
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
        "name": "CRASH SITE",
        "theme": "crash",
        "part": None,
        "part_pos": None,
        "danger": 0.18,
        "obstacles": [
            {"kind": "crashed_ship", "x": 270, "y": 120, "w": 260, "h": 200},
            {"kind": "rock", "x": 130, "y": 450, "w": 85, "h": 52},
            {"kind": "rock", "x": 600, "y": 450, "w": 80, "h": 48},
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
        "name": "DEBRIS FIELD",
        "theme": "debris",
        "part": None,
        "part_pos": None,
        "danger": 0.12,
        "obstacles": [
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
        self.screen_shake = 0
        self.glitch_timer = 0
        self.glitch_active_frames = 0

        # ── Watcher state ─────────────────────────────
        self.watcher_sector = (1, 1)  # B2
        self.watcher_x = 120
        self.watcher_y = 160
        self.watcher_frame = 0
        self.watcher_speed = 1.1
        self.watcher_sector_timer = 0
        self.watcher_sector_delay = 330
        self.watcher_visible = False
        self.heartbeat_channel = None
        self.heartbeat_tier = None

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
        play_music("assets/audio/level1/level1bgmusic.wav", loops=-1, volume=0.5)

        # ── Image Assets & Sprites (No hardcoded graphics) ──
        self.sector_imgs = {}
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                code = sector_label(col, row)
                path = f"assets/images/level1_{code}.png"
                try:
                    img = pygame.image.load(path).convert()
                    img = pygame.transform.scale(img, (800, 600))
                    self.sector_imgs[code] = img
                except Exception as e:
                    print(f"[ERROR] Failed to load sector image {path}: {e}")
                    self.sector_imgs[code] = None

        def load_transparent_img(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"[WARNING] Failed to load sprite {path}: {e}")
                return None

        # Load Watcher walking frames
        self.watcher_frames = []
        for i in range(5):
            path = f"assets/images/watcher_walk{i}.png"
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, (72, 96))
                self.watcher_frames.append(img)
            except Exception as e:
                print(f"[ERROR] Failed to load {path}: {e}")
        self.rock_img = load_transparent_img("assets/images/rock.png")
        self.crater_img = load_transparent_img("assets/images/crater.png")
        self.debris_img = load_transparent_img("assets/images/debris.png")

        # Load custom colored obstacle assets
        self.obstacle_imgs = {}
        for name in ["blue_barrel", "green_crate", "orange_barrier", "crashed_ship"]:
            try:
                img = pygame.image.load(f"assets/images/{name}.png").convert_alpha()
                self.obstacle_imgs[name] = img
            except Exception as e:
                print(f"[ERROR] Failed to load obstacle image {name}: {e}")
                self.obstacle_imgs[name] = None

        try:
            self.jumpscare_img = pygame.image.load(
                "assets/images/watcher_jumpscare.png"
            ).convert_alpha()
        except Exception as e:
            print(f"[ERROR] Failed to load watcher_jumpscare.png: {e}")
            self.jumpscare_img = None

        # Load astronaut walking frames from Level 2
        self.astro_frames = []
        for i in range(10):
            path = f"assets/images/monsters/astronaut/ASTRO{i}.png"
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (72, 96))
                self.astro_frames.append(img)
            except Exception as e:
                print(f"[ERROR] Failed to load ASTRO{i}.png: {e}")
        self.astro_anim_speed = 6

    # ─────────────────────────────────────────────
    #  SOUND
    # ─────────────────────────────────────────────

    def _init_sounds(self):
        self.snd_collect = self._gen_tone(880, 0.12, shape="square")
        self.snd_heartbeat_far = load_sound("assets/audio/level1/54bpmheartbeat.wav", volume=0.4)
        self.snd_heartbeat_mid = load_sound("assets/audio/level1/75bpmheartbeat.wav", volume=0.5)
        self.snd_heartbeat_close = load_sound("assets/audio/level1/115bpmheartbeat.wav", volume=0.6)
        self.snd_jumpscare = self._gen_noise(0.5)
        self.snd_jumpscare_caught = load_sound("assets/audio/level1/Level1JumpscareCaught.mp3")

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
            return  # Freeze player/enemy updates during sector transition fade!

        if self.immune_timer > 0:
            self.immune_timer -= 1

        if self.screen_shake > 0:
            self.screen_shake -= 1

        # Glitch effect timing (subtle horizontal jitter every few seconds)
        self.glitch_timer += 1
        if self.glitch_active_frames > 0:
            self.glitch_active_frames -= 1
        elif self.glitch_timer > 210:  # ~3.5 seconds at 60fps
            if random.random() < 0.015:  # small chance once timer expires
                self.glitch_active_frames = random.randint(3, 7)  # lasts 3-7 frames
                self.glitch_timer = 0

        self._update_player()
        self._update_part_collection()
        self._update_watcher()

    def _apply_shake_offset(self):
        ox, oy = 0, 0
        if self.screen_shake > 0:
            ox += random.randint(-self.screen_shake, self.screen_shake)
            oy += random.randint(-self.screen_shake, self.screen_shake)
        if self.glitch_active_frames > 0:
            ox += random.randint(-8, 8)  # horizontal jitter shift during glitch
        return ox, oy

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

    def _obstacle_collision_shape(self, ob):
        """Get the actual uniform rect/circle used for collision and drawing (no stretching)."""
        kind = ob["kind"]
        img_key = OBSTACLE_MAPPING.get(kind, "green_crate")
        if img_key == "crashed_ship":
            size = 180
        elif img_key == "green_crate":
            size = 85
        else:
            size = 65
        if is_circle_obstacle(ob):
            # Returns (center_x, center_y, radius)
            return (ob["x"], ob["y"], size // 2)
        else:
            rect = rect_from_obstacle(ob)
            # Create a square rect of 'size' centered at rect.center
            return pygame.Rect(rect.centerx - size // 2, rect.centery - size // 2, size, size)

    def _collides_with_obstacle(self, x, y, radius):
        """Check player/watcher circle collision with current sector obstacles."""
        for ob in self.sector_info()["obstacles"]:
            shape = self._obstacle_collision_shape(ob)
            if isinstance(shape, tuple):
                cx, cy, r = shape
                d = math.hypot(x - cx, y - cy)
                if d < radius + r:
                    return True
            else:
                rect = shape.inflate(radius * 2, radius * 2)
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
                if math.hypot(self.px - 400, self.py - 330) < 130:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_e]:
                        self.flash_msg = "REPAIR SEQUENCE READY!"
                        self.flash_timer = 90
                        self.done = True
                        stop_music(fade_ms=500)
                        if self.heartbeat_channel is not None:
                            self.heartbeat_channel.stop()
                            self.heartbeat_channel = None
                            self.heartbeat_tier = None
            return

        if part_name in self.collected_parts:
            return

        part_x, part_y = info["part_pos"]

        if math.hypot(self.px - part_x, self.py - part_y) < 42:
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
            self.screen_shake = 12

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
        sector_dist = self._sector_distance(self.watcher_sector, current)
        watcher_nearby = sector_dist <= 1

        self.watcher_sector_timer += 1

        if self.watcher_sector_timer >= self.watcher_sector_delay:
            self.watcher_sector_timer = 0
            self._move_watcher_sector_towards_player()

        d = math.hypot(self.px - self.watcher_x, self.py - self.watcher_y)

        if watcher_same_sector:
            self.watcher_visible = True
            self._chase_player()
            if d < 320:
                shake_amount = int((320 - d) / 320 * 7)
                if shake_amount > self.screen_shake:
                    self.screen_shake = shake_amount
        else:
            self.watcher_visible = False

        if watcher_same_sector and d < 180:
            tier = "close"
        elif watcher_nearby:
            tier = "mid"
        else:
            tier = "far"

        self._update_heartbeat(tier)

    def _update_heartbeat(self, tier):
        if tier == self.heartbeat_tier:
            return

        self.heartbeat_tier = tier

        if self.heartbeat_channel is not None:
            self.heartbeat_channel.stop()
            self.heartbeat_channel = None

        snd = {
            "far": self.snd_heartbeat_far,
            "mid": self.snd_heartbeat_mid,
            "close": self.snd_heartbeat_close,
        }.get(tier)

        if snd:
            self.heartbeat_channel = snd.play(loops=-1)

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

        # If already in the same sector, don't move sector and don't reset spawn position
        if (wc, wr) == (pc, pr):
            return

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
        if not hasattr(self, "watcher_slide_sign"):
            self.watcher_slide_sign = 0
            self.watcher_slide_angle = 0.0

        dx = self.px - self.watcher_x
        dy = self.py - self.watcher_y
        dist = math.hypot(dx, dy)

        if dist > 1:
            target_angle = math.atan2(dy, dx)
            speed = self.watcher_speed

            # Check if direct path is clear
            dir_x = self.watcher_x + math.cos(target_angle) * speed
            dir_y = self.watcher_y + math.sin(target_angle) * speed
            direct_clear = not self._collides_with_obstacle(dir_x, dir_y, WATCHER_RADIUS)

            if direct_clear:
                # Direct path is clear! Go straight and reset slide state
                self.watcher_slide_sign = 0
                self.watcher_x = dir_x
                self.watcher_y = dir_y
            else:
                # Direct path is blocked! We need to slide
                found_slide = False
                
                # If we already have a slide direction, try to keep it
                if self.watcher_slide_sign != 0:
                    # Scan offsets using the same sign
                    for deg in [30, 45, 60, 75, 90, 105, 120, 135, 150]:
                        angle = target_angle + self.watcher_slide_sign * math.radians(deg)
                        cx = self.watcher_x + math.cos(angle) * speed
                        cy = self.watcher_y + math.sin(angle) * speed
                        
                        if not self._collides_with_obstacle(cx, cy, WATCHER_RADIUS):
                            self.watcher_slide_angle = angle
                            self.watcher_x = cx
                            self.watcher_y = cy
                            found_slide = True
                            break
                            
                # If we didn't have a sign, or the existing sign is blocked, scan both signs
                if not found_slide:
                    for deg in [45, 60, 75, 90, 105, 120, 135]:
                        rad_offset = math.radians(deg)
                        # Try both Left and Right
                        for sign in [1, -1]:
                            angle = target_angle + sign * rad_offset
                            cx = self.watcher_x + math.cos(angle) * speed
                            cy = self.watcher_y + math.sin(angle) * speed
                            
                            if not self._collides_with_obstacle(cx, cy, WATCHER_RADIUS):
                                self.watcher_slide_sign = sign
                                self.watcher_slide_angle = angle
                                self.watcher_x = cx
                                self.watcher_y = cy
                                found_slide = True
                                break
                        if found_slide:
                            break
                            
                # Fallback: simple axis movement if absolutely everything is blocked
                if not found_slide:
                    self.watcher_slide_sign = 0
                    if not self._collides_with_obstacle(dir_x, self.watcher_y, WATCHER_RADIUS):
                        self.watcher_x = dir_x
                    if not self._collides_with_obstacle(self.watcher_x, dir_y, WATCHER_RADIUS):
                        self.watcher_y = dir_y

        if dist < 34 and not self.jumpscare_active:
            self._trigger_jumpscare()

    def _trigger_jumpscare(self):
        self.jumpscare_active = True
        self.jumpscare_timer = 0
        self.jumpscare_scale = 0.0
        self._play(self.snd_jumpscare)
        self._play(self.snd_jumpscare_caught)
        stop_music(fade_ms=300)

        if self.heartbeat_channel is not None:
            self.heartbeat_channel.stop()
            self.heartbeat_channel = None
            self.heartbeat_tier = None

    def _update_jumpscare(self):
        self.jumpscare_timer += 1
        t = self.jumpscare_timer
        self.screen_shake = 14

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

        ox, oy = self._apply_shake_offset()

        self._draw_sector_background(surf, ox, oy)
        self._draw_sector_details(surf, ox, oy)
        self._draw_obstacles(surf, ox, oy)
        self._draw_part(surf, ox, oy)

        if self.watcher_visible:
            self._draw_watcher(surf, ox, oy)

        # Draw player astronaut using image frames
        if self.astro_frames:
            frame_index = (self.player_frame // self.astro_anim_speed) % len(self.astro_frames)
            img = self.astro_frames[frame_index]
            if self.facing == -1:
                img = pygame.transform.flip(img, True, False)
            rect = img.get_rect(center=(int(self.px + ox), int(self.py + oy)))
            surf.blit(img, rect)
        else:
            draw_astronaut(surf, int(self.px + ox), int(self.py + oy), self.player_frame, self.facing)

        update_particles(surf)

        self._draw_danger_overlay(surf)
        self._draw_hud(surf)

        # Draw interaction prompt if all parts are collected and player is near the crashed spaceship in sector B4
        if self.all_parts_collected() and self.current_sector() == CRASH_SITE_SECTOR:
            dist_to_ship = math.hypot(self.px - 400, self.py - 330)
            if dist_to_ship < 130:
                pygame.draw.rect(surf, (10, 15, 30, 220), (SCREEN_W // 2 - 180, SCREEN_H - 95, 360, 45), border_radius=6)
                pygame.draw.rect(surf, GOLD, (SCREEN_W // 2 - 180, SCREEN_H - 95, 360, 45), 1, border_radius=6)
                draw_text(surf, "PRESS [E] TO REPAIR & ENTER SHIP", font_small, GOLD, SCREEN_W // 2, SCREEN_H - 73)

        self._draw_sector_title(surf)
        self._draw_flash_message(surf)
        self._draw_scanlines(surf)
        self._draw_transition_overlay(surf)

        # Draw subtle color aberration lines during screen glitch
        if self.glitch_active_frames > 0:
            glitch_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            for _ in range(random.randint(2, 5)):
                gy = random.randint(PLAY_TOP, SCREEN_H - 12)
                gh = random.randint(1, 4)
                color = (0, 255, 255, 80) if random.random() < 0.5 else (255, 0, 128, 80)
                pygame.draw.rect(glitch_surf, color, (0, gy, SCREEN_W, gh))
            surf.blit(glitch_surf, (0, 0))

    def _draw_sector_background(self, surf, ox, oy):
        info = self.sector_info()
        code = info["code"]
        img = self.sector_imgs.get(code)
        if img:
            surf.blit(img, (ox, oy))
        else:
            surf.fill((34, 34, 42))

        # Star strip above playfield / sky feel
        pygame.draw.rect(surf, (4, 4, 12), (0, 0, SCREEN_W, PLAY_TOP))

        # Sector border lines like screen tiles / Faith-ish framing
        pygame.draw.rect(surf, (70, 70, 85), (ox, PLAY_TOP + oy, SCREEN_W, SCREEN_H - PLAY_TOP), 1)

    def _draw_sector_details(self, surf, ox, oy):
        info = self.sector_info()
        theme = info["theme"]

        # Footprints/tracks
        rng = random.Random((self.sector_col + 1) * 123 + (self.sector_row + 1) * 456)
        for _ in range(8):
            x = rng.randint(80, SCREEN_W - 80)
            y = rng.randint(PLAY_TOP + 70, SCREEN_H - 70)
            pygame.draw.ellipse(surf, (55, 55, 65), (x + ox, y + oy, 7, 3))
            pygame.draw.ellipse(surf, (50, 50, 60), (x + 12 + ox, y + 7 + oy, 7, 3))

        # Dynamic lunar surface textures: tiny craters, cracks, and dust layers
        for _ in range(25):
            x = rng.randint(20, SCREEN_W - 20)
            y = rng.randint(PLAY_TOP + 20, SCREEN_H - 20)
            r = rng.randint(2, 6)
            pygame.draw.circle(surf, (45, 45, 55), (x + ox, y + oy), r, 1)
            pygame.draw.circle(surf, (30, 30, 40), (x + ox + 1, y + oy + 1), r - 1, 1)
            
        # Scattered tiny lunar rocks / debris
        for _ in range(12):
            x = rng.randint(30, SCREEN_W - 30)
            y = rng.randint(PLAY_TOP + 30, SCREEN_H - 30)
            size = rng.randint(3, 8)
            pygame.draw.polygon(surf, (60, 60, 75), [
                (x + ox, y + oy),
                (x + size + ox, y - size//2 + oy),
                (x + size + ox, y + size + oy),
                (x - size//2 + ox, y + size + oy)
            ])
            pygame.draw.polygon(surf, (40, 40, 50), [
                (x + ox, y + oy),
                (x + size + ox, y + size + oy),
                (x - size//2 + ox, y + size + oy)
            ], 1)
            
        # Terminal coordinate hud telemetry on the ground
        col, row = self.current_sector()
        code = info["code"]
        draw_text(surf, f"COORD: {col*200:04d}m, {row*200:04d}m", font_tiny, (60, 60, 80), 110, PLAY_TOP + 25, 120)
        draw_text(surf, f"SYS_LOC: SECTOR_{code}_L1", font_tiny, (60, 60, 80), SCREEN_W - 130, SCREEN_H - 25, 120)

    def _draw_obstacles(self, surf, ox, oy):
        for ob in self.sector_info()["obstacles"]:
            self._draw_obstacle(surf, ob, ox, oy)

    def _draw_obstacle(self, surf, ob, ox, oy):
        kind = ob["kind"]
        img_key = OBSTACLE_MAPPING.get(kind, "green_crate")
        img = self.obstacle_imgs.get(img_key)

        shape = self._obstacle_collision_shape(ob)
        size = 300 if img_key == "crashed_ship" else 105 if img_key == "green_crate" else 80

        if isinstance(shape, tuple):
            cx, cy, r = shape
            
            # Draw drop shadow beneath circular/barrel obstacles (not for crashed spaceship)
            if img_key != "crashed_ship":
                shadow_h = size // 5
                shadow_surf = pygame.Surface((size, shadow_h), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, size, shadow_h))
                surf.blit(shadow_surf, (cx - size // 2 + ox, cy + size // 2 - shadow_h + 4 + oy))
            
            if img:
                scaled_img = pygame.transform.smoothscale(img, (size, size))
                surf.blit(scaled_img, (cx - size // 2 + ox, cy - size // 2 + oy))
            else:
                pygame.draw.circle(surf, (150, 150, 50), (cx + ox, cy + oy), r)
        else:
            rect = shape
            
            # Draw drop shadow beneath rectangular/crate obstacles (not for crashed spaceship)
            if img_key != "crashed_ship":
                shadow_h = size // 5
                shadow_surf = pygame.Surface((size, shadow_h), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, size, shadow_h))
                surf.blit(shadow_surf, (rect.x + ox, rect.y + size - shadow_h + 4 + oy))
            
            if img:
                # Check if vertical orientation in design, rotate if so
                orig_rect = rect_from_obstacle(ob)
                draw_img = img
                if orig_rect.h > orig_rect.w and img_key in ["blue_barrel", "green_crate"]:
                    draw_img = pygame.transform.rotate(img, 90)
                scaled_img = pygame.transform.smoothscale(draw_img, (size, size))
                surf.blit(scaled_img, (rect.x + ox, rect.y + oy))
            else:
                pygame.draw.rect(surf, (150, 150, 50), (rect.x + ox, rect.y + oy, rect.w, rect.h))

    def _draw_part(self, surf, ox, oy):
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
        surf.blit(glow, (x - glow_r + ox, y - glow_r + oy))

        # Existing detailed part drawer
        draw_ship_part(surf, x + ox, y + oy, part_type)

        if math.hypot(self.px - x, self.py - y) < 75:
            draw_text(
                surf,
                f"RECOVER {part_name}",
                font_tiny,
                GOLD,
                x + ox,
                y - 45 + oy
            )

    def _draw_watcher(self, surf, ox, oy):
        wx = int(self.watcher_x)
        wy = int(self.watcher_y)

        # 1. Pulsing organic aura backdrop
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.1)
        base_radius = 45 + 15 * pulse
        for r_offset, alpha in [(0, 48), (12, 32), (24, 18), (36, 8)]:
            r = int(base_radius + r_offset)
            aura_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (140, 0, 70, alpha), (r, r), r)
            surf.blit(aura_surf, (wx + ox - r, wy + oy - r))

        # 2. Watcher walk frame animation
        if self.watcher_frames:
            frame_idx = (self.watcher_frame // 6) % len(self.watcher_frames)
            img = self.watcher_frames[frame_idx]
            # Flip relative to player: if player is to left of watcher, face left (flip True)
            if self.px < self.watcher_x:
                img = pygame.transform.flip(img, True, False)
            rect = img.get_rect(center=(wx + ox, wy + oy))
            surf.blit(img, rect)
        else:
            draw_watcher(surf, wx + ox, wy + oy, self.watcher_frame)

    def _draw_danger_overlay(self, surf):
        current = self.current_sector()
        dist = self._sector_distance(self.watcher_sector, current)
        info = self.sector_info()

        is_dark = info.get("danger", 0.1) >= 0.30 or dist <= 1

        if is_dark:
            base_alpha = 165

            if dist == 0:
                w_dist = math.hypot(self.px - self.watcher_x, self.py - self.watcher_y)
                if w_dist < 320:
                    base_alpha = int(lerp(210, 165, clamp(w_dist / 320, 0.0, 1.0)))

            darkness = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            darkness.fill((0, 0, 0, base_alpha))
            surf.blit(darkness, (0, 0))

        if self.watcher_visible:
            d = math.hypot(self.px - self.watcher_x, self.py - self.watcher_y)
            if d < 320:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                alpha = int(clamp((320 - d) / 320 * 120, 0, 120))
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

        pygame.draw.rect(surf, (18, 20, 34), (12, 9, 230, 36), border_radius=8)
        pygame.draw.rect(surf, (90, 90, 120), (12, 9, 230, 36), 1, border_radius=8)

        draw_text_left(surf, "LEVEL 1", font_tiny, (120, 120, 150), 24, 14)

        objective = "RETURN TO CRASH SITE" if self.all_parts_collected() else "RECOVER SHIP PARTS"
        draw_text_left(surf, objective, font_small, MOON_GREY, 24, 27)

        draw_text(
            surf,
            f"SECTOR {info['code']}",
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
        cell = 18
        gap = 3
        pad = 8
        grid_w = MAP_COLS * cell + (MAP_COLS - 1) * gap
        grid_h = MAP_ROWS * cell + (MAP_ROWS - 1) * gap

        box_w = grid_w + pad * 2
        box_h = grid_h + pad * 2
        margin = 12
        box_x = SCREEN_W - box_w - margin
        box_y = SCREEN_H - box_h - margin

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surf.fill((6, 8, 18, 210))
        surf.blit(box_surf, (box_x, box_y))
        pygame.draw.rect(surf, (90, 90, 120), (box_x, box_y, box_w, box_h), 1, border_radius=4)

        draw_text_left(surf, "MAP", font_tiny, (120, 120, 150), box_x + 4, box_y - 14)

        start_x = box_x + pad
        start_y = box_y + pad

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                x = start_x + col * (cell + gap)
                y = start_y + row * (cell + gap)
                sector = (col, row)

                if sector == self.current_sector():
                    colr = CYAN
                elif sector == self.watcher_sector:
                    colr = PURPLE
                elif sector in self.visited_sectors:
                    colr = (80, 80, 100)
                else:
                    colr = (20, 20, 30)

                pygame.draw.rect(surf, colr, (x, y, cell, cell))
                pygame.draw.rect(surf, (120, 120, 150), (x, y, cell, cell), 1)

                if sector == self.current_sector():
                    dot_x = x + int((self.px - PLAY_LEFT) / (PLAY_RIGHT - PLAY_LEFT) * cell)
                    dot_y = y + int((self.py - PLAY_TOP) / (PLAY_BOTTOM - PLAY_TOP) * cell)
                    dot_x = max(x + 1, min(x + cell - 2, dot_x))
                    dot_y = max(y + 1, min(y + cell - 2, dot_y))
                    pygame.draw.circle(surf, WHITE, (dot_x, dot_y), 2)

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

    def _draw_scanlines(self, surf):
        # CRT scanlines (matching Level 3 / Screens)
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 5):
            pygame.draw.line(scan, (255, 255, 255, 7), (0, y), (SCREEN_W, y))
        surf.blit(scan, (0, 0))

    def _draw_jumpscare(self, surf):
        t = self.jumpscare_timer
        scale = self.jumpscare_scale

        surf.fill((0, 0, 0))

        ox, oy = self._apply_shake_offset()

        if scale > 0.01:
            try:
                js_img = pygame.image.load("assets/images/watcher_jumpscare.png").convert_alpha()
            except Exception:
                js_img = js_img = self.jumpscare_img

            if js_img:
                # Scale image up from small to full screen as scale goes 0 -> 1
                target_w = int(SCREEN_W * scale)
                target_h = int(SCREEN_H * scale)

            if target_w > 0 and target_h > 0:
                scaled = pygame.transform.smoothscale(js_img, (target_w, target_h))
                cx = SCREEN_W // 2 + ox - target_w // 2
                cy = SCREEN_H // 2 + oy - target_h // 2
                surf.blit(scaled, (cx, cy))

        if t > 20:
            text_alpha = min(255, (t - 20) * 8)
            pulse = int(220 + 35 * math.sin(t * 0.3))

            draw_text(
                surf,
                "IT FOUND YOU",
                font_huge,
                (pulse, 0, 0),
                SCREEN_W // 2 + ox,
                SCREEN_H - 120 + oy,
                text_alpha
            )

            draw_text(
                surf,
                "THE WATCHER SEES ALL",
                font_med,
                (180, 0, 0),
                SCREEN_W // 2 + ox,
                SCREEN_H - 60 + oy,
                text_alpha
            )

        if t > 80:
            fade_alpha = int((t - 80) / 40 * 255)
            fs = pygame.Surface((SCREEN_W, SCREEN_H))
            fs.fill(BLACK)
            fs.set_alpha(clamp(fade_alpha, 0, 255))
            surf.blit(fs, (0, 0))
