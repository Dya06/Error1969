"""Level 2: ship interior repair tasks + Failed Experiment PNG chase.

Save this as: levels/level2_ship_repair.py
Monster frames expected:
assets/images/monsters/failed_experiment/FE_0.png ... FE_7.png
"""

import os
import math
import random
import pygame

from settings import *
from utils import *
from core.particles import spawn_particles, update_particles

# ─────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────
S2_TS = 32
S2_COLS = 44
S2_ROWS = 30
S2_HUD = 70
S2_VOID = 0
S2_FLOOR = 1
WORLD_W = S2_COLS * S2_TS
WORLD_H = S2_ROWS * S2_TS

FE_FRAME_DIR = "assets/images/monsters/failed_experiment"
FE_FRAME_COUNT = 8
ASTRO_FRAME_DIR = "assets/images/monsters/astronaut"
ASTRO_FRAME_COUNT = 10

# ─────────────────────────────────────────────
# STUN GUN
# ─────────────────────────────────────────────
STUN_GUN_PATH      = "assets/images/Stunt/Stun gun.png"
STUN_ICON_PATH     = "assets/images/Stunt/stun-icon.png"
STUN_GUN_SPAWNS    = 2          # always exactly 2 pickups
STUN_ICON_DURATION = 300        # 5 seconds at 60 fps
STUN_RADIUS        = 38         # pick-up range (pixels, world space)
STUN_SHOOT_RANGE   = 260        # range a stun "shot" carries (world space)
ASTRO3_FRAME_DIR   = "assets/images/monsters/astro3"   # ASTROS0-ASTROS3 shooting frames
ASTRO3_SHOOT_COUNT = 4

# ─────────────────────────────────────────────
# MAP DATA
# ─────────────────────────────────────────────
def _build_ship_map():
    grid = [[S2_VOID] * S2_COLS for _ in range(S2_ROWS)]

    def fill(c0, r0, cw, rh):
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + cw):
                if 0 <= c < S2_COLS and 0 <= r < S2_ROWS:
                    grid[r][c] = S2_FLOOR

    fill(15, 2, 14, 8)
    fill(30, 2, 8, 7)
    fill(38, 4, 5, 5)
    fill(31, 12, 8, 6)
    fill(25, 21, 8, 6)
    fill(10, 21, 8, 6)
    fill(2, 11, 8, 8)
    fill(10, 12, 7, 6)
    fill(18, 12, 8, 7)
    fill(4, 21, 7, 6)
    fill(17, 21, 9, 6)

    fill(19, 10, 4, 3)
    fill(29, 4, 2, 4)
    fill(36, 5, 3, 3)
    fill(39, 8, 2, 6)
    fill(31, 9, 2, 4)
    fill(27, 18, 4, 4)
    fill(19, 19, 2, 3)
    fill(13, 18, 6, 3)
    fill(10, 18, 3, 4)
    fill(4, 18, 7, 3)
    fill(10, 15, 2, 5)
    fill(2, 18, 9, 3)
    fill(25, 16, 7, 3)
    return grid

S2_MAP = _build_ship_map()

S2_ROOMS = [
    {"name": "CAFETERIA",    "rect": (15, 2, 14, 8), "col": (170, 115, 40)},
    {"name": "WEAPONS",      "rect": (30, 2, 8, 7),  "col": (210, 45, 55)},
    {"name": "NAVIGATION",   "rect": (38, 4, 5, 5),  "col": (40, 170, 220)},
    {"name": "SHIELDS",      "rect": (31, 12, 8, 6), "col": (30, 150, 170)},
    {"name": "LOWER ENGINE", "rect": (25, 21, 8, 6), "col": (220, 95, 30)},
    {"name": "UPPER ENGINE", "rect": (10, 21, 8, 6), "col": (220, 95, 30)},
    {"name": "REACTOR",      "rect": (2, 11, 8, 8),  "col": (165, 55, 210)},
    {"name": "SECURITY",     "rect": (10, 12, 7, 6), "col": (35, 135, 120)},
    {"name": "MED-BAY",      "rect": (18, 12, 8, 7), "col": (80, 210, 105)},
    {"name": "ELECTRICAL",   "rect": (4, 21, 7, 6),  "col": (190, 45, 35)},
    {"name": "STORAGE",      "rect": (17, 21, 9, 6), "col": (100, 110, 140)},
]

S2_TASKS_DEF = [
    {"name": "ENGINE CORE",  "desc": "Stabilise main engine output",   "tile": (28, 23), "col": ORANGE,        "kind": "engine"},
    {"name": "NAV MODULE",   "desc": "Recalibrate flight path",         "tile": (40, 6),  "col": CYAN,          "kind": "nav"},
    {"name": "REACTOR CORE", "desc": "Cool unstable reactor",           "tile": (5, 14),  "col": PURPLE,        "kind": "reactor"},
    {"name": "LIFE SUPPORT", "desc": "Restore oxygen circulation",      "tile": (21, 15), "col": (80, 230, 120),"kind": "life"},
    {"name": "COMM ARRAY",   "desc": "Reconnect distress signal",       "tile": (18, 5),  "col": GOLD,          "kind": "comms"},
]

S2_SOLID_OBJECTS = [
    pygame.Rect(18 * S2_TS + 6,  4 * S2_TS + 8,  4 * S2_TS - 12, 1 * S2_TS - 12),
    pygame.Rect(18 * S2_TS + 6,  6 * S2_TS + 8,  4 * S2_TS - 12, 1 * S2_TS - 12),
    pygame.Rect(18 * S2_TS + 6,  8 * S2_TS + 8,  4 * S2_TS - 12, 1 * S2_TS - 12),
    pygame.Rect(31 * S2_TS + 8,  3 * S2_TS + 8,  2 * S2_TS - 16, 2 * S2_TS - 16),
    pygame.Rect(34 * S2_TS + 8,  3 * S2_TS + 8,  2 * S2_TS - 16, 2 * S2_TS - 16),
    pygame.Rect(18 * S2_TS + 8, 22 * S2_TS + 8,  S2_TS - 16,     S2_TS - 16),
    pygame.Rect(20 * S2_TS + 8, 22 * S2_TS + 8,  S2_TS - 16,     S2_TS - 16),
    pygame.Rect(22 * S2_TS + 8, 22 * S2_TS + 8,  S2_TS - 16,     S2_TS - 16),
    pygame.Rect(18 * S2_TS + 8, 24 * S2_TS + 8,  S2_TS - 16,     S2_TS - 16),
    pygame.Rect(21 * S2_TS + 8, 24 * S2_TS + 8,  S2_TS - 16,     S2_TS - 16),
    pygame.Rect(5  * S2_TS + 10,22 * S2_TS + 8,  S2_TS - 20,     2 * S2_TS - 16),
    pygame.Rect(7  * S2_TS + 10,22 * S2_TS + 8,  S2_TS - 20,     2 * S2_TS - 16),
    pygame.Rect(9  * S2_TS + 10,22 * S2_TS + 8,  S2_TS - 20,     2 * S2_TS - 16),
]

def _tile_to_world(tc, tr):
    return tc * S2_TS + S2_TS // 2, tr * S2_TS + S2_TS // 2

def _is_floor_tile(c, r):
    return 0 <= c < S2_COLS and 0 <= r < S2_ROWS and S2_MAP[r][c] == S2_FLOOR

def _compute_solid_tiles():
    blocked = set()
    for solid in S2_SOLID_OBJECTS:
        c0 = solid.left // S2_TS
        c1 = (solid.right - 1) // S2_TS
        r0 = solid.top // S2_TS
        r1 = (solid.bottom - 1) // S2_TS
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                blocked.add((c, r))
    return blocked

S2_SOLID_TILES = _compute_solid_tiles()

def _is_path_tile(c, r):
    return _is_floor_tile(c, r) and (c, r) not in S2_SOLID_TILES

def _blocked_world(x, y, radius=11):
    checks = [
        (-radius, -radius), (radius, -radius),
        (-radius,  radius), (radius,  radius),
        (0, -radius), (0, radius),
        (-radius, 0), (radius, 0),
    ]
    for ox, oy in checks:
        c = int((x + ox) / S2_TS)
        r = int((y + oy) / S2_TS)
        if not _is_floor_tile(c, r):
            return True
    player_rect = pygame.Rect(int(x - radius), int(y - radius), radius * 2, radius * 2)
    for solid in S2_SOLID_OBJECTS:
        if player_rect.colliderect(solid.inflate(-6, -6)):
            return True
    return False

def _bfs_path(sx, sy, gx, gy):
    from collections import deque
    start = (int(sx / S2_TS), int(sy / S2_TS))
    goal  = (int(gx / S2_TS), int(gy / S2_TS))
    if start == goal:
        return []
    q = deque([(start, [start])])
    visited = {start}
    while q:
        (c, r), path = q.popleft()
        for dc, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
            nc, nr = c + dc, r + dr
            if (nc, nr) == goal:
                return path + [(nc, nr)]
            if (nc, nr) not in visited and _is_path_tile(nc, nr):
                visited.add((nc, nr))
                q.append(((nc, nr), path + [(nc, nr)]))
    return []

def _room_at_world(x, y):
    c = int(x / S2_TS)
    r = int(y / S2_TS)
    for room in S2_ROOMS:
        c0, r0, cw, rh = room["rect"]
        if c0 <= c < c0 + cw and r0 <= r < r0 + rh:
            return room
    return {"name": "CORRIDOR", "col": (120, 130, 150)}


class Level2:
    HUD_H = S2_HUD

    def __init__(self):
        self.cam_x = 0.0
        self.cam_y = 0.0

        self.px, self.py = _tile_to_world(21, 5)
        self.px = float(self.px)
        self.py = float(self.py)
        self.player_frame  = 0
        self.facing        = 1
        self.speed         = 2.7
        self.astro_frames      = self._load_astronaut_frames()
        self.astro_anim_speed  = 6
        self.astro_facing      = 1

        self.ex, self.ey = _tile_to_world(5, 15)
        self.ex = float(self.ex)
        self.ey = float(self.ey)
        self.exp_frame       = 0
        self.exp_speed       = 2.55
        self.exp_path        = []
        self.path_timer      = 0
        self.exp_stuck_timer = 0
        self.exp_facing      = 1
        self.fe_frames       = self._load_failed_experiment_frames()
        self.fe_anim_speed   = 5

        self.tasks = []
        for td in S2_TASKS_DEF:
            wx, wy = _tile_to_world(*td["tile"])
            self.tasks.append({
                "name": td["name"], "desc": td["desc"], "kind": td["kind"],
                "col": td["col"], "wx": wx, "wy": wy,
                "progress": 0.0, "done": False,
            })

        self.active_task    = None
        self.player_hp      = 15
        self.player_max     = 15
        self.immune_timer   = 0
        self.flash_msg      = ""
        self.flash_timer    = 0
        self.done           = False
        self.lose           = False
        self.t              = 0
        self.attack_cooldown = 0
        self.room_name_timer = 90
        self.last_room_name  = _room_at_world(self.px, self.py)["name"]
        self._map_surf       = self._render_map()
        self.zoom            = 1.75
        self.view_w          = SCREEN_W / self.zoom
        self.view_h          = (SCREEN_H - self.HUD_H) / self.zoom

        # ── STUN GUN ──────────────────────────────────────────────────
        self.stun_gun_img        = self._load_stun_gun_img()
        self.stun_icon_img       = self._load_stun_icon_img()
        self.astro_shoot_frames  = self._load_astro3_shoot_frames()
        self.shooting_timer      = 0
        self.shooting_anim_speed = 4
        self.stun_pickups        = self._spawn_stun_pickups()
        self.stun_charges        = 0
        self.stun_status         = {"active": False, "timer": 0}
        self.stun_cooldown       = 0

        # ── AUDIO ─────────────────────────────────────────────────────
        self.snd_monster       = load_sound("assets/audio/level2/Level2Monster.mp3")
        self.monster_sound_timer = random.randint(240, 420)
        self.snd_bite          = load_sound("assets/audio/level2/bitesound.wav")
        self.snd_fixing        = [
            load_sound("assets/audio/level2/fixingsound1.wav"),
            load_sound("assets/audio/level2/fixingsound2.wav"),
        ]
        self._fix_channel      = None
        self._fix_sound_index  = 0
        play_music("assets/audio/level2/Level2MapMusic.mp3", loops=-1, volume=0.45)

    # ─────────────────────────────────────────────
    # ASSET LOADERS
    # ─────────────────────────────────────────────
    def _load_failed_experiment_frames(self):
        frames = []
        for i in range(FE_FRAME_COUNT):
            path = os.path.join(FE_FRAME_DIR, f"FE_{i}.png")
            if not os.path.exists(path):
                print(f"[WARNING] Missing Failed Experiment frame: {path}")
                frames.append(self._make_missing_fe_frame(i))
                continue
            img = pygame.image.load(path).convert_alpha()
            frames.append(pygame.transform.scale(img, (62, 62)))
        return frames

    def _load_astronaut_frames(self):
        frames = []
        for i in range(ASTRO_FRAME_COUNT):
            path = os.path.join(ASTRO_FRAME_DIR, f"ASTRO{i}.png")
            if not os.path.exists(path):
                print(f"[WARNING] Missing astronaut frame: {path}")
                frames.append(self._make_missing_astronaut_frame(i))
                continue
            img = pygame.image.load(path).convert_alpha()
            frames.append(pygame.transform.scale(img, (52, 52)))
        return frames

    def _make_missing_astronaut_frame(self, i):
        s = pygame.Surface((42, 42), pygame.SRCALPHA)
        pygame.draw.rect(s, (230, 230, 230), (14, 16, 14, 18))
        pygame.draw.circle(s, (220, 220, 220), (21, 12), 9)
        pygame.draw.rect(s, CYAN, (17, 9, 8, 5))
        draw_text(s, str(i), font_tiny, RED, 21, 34)
        return s

    def _make_missing_fe_frame(self, i):
        s = pygame.Surface((76, 76), pygame.SRCALPHA)
        pygame.draw.circle(s, (90, 0, 0), (38, 38), 28)
        pygame.draw.circle(s, (240, 230, 230), (28, 30), 8)
        pygame.draw.circle(s, (0, 0, 0), (28, 30), 4)
        pygame.draw.line(s, (180, 0, 0), (18, 52), (58, 52), 3)
        draw_text(s, str(i), font_tiny, WHITE, 38, 10)
        return s

    # ── STUN GUN ASSETS ───────────────────────────────────────────────
    @staticmethod
    def _pil_to_pygame(path, size):
        import io as _io
        import numpy as _np
        from PIL import Image as _Pil

        with open(path, "rb") as f:
            raw = f.read()
        pil = _Pil.open(_io.BytesIO(raw)).convert("RGBA")
        arr = _np.array(pil)
        rgb_sum = arr[:, :, 0].astype(int) + arr[:, :, 1].astype(int) + arr[:, :, 2].astype(int)
        arr[:, :, 3] = _np.where(rgb_sum < 60, 0, arr[:, :, 3])
        cleaned = _Pil.fromarray(arr, "RGBA")
        buf = _io.BytesIO()
        cleaned.save(buf, format="PNG")
        buf.seek(0)
        surf = pygame.image.load(buf).convert_alpha()
        return pygame.transform.scale(surf, size)

    def _load_stun_gun_img(self):
        if os.path.exists(STUN_GUN_PATH):
            try:
                return self._pil_to_pygame(STUN_GUN_PATH, (44, 44))
            except Exception as e:
                print(f"[WARNING] Could not load stun gun image: {e}")
        s = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.rect(s, (240, 200, 40), (4, 16, 28, 12))
        pygame.draw.rect(s, (240, 200, 40), (26,  6, 10, 12))
        pygame.draw.rect(s, (200, 160, 20), (4, 16, 28, 12), 1)
        return s

    def _load_stun_icon_img(self):
        if os.path.exists(STUN_ICON_PATH):
            try:
                return self._pil_to_pygame(STUN_ICON_PATH, (90, 70))
            except Exception as e:
                print(f"[WARNING] Could not load stun icon image: {e}")
        s = pygame.Surface((90, 70), pygame.SRCALPHA)
        pygame.draw.polygon(s, (240, 220, 40), [(45,4),(24,40),(38,40),(28,66),(62,28),(46,28)])
        pygame.draw.polygon(s, (255, 255, 100), [(45,4),(24,40),(38,40),(28,66),(62,28),(46,28)], 1)
        return s

    def _load_astro3_shoot_frames(self):
        """Load ASTROS0-ASTROS3 from the astro3 folder (mirrors level 3)."""
        frames = []
        for i in range(ASTRO3_SHOOT_COUNT):
            path = os.path.join(ASTRO3_FRAME_DIR, f"ASTROS{i}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                frames.append(pygame.transform.scale(img, (52, 52)))
            else:
                print(f"[WARNING] Missing astro3 shoot frame: {path}")
                if self.astro_frames:
                    frames.append(self.astro_frames[0])
        return frames

    def _spawn_stun_pickups(self):
        """Pick 2 distinct random floor tiles and place stun gun drops there."""
        candidates = [
            (tc, tr) for tr in range(S2_ROWS)
                     for tc in range(S2_COLS)
                     if S2_MAP[tr][tc] == S2_FLOOR
        ]
        chosen = random.sample(candidates, STUN_GUN_SPAWNS)
        return [{"wx": float(_tile_to_world(tc, tr)[0]),
                 "wy": float(_tile_to_world(tc, tr)[1]),
                 "picked": False}
                for tc, tr in chosen]

    # ─────────────────────────────────────────────
    # STATIC MAP
    # ─────────────────────────────────────────────
    def _render_map(self):
        surf = pygame.Surface((WORLD_W, WORLD_H))
        surf.fill((2, 3, 9))

        void_col   = (2, 3, 9)
        floor_a    = (22, 25, 36)
        floor_b    = (27, 31, 44)
        floor_line = (12, 14, 22)
        wall_dark  = (8, 10, 18)
        wall_mid   = (46, 58, 82)
        wall_hi    = (92, 110, 145)

        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                x = c * S2_TS
                y = r * S2_TS
                if S2_MAP[r][c] == S2_VOID:
                    pygame.draw.rect(surf, void_col, (x, y, S2_TS, S2_TS))
                    continue
                base = floor_a if (c + r) % 2 == 0 else floor_b
                pygame.draw.rect(surf, base, (x, y, S2_TS, S2_TS))
                pygame.draw.rect(surf, (base[0]+5, base[1]+5, base[2]+7), (x+3, y+3, 26, 26))
                pygame.draw.rect(surf, floor_line, (x, y, S2_TS, S2_TS), 1)
                if (c*17 + r*11) % 7 == 0:
                    pygame.draw.rect(surf, (10, 12, 18), (x+7, y+20, 6, 2))
                if (c*13 + r*19) % 11 == 0:
                    pygame.draw.rect(surf, (40, 44, 56), (x+21, y+8, 3, 3))

        for room in S2_ROOMS:
            c0, r0, cw, rh = room["rect"]
            col  = room["col"]
            rect = pygame.Rect(c0*S2_TS, r0*S2_TS, cw*S2_TS, rh*S2_TS)
            tint = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            tint.fill((*col, 18))
            surf.blit(tint, rect.topleft)
            border_dark = tuple(max(0, int(v * 0.30)) for v in col)
            border_mid  = tuple(max(0, int(v * 0.65)) for v in col)
            pygame.draw.rect(surf, border_dark, rect, 4)
            pygame.draw.rect(surf, border_mid, rect.inflate(-6, -6), 2)
            corner = 10
            for cx, cy in [(rect.left, rect.top), (rect.right-corner, rect.top),
                           (rect.left, rect.bottom-corner), (rect.right-corner, rect.bottom-corner)]:
                pygame.draw.rect(surf, col, (cx, cy, corner, corner))
            label    = font_tiny.render(room["name"], False, col)
            label_bg = pygame.Rect(rect.centerx - label.get_width()//2 - 6,
                                   rect.top + 7, label.get_width()+12, label.get_height()+4)
            pygame.draw.rect(surf, (5, 7, 14), label_bg)
            pygame.draw.rect(surf, border_mid, label_bg, 1)
            surf.blit(label, (label_bg.x+6, label_bg.y+2))

        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                if S2_MAP[r][c] != S2_FLOOR:
                    continue
                x = c * S2_TS
                y = r * S2_TS
                for nc, nr, side in [(c, r-1,"top"),(c, r+1,"bottom"),(c-1, r,"left"),(c+1, r,"right")]:
                    if _is_floor_tile(nc, nr):
                        continue
                    if side == "top":
                        pygame.draw.rect(surf, wall_dark, (x, y, S2_TS, 8))
                        pygame.draw.rect(surf, wall_hi,   (x, y, S2_TS, 3))
                        pygame.draw.rect(surf, wall_mid,  (x, y+3, S2_TS, 3))
                    elif side == "bottom":
                        pygame.draw.rect(surf, wall_dark, (x, y+S2_TS-8, S2_TS, 8))
                        pygame.draw.rect(surf, wall_mid,  (x, y+S2_TS-6, S2_TS, 3))
                    elif side == "left":
                        pygame.draw.rect(surf, wall_dark, (x, y, 8, S2_TS))
                        pygame.draw.rect(surf, wall_hi,   (x, y, 3, S2_TS))
                        pygame.draw.rect(surf, wall_mid,  (x+3, y, 3, S2_TS))
                    elif side == "right":
                        pygame.draw.rect(surf, wall_dark, (x+S2_TS-8, y, 8, S2_TS))
                        pygame.draw.rect(surf, wall_mid,  (x+S2_TS-6, y, 3, S2_TS))

        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                if S2_MAP[r][c] == S2_VOID:
                    continue
                x = c * S2_TS
                y = r * S2_TS
                if (c*5 + r*9) % 13 == 0:
                    pygame.draw.rect(surf, (7, 8, 13), (x+4, y+4, 5, 5))

        self._draw_static_decor_to_map(surf)
        return surf

    def _draw_static_decor_to_map(self, surf):
        def tile_rect(tc, tr, cw, rh):
            return pygame.Rect(tc*S2_TS, tr*S2_TS, cw*S2_TS, rh*S2_TS)
        def px_rect(rect, fill, outline=None):
            pygame.draw.rect(surf, fill, rect)
            if outline:
                pygame.draw.rect(surf, outline, rect, 2)

        for tr in [4, 6, 8]:
            rect = tile_rect(18, tr, 4, 1).inflate(-4, -6)
            pygame.draw.rect(surf, (20, 15, 10), rect.move(3, 4))
            px_rect(rect, (82, 58, 34), (175, 130, 70))
            pygame.draw.rect(surf, (120, 86, 48), (rect.x+5, rect.y+4, rect.w-10, 4))
            pygame.draw.rect(surf, (40, 28, 18), (rect.x+5, rect.bottom-6, rect.w-10, 3))
            for cx in [rect.left-13, rect.right+5]:
                pygame.draw.rect(surf, (52, 38, 24), (cx, rect.y+4, 9, 16))
                pygame.draw.rect(surf, (110, 80, 45), (cx, rect.y+4, 9, 16), 1)

        for tc in [31, 34]:
            rect = tile_rect(tc, 3, 2, 2).inflate(-5, -5)
            pygame.draw.rect(surf, (25, 5, 8), rect.move(3, 4))
            px_rect(rect, (72, 16, 20), (190, 45, 50))
            screen = pygame.Rect(rect.x+10, rect.y+8, rect.w-20, 18)
            px_rect(screen, (18, 4, 8), (220, 60, 65))
            pygame.draw.rect(surf, (255, 70, 80), (screen.centerx-2, screen.centery-2, 4, 4))
            for i in range(3):
                pygame.draw.rect(surf, (200, 60, 60), (rect.x+10+i*12, rect.bottom-12, 6, 6))

        rect = tile_rect(39, 5, 3, 2).inflate(-5, -5)
        pygame.draw.rect(surf, (0, 10, 20), rect.move(3, 4))
        px_rect(rect, (5, 35, 70), CYAN)
        screen = pygame.Rect(rect.x+8, rect.y+8, rect.w-16, rect.h-16)
        px_rect(screen, (1, 12, 26), (0, 120, 170))
        for sx, sy in [(screen.x+12,screen.y+8),(screen.x+40,screen.y+18),(screen.x+60,screen.y+9)]:
            pygame.draw.rect(surf, WHITE, (sx, sy, 2, 2))

        for tc in [19, 23]:
            rect = tile_rect(tc, 14, 3, 1).inflate(-4, -5)
            pygame.draw.rect(surf, (5, 20, 18), rect.move(3, 4))
            px_rect(rect, (18, 72, 58), (100, 235, 170))
            pygame.draw.rect(surf, (205, 215, 225), (rect.right-24, rect.y+5, 16, 10))
            pygame.draw.rect(surf, (70, 110, 100), (rect.x+6, rect.y+5, rect.w-36, 6))

        for tc, tr in [(18,22),(20,22),(22,22),(18,24),(21,24)]:
            rect = tile_rect(tc, tr, 1, 1).inflate(-5, -5)
            pygame.draw.rect(surf, (22, 16, 10), rect.move(3, 4))
            px_rect(rect, (74, 55, 34), (150, 110, 65))
            pygame.draw.line(surf, (105, 78, 46), rect.midleft, rect.midright, 2)
            pygame.draw.line(surf, (105, 78, 46), rect.midtop, rect.midbottom, 2)

        for tc in [5, 7, 9]:
            rect = tile_rect(tc, 22, 1, 2).inflate(-5, -5)
            pygame.draw.rect(surf, (20, 16, 2), rect.move(3, 4))
            px_rect(rect, (64, 54, 10), GOLD)
            for j in range(4):
                y = rect.y + 8 + j * 10
                col = GOLD if j % 2 == 0 else (220, 90, 20)
                pygame.draw.rect(surf, col, (rect.x+7, y, rect.w-14, 4))
            pygame.draw.line(surf, (200,30,40),  (rect.right, rect.y+12), (rect.right+16, rect.y+20), 2)
            pygame.draw.line(surf, (40,120,220), (rect.right, rect.y+26), (rect.right+16, rect.y+34), 2)

        for tc in [11, 26]:
            rect = tile_rect(tc, 23, 3, 2).inflate(-4, -4)
            pygame.draw.rect(surf, (20, 10, 5), rect.move(4, 5))
            body   = pygame.Rect(rect.x, rect.y, rect.w-14, rect.h)
            nozzle = pygame.Rect(body.right-2, rect.y+10, 24, rect.h-20)
            px_rect(body, (78, 45, 24), ORANGE)
            px_rect(nozzle, (45, 28, 20), (230, 120, 40))
            pygame.draw.rect(surf, (140,75,35),  (body.x+8, body.y+8, body.w-16, 6))
            pygame.draw.rect(surf, (30, 16, 10), (body.x+8, body.bottom-14, body.w-16, 6))

        rect = tile_rect(4, 13, 3, 3).inflate(-5, -5)
        pygame.draw.rect(surf, (18, 4, 24), rect.move(4, 5))
        px_rect(rect, (58, 15, 70), PURPLE)
        core = pygame.Rect(rect.centerx-16, rect.centery-16, 32, 32)
        px_rect(core, (30, 0, 45), (190, 70, 220))
        pygame.draw.rect(surf, (230, 120, 255), (core.centerx-5, core.centery-5, 10, 10))

        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                if S2_MAP[r][c] != S2_FLOOR:
                    continue
                x    = c * S2_TS
                y    = r * S2_TS
                seed = c * 31 + r * 17
                if seed % 19 == 0:
                    pygame.draw.rect(surf, (8, 10, 16), (x+6, y+24, 10, 3))
                if seed % 23 == 0:
                    pygame.draw.rect(surf, (45, 48, 60), (x+20, y+6, 4, 4))
                if seed % 29 == 0:
                    pygame.draw.line(surf, (12, 14, 22), (x+5, y+5), (x+17, y+9), 1)

        for start, end, col in [
            ((20,15),(22,16),(120,15,25)), ((33,6),(35,7),(120,15,25)),
            ((7,23),(9,24),(110,20,20)),   ((23,16),(25,16),(95,20,30)),
        ]:
            x1,y1 = _tile_to_world(*start)
            x2,y2 = _tile_to_world(*end)
            pygame.draw.line(surf, col, (x1,y1), (x2,y2), 3)
            for i in range(4):
                px = x1+(x2-x1)*i//4
                py = y1+(y2-y1)*i//4
                pygame.draw.rect(surf, col, (px, py, 5, 3))

        for tc, tr in [(16,7),(24,5),(32,8),(36,14),(6,17),(12,15),(20,24),(28,26),(41,7),(8,25),(23,13)]:
            x = tc*S2_TS; y = tr*S2_TS
            pygame.draw.rect(surf, (35,38,48), (x+7, y+9, 12, 5))
            pygame.draw.rect(surf, (70,75,90), (x+9, y+18, 7, 4))
            pygame.draw.line(surf, (10,12,18), (x+5,y+24), (x+21,y+27), 1)

        for tc, tr in [(31,4),(39,6),(21,15),(5,22),(18,5)]:
            x = tc*S2_TS; y = tr*S2_TS
            pygame.draw.rect(surf, (8,8,12),    (x+6, y+6, 20, 18))
            pygame.draw.rect(surf, (180,30,40), (x+6, y+6, 20, 18), 1)
            pygame.draw.rect(surf, (220,70,80), (x+11, y+12, 3, 3))
            pygame.draw.rect(surf, (220,70,80), (x+18, y+16, 3, 3))

        for tc, tr, kind in [
            (12,14,"cable"),(14,16,"panel"),(11,13,"scratch"),
            (23,4,"scratch"),(25,7,"panel"),(16,5,"cable"),
            (32,6,"sparks"),(36,7,"scratch"),
            (41,7,"panel"),(40,5,"cable"),
            (34,14,"scratch"),(36,16,"panel"),
            (20,16,"cable"),(24,17,"stain"),
            (19,25,"scratch"),(23,23,"panel"),
            (6,25,"sparks"),(8,24,"cable"),
        ]:
            x = tc*S2_TS; y = tr*S2_TS
            if kind == "cable":
                pygame.draw.line(surf,(55,20,20),(x+4,y+18),(x+28,y+12),2)
                pygame.draw.line(surf,(20,45,80),(x+6,y+22),(x+26,y+24),2)
            elif kind == "panel":
                pygame.draw.rect(surf,(18,20,28),(x+7,y+8,18,14))
                pygame.draw.rect(surf,(55,65,80),(x+7,y+8,18,14),1)
                pygame.draw.rect(surf,(120,25,25),(x+11,y+12,4,4))
            elif kind == "scratch":
                pygame.draw.line(surf,(10,12,18),(x+6,y+9),(x+24,y+16),1)
                pygame.draw.line(surf,(35,35,45),(x+10,y+20),(x+26,y+22),1)
            elif kind == "sparks":
                pygame.draw.rect(surf,(220,70,40),(x+12,y+10,3,3))
                pygame.draw.rect(surf,(255,180,40),(x+20,y+15,2,2))
                pygame.draw.line(surf,(180,40,20),(x+8,y+22),(x+25,y+26),1)
            elif kind == "stain":
                pygame.draw.rect(surf,(55,20,25),(x+8,y+15,12,4))
                pygame.draw.rect(surf,(35,10,15),(x+14,y+20,8,3))

    # ─────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.done = True

    def update(self):
        self.t           += 1
        self.player_frame += 1
        self.exp_frame    += 1
        if self.flash_timer   > 0: self.flash_timer   -= 1
        if self.immune_timer  > 0: self.immune_timer  -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.room_name_timer > 0: self.room_name_timer -= 1
        if self.shooting_timer  > 0: self.shooting_timer  -= 1
        if self.stun_cooldown   > 0: self.stun_cooldown   -= 1
        if self.stun_status["active"]:
            self.stun_status["timer"] -= 1
            if self.stun_status["timer"] <= 0:
                self.stun_status["active"] = False

        self._update_player()
        self._update_camera()
        self._update_room_name()
        self._update_task_interaction()
        self._update_experiment()
        self._update_stun_gun()
        self._update_monster_sound()

        if all(t["done"] for t in self.tasks):
            self.flash_msg   = "SHIP SYSTEMS RESTORED!"
            self.flash_timer = 90
            self.done        = True
            stop_music(fade_ms=400)

    def _update_monster_sound(self):
        self.monster_sound_timer -= 1
        if self.monster_sound_timer <= 0:
            if self.snd_monster:
                self.snd_monster.play()
            self.monster_sound_timer = random.randint(420, 720)

    def _update_player(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        if dx and dy:
            dx *= 0.707; dy *= 0.707
        if dx:
            self.facing      = dx
            self.astro_facing = 1 if dx > 0 else -1
        speed = self.speed
        if self.active_task is not None and keys[pygame.K_e]:
            speed *= 0.35
        self.px, self.py = self._move(self.px, self.py, dx*speed, dy*speed)

    def _move(self, x, y, dx, dy, radius=11):
        nx = x + dx
        if not _blocked_world(nx, y, radius): x = nx
        ny = y + dy
        if not _blocked_world(x, ny, radius): y = ny
        return x, y

    def _update_camera(self):
        self.cam_x += (self.px - self.view_w/2 - self.cam_x) * 0.12
        self.cam_y += (self.py - self.view_h/2 - self.cam_y) * 0.12
        self.cam_x = clamp(self.cam_x, 0, max(0, WORLD_W - self.view_w))
        self.cam_y = clamp(self.cam_y, 0, max(0, WORLD_H - self.view_h))

    def _update_room_name(self):
        room_name = _room_at_world(self.px, self.py)["name"]
        if room_name != self.last_room_name:
            self.last_room_name  = room_name
            self.room_name_timer = 90

    def _update_task_interaction(self):
        keys = pygame.key.get_pressed()
        self.active_task = None
        holding_fix = False
        for task in self.tasks:
            if task["done"]: continue
            d = math.hypot(self.px - task["wx"], self.py - task["wy"])
            if d < 42:
                self.active_task = task
                if keys[pygame.K_e]:
                    holding_fix = True
                    task["progress"] = min(100, task["progress"] + 0.55)
                    if task["progress"] >= 100:
                        task["done"] = True
                        self.flash_msg   = f"{task['name']} REPAIRED!"
                        self.flash_timer = 100
                        sx, sy = self._world_to_screen(task["wx"], task["wy"])
                        spawn_particles(sx, sy, task["col"], 24, 3, 55)
                        self.exp_speed = 2.55 + self._repaired_count() * 0.22
                break
        self._update_fixing_sound(holding_fix)

    def _update_fixing_sound(self, holding):
        if holding:
            if self._fix_channel is None or not self._fix_channel.get_busy():
                snd = self.snd_fixing[self._fix_sound_index]
                if snd:
                    self._fix_channel = snd.play()
                self._fix_sound_index = 1 - self._fix_sound_index
        elif self._fix_channel is not None:
            self._fix_channel.stop()
            self._fix_channel      = None
            self._fix_sound_index  = 0

    def _update_experiment(self):
        self.path_timer += 1
        repaired = self._repaired_count()
        refresh  = max(10, 22 - repaired * 2)
        if self.path_timer >= refresh:
            self.path_timer = 0
            self.exp_path   = _bfs_path(self.ex, self.ey, self.px, self.py)

        if self.exp_path:
            tc, tr = self.exp_path[0]
            tx, ty = _tile_to_world(tc, tr)
            dx   = tx - self.ex
            dy   = ty - self.ey
            dist = math.hypot(dx, dy)
            if dist < self.exp_speed + 1:
                self.exp_path.pop(0)
            elif dist > 0:
                # Freeze completely while stunned
                stun_mult = 0.0 if self.stun_status["active"] else 1.0
                move_x = (dx / dist) * self.exp_speed * stun_mult
                move_y = (dy / dist) * self.exp_speed * stun_mult

                new_x, new_y = self._move(self.ex, self.ey, move_x, move_y, radius=12)
                progress = math.hypot(new_x - self.ex, new_y - self.ey)
                self.ex, self.ey = new_x, new_y

                if progress < 0.3:
                    self.exp_stuck_timer += 1
                    if self.exp_stuck_timer > 6:
                        self.exp_stuck_timer = 0
                        if self.exp_path: self.exp_path.pop(0)
                        self.path_timer = refresh
                else:
                    self.exp_stuck_timer = 0

                if abs(move_x) > 0.1:
                    self.exp_facing = 1 if move_x > 0 else -1

        dist_to_player = math.hypot(self.px - self.ex, self.py - self.ey)
        if dist_to_player < 34 and self.attack_cooldown <= 0 and not self.stun_status["active"]:
            if self.snd_bite: self.snd_bite.play()
            self.player_hp   -= 4
            self.immune_timer = 75
            self.attack_cooldown = 80
            self.flash_msg   = "FAILED EXPERIMENT IS ATTACKING!"
            self.flash_timer = 65
            sx, sy = self._world_to_screen(self.px, self.py)
            spawn_particles(sx, sy, BLOOD_RED, 14, 3, 40)
            if self.player_hp <= 0:
                self.lose = True
                stop_music(fade_ms=400)
                if self.snd_bite: self.snd_bite.stop()

    def _update_stun_gun(self):
        """Pick up stun guns on the floor and fire with [F]."""
        keys = pygame.key.get_pressed()

        # ── Pick up ───────────────────────────────────────────────────
        for pickup in self.stun_pickups:
            if pickup["picked"]: continue
            d = math.hypot(self.px - pickup["wx"], self.py - pickup["wy"])
            if d < STUN_RADIUS:
                pickup["picked"]  = True
                self.stun_charges += 1
                self.flash_msg    = "STUN GUN PICKED UP!  [F] TO FIRE"
                self.flash_timer  = 90
                sx, sy = self._world_to_screen(pickup["wx"], pickup["wy"])
                spawn_particles(sx, sy, (240, 200, 40), 18, 3, 50)

        # ── Fire ──────────────────────────────────────────────────────
        if keys[pygame.K_f] and self.stun_charges > 0 and self.stun_cooldown <= 0:
            self.stun_charges  -= 1
            self.stun_cooldown  = 45
            self.shooting_timer = self.shooting_anim_speed * ASTRO3_SHOOT_COUNT

            d = math.hypot(self.px - self.ex, self.py - self.ey)
            if d <= STUN_SHOOT_RANGE:
                self.stun_status["active"] = True
                self.stun_status["timer"]  = STUN_ICON_DURATION
                self.flash_msg   = "MONSTER STUNNED!"
                self.flash_timer = 80
                sx, sy = self._world_to_screen(self.ex, self.ey)
                spawn_particles(sx, sy, (240, 220, 40), 22, 3, 55)
            else:
                self.flash_msg   = "MISSED – OUT OF RANGE"
                self.flash_timer = 60

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────
    def _repaired_count(self):
        return sum(1 for t in self.tasks if t["done"])

    def _world_to_view(self, wx, wy):
        return int(wx - self.cam_x), int(wy - self.cam_y)

    def _world_to_screen(self, wx, wy):
        vx, vy = self._world_to_view(wx, wy)
        return int(vx * self.zoom), int(vy * self.zoom) + self.HUD_H

    # ─────────────────────────────────────────────
    # DRAWING
    # ─────────────────────────────────────────────
    def draw(self, surf):
        game_h    = SCREEN_H - self.HUD_H
        view_surf = pygame.Surface((int(self.view_w), int(self.view_h)))
        view_rect = pygame.Rect(int(self.cam_x), int(self.cam_y), int(self.view_w), int(self.view_h))
        view_surf.blit(self._map_surf, (0, 0), area=view_rect)

        self._draw_dynamic_room_lights(view_surf)
        self._draw_tasks(view_surf)
        self._draw_stun_pickups(view_surf)       # ← gun drops on floor
        self._draw_failed_experiment(view_surf)  # ← includes stun icon
        self._draw_player(view_surf)

        zoomed_view = pygame.transform.scale(view_surf, (SCREEN_W, game_h))
        surf.blit(zoomed_view, (0, self.HUD_H))

        update_particles(surf)
        self._draw_horror_lighting(surf)
        self._draw_hud(surf)
        self._draw_room_overlay(surf)
        self._draw_task_prompt(surf)
        self._draw_flash_message(surf)

    def _draw_dynamic_room_lights(self, surf):
        sw, sh = surf.get_width(), surf.get_height()
        if (self.t // 45) % 2 == 0:
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((40, 0, 0, 18))
            surf.blit(overlay, (0, 0))
        rx, ry = _tile_to_world(5, 14)
        vx, vy = self._world_to_view(rx, ry)
        glow_size = int(70 + 10 * math.sin(self.t * 0.08))
        gs = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (150, 0, 210, 55), (glow_size, glow_size), glow_size)
        surf.blit(gs, (vx-glow_size, vy-glow_size))
        for tx, ty in [(12, 24), (28, 24)]:
            wx, wy = _tile_to_world(tx, ty)
            vx, vy = self._world_to_view(wx, wy)
            pygame.draw.circle(surf, (255, 120, 35), (vx, vy), 6+int(3*math.sin(self.t*0.12)))

    def _draw_tasks(self, surf):
        for task in self.tasks:
            vx, vy = self._world_to_view(task["wx"], task["wy"])
            if not (-80 < vx < surf.get_width()+80 and -80 < vy < surf.get_height()+80):
                continue
            self._draw_task_panel(surf, vx, vy, task)

    def _draw_task_panel(self, surf, x, y, task):
        col      = task["col"]
        done     = task["done"]
        progress = task["progress"]

        glow_r = 34 if not done else 24
        gs = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*col, 80 if not done else 45), (glow_r, glow_r), glow_r)
        surf.blit(gs, (x-glow_r, y-glow_r))

        w, h = 68, 52
        bg   = (8, 35, 20) if done else (35, 12, 14)
        rect = pygame.Rect(x-w//2, y-h//2, w, h)
        pygame.draw.rect(surf, bg, rect, border_radius=8)
        pygame.draw.rect(surf, col, rect, 2, border_radius=8)

        kind = task["kind"]
        if kind == "engine":
            for i in range(3):
                px = x - 16 + i * 16
                pygame.draw.rect(surf, (85,50,20), (px-4, y-16, 8, 22))
                pygame.draw.rect(surf, col, (px-4, y-16, 8, 22), 1)
            pygame.draw.line(surf, col, (x-20, y+8), (x+20, y+8), 2)
        elif kind == "nav":
            screen_rect = pygame.Rect(x-20, y-18, 40, 26)
            pygame.draw.rect(surf, (2,10,20), screen_rect)
            pygame.draw.rect(surf, col, screen_rect, 2)
            pygame.draw.rect(surf, (0,180,220), (x-12, y-10, 3, 3))
            pygame.draw.rect(surf, (0,180,220), (x+4,  y-5,  3, 3))
            pygame.draw.rect(surf, (0,180,220), (x+13, y-13, 2, 2))
            pygame.draw.line(surf, col, (x-11, y-9), (x+5, y-4), 1)
            pygame.draw.line(surf, col, (x+5, y-4), (x+14, y-12), 1)
            if self.t % 40 < 20:
                pygame.draw.rect(surf, WHITE, (x-16, y+5, 5, 3))
        elif kind == "reactor":
            pulse = int(100 + 60 * math.sin(self.t * 0.12))
            pygame.draw.circle(surf, (pulse, 0, 160), (x, y-3), 16)
            pygame.draw.circle(surf, col, (x, y-3), 16, 2)
        elif kind == "life":
            pygame.draw.rect(surf, (20,80,35), (x-8, y-18, 16, 28), border_radius=6)
            pygame.draw.rect(surf, col, (x-8, y-18, 16, 28), 2, border_radius=6)
            draw_text(surf, "O2", font_tiny, col, x, y-4)
        elif kind == "comms":
            points = [(x-18,y+8),(x-10,y-10),(x,y-18),(x+10,y-10),(x+18,y+8)]
            pygame.draw.polygon(surf, (80,65,10), points)
            pygame.draw.polygon(surf, col, points, 2)

        bar_w = w - 14
        pygame.draw.rect(surf, (8,8,12), (x-bar_w//2, y+18, bar_w, 6), border_radius=3)
        pygame.draw.rect(surf, col, (x-bar_w//2, y+18, int(bar_w*progress/100), 6), border_radius=3)
        if done:
            draw_text(surf, "DONE", font_tiny, (80, 230, 110), x, y+31)

    def _draw_stun_pickups(self, surf):
        """Draw stun gun drops on the floor with a glowing halo."""
        for pickup in self.stun_pickups:
            if pickup["picked"]: continue
            vx, vy = self._world_to_view(pickup["wx"], pickup["wy"])
            if not (-60 < vx < surf.get_width()+60 and -60 < vy < surf.get_height()+60):
                continue
            # Pulsing glow
            glow_r = 20 + int(5 * math.sin(self.t * 0.12))
            gs = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (240, 200, 40, 65), (glow_r, glow_r), glow_r)
            surf.blit(gs, (vx-glow_r, vy-glow_r))
            # Gun sprite (your actual image)
            rect = self.stun_gun_img.get_rect(center=(vx, vy))
            surf.blit(self.stun_gun_img, rect)
            # Pick-up prompt
            draw_text(surf, "[F] STUN GUN", font_tiny, (240, 200, 40), vx, vy - 28)

    def _draw_failed_experiment(self, surf):
        vx, vy = self._world_to_view(self.ex, self.ey)
        if not (-100 < vx < surf.get_width()+100 and -100 < vy < surf.get_height()+100):
            return
        d          = math.hypot(self.px - self.ex, self.py - self.ey)
        frame_index = (self.exp_frame // self.fe_anim_speed) % len(self.fe_frames)
        img         = self.fe_frames[frame_index]
        if self.exp_facing == -1:
            img = pygame.transform.flip(img, True, False)
        rect = img.get_rect(center=(vx, vy))
        if self.t % 12 < 4:
            ghost = img.copy()
            ghost.fill((180, 0, 40, 90), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(ghost, rect.move(-3, 0))
            surf.blit(ghost, rect.move(3, 0))
        surf.blit(img, rect)

        # Stun icon (your actual image — already has "STUNNED" text baked in)
        if self.stun_status["active"]:
            icon_rect = self.stun_icon_img.get_rect(center=(vx, vy - 68))
            surf.blit(self.stun_icon_img, icon_rect)

        if d < 150:
            draw_text(surf, "FAILED EXPERIMENT", font_tiny, BLOOD_RED, vx, vy - 38)

    def _draw_player(self, surf):
        vx, vy = self._world_to_view(self.px, self.py)
        if self.immune_timer > 0 and self.immune_timer % 8 >= 4:
            return

        # Shooting animation (level-3 ASTROS frames) takes priority
        if self.shooting_timer > 0 and self.astro_shoot_frames:
            frame_index = (
                (self.shooting_anim_speed * ASTRO3_SHOOT_COUNT - self.shooting_timer)
                // self.shooting_anim_speed
            )
            frame_index = max(0, min(frame_index, len(self.astro_shoot_frames) - 1))
            img = self.astro_shoot_frames[int(frame_index)]
        else:
            frame_index = (self.player_frame // self.astro_anim_speed) % len(self.astro_frames)
            img = self.astro_frames[frame_index]

        if self.astro_facing == -1:
            img = pygame.transform.flip(img, True, False)
        rect = img.get_rect(center=(vx, vy))
        surf.blit(img, rect)

    def _draw_horror_lighting(self, surf):
        darkness = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        darkness.fill((0, 0, 0, 195))
        psx, psy = self._world_to_screen(self.px, self.py)
        light_radius = 145
        for radius, alpha in [(light_radius,0),(light_radius+35,65),(light_radius+70,125)]:
            pygame.draw.circle(darkness, (0,0,0,alpha), (psx, psy), radius)
        surf.blit(darkness, (0, 0))

        d = math.hypot(self.px - self.ex, self.py - self.ey)
        if d < 210:
            alpha  = int(clamp((210-d)/210*120, 0, 120))
            danger = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            danger.fill((130, 0, 0, alpha))
            surf.blit(danger, (0, 0))
            pulse = int(210 + 45 * math.sin(self.t * 0.22))
            draw_text(surf, "FE SIGNAL CLOSE", font_med, (pulse,35,35), SCREEN_W//2, SCREEN_H-80)

        if self.t % 9 == 0:
            static = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            for _ in range(90):
                x = random.randint(0, SCREEN_W-1)
                y = random.randint(self.HUD_H, SCREEN_H-1)
                s = random.randint(80, 160)
                static.set_at((x, y), (s, s, s, 35))
            surf.blit(static, (0, 0))

        if self.t % 120 < 8:
            flicker = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flicker.fill((255, 0, 0, 30))
            surf.blit(flicker, (0, 0))

    def _draw_hud(self, surf):
        hud_h    = self.HUD_H
        room     = _room_at_world(self.px, self.py)
        repaired = self._repaired_count()
        total    = len(self.tasks)
        d        = math.hypot(self.px - self.ex, self.py - self.ey)
        danger_near = d < 210

        BG        = (3, 4, 8)
        LINE      = (90, 18, 14)
        RED       = (235, 55, 35)
        RED_DIM   = (120, 28, 22)
        ORANGE    = (255, 125, 20)
        GREEN     = (0, 235, 80)
        GREEN_DIM = (0, 110, 45)
        DIM       = (110, 55, 45)
        STUN_COL  = (240, 200, 40)
        STUN_DIM  = (80, 65, 10)

        pygame.draw.rect(surf, BG, (0, 0, SCREEN_W, hud_h))
        pygame.draw.line(surf, LINE, (0, hud_h-1), (SCREEN_W, hud_h-1), 1)
        for y in range(2, hud_h, 5):
            pygame.draw.line(surf, (16, 4, 4), (0, y), (SCREEN_W, y), 1)

        margin  = 16
        left_w  = 150
        right_w = 170
        left_x  = margin
        center_x = SCREEN_W // 2
        right_x  = SCREEN_W - right_w - margin

        pygame.draw.line(surf, LINE, (left_w+25, 6), (left_w+25, hud_h-12), 1)
        pygame.draw.line(surf, LINE, (right_x-18, 6), (right_x-18, hud_h-12), 1)

        # LEFT
        draw_text_left(surf, "MISSION",     font_tiny,  DIM, left_x, 12)
        draw_text_left(surf, "REPAIR SHIP", font_small, RED, left_x, 30)

        # CENTER
        room_col = RED if danger_near and self.t % 30 < 16 else ORANGE
        draw_text(surf, room["name"].upper(), font_small, room_col, center_x, 17)
        draw_text(surf, "SYSTEM FAILURE",     font_tiny,  RED_DIM,  center_x, 35)

        # RIGHT: suit HP
        draw_text_left(surf, "SUIT", font_tiny, GREEN_DIM, right_x, 10)
        draw_text(surf, f"{self.player_hp}/{self.player_max}", font_small,
                  GREEN if not danger_near else RED, right_x+105, 26)
        hp_bar_x = right_x; hp_bar_y = 34; hp_bar_w = 90; hp_bar_h = 7
        pygame.draw.rect(surf, (5,20,8),    (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h))
        pygame.draw.rect(surf, GREEN_DIM,   (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h), 1)
        hp_fill = int(hp_bar_w * self.player_hp / self.player_max)
        if hp_fill > 0:
            pygame.draw.rect(surf, GREEN if not danger_near else RED,
                             (hp_bar_x, hp_bar_y, hp_fill, hp_bar_h))

        # RIGHT: stun charge pips
        draw_text_left(surf, "STUN", font_tiny, STUN_DIM, right_x, 46)
        for i in range(STUN_GUN_SPAWNS):
            pip_col = STUN_COL if i < self.stun_charges else STUN_DIM
            pygame.draw.rect(surf, pip_col,  (right_x + 36 + i*16, 46, 12, 8))
            pygame.draw.rect(surf, STUN_COL, (right_x + 36 + i*16, 46, 12, 8), 1)
        if self.stun_charges > 0:
            draw_text_left(surf, "[F] FIRE", font_tiny, STUN_COL, right_x+68, 46)

        # BOTTOM: repair progress strip
        strip_y = hud_h - 10; strip_h = 6
        pygame.draw.rect(surf, (18,4,3), (0, strip_y, SCREEN_W, strip_h))
        fill_w = int(SCREEN_W * repaired / total)
        if fill_w > 0:
            pygame.draw.rect(surf, ORANGE, (0, strip_y, fill_w, strip_h))
        pip_w = 34; pip_h = 6; gap = 6
        pip_start = SCREEN_W//2 - (total*pip_w+(total-1)*gap)//2
        for i in range(total):
            pip_rect = pygame.Rect(pip_start+i*(pip_w+gap), strip_y, pip_w, pip_h)
            pygame.draw.rect(surf, (35,8,5), pip_rect)
            if i < repaired:
                pygame.draw.rect(surf, ORANGE, pip_rect)
            pygame.draw.rect(surf, RED_DIM, pip_rect, 1)
        draw_text(surf, f"REPAIRS {repaired}/{total}", font_tiny, ORANGE, center_x, hud_h-20)

    def _draw_room_overlay(self, surf):
        if self.room_name_timer <= 0: return
        alpha = min(210, self.room_name_timer * 4)
        room  = _room_at_world(self.px, self.py)
        draw_text(surf, room["name"], font_large, room["col"], SCREEN_W//2, SCREEN_H//2-130, alpha)

    def _draw_task_prompt(self, surf):
        if self.active_task is None: return
        task    = self.active_task
        panel_h = 72
        panel_y = SCREEN_H - panel_h
        pygame.draw.rect(surf, (3,6,12), (0, panel_y, SCREEN_W, panel_h))
        pygame.draw.line(surf, task["col"], (0, panel_y), (SCREEN_W, panel_y), 2)
        for y in range(panel_y+2, SCREEN_H, 4):
            pygame.draw.line(surf, (15,15,15), (0, y), (SCREEN_W, y), 1)
        draw_text(surf, f"HOLD [E] TO REPAIR: {task['name']}", font_med, task["col"], SCREEN_W//2, panel_y+18)
        draw_text(surf, task["desc"].upper(), font_small, (160,160,160), SCREEN_W//2, panel_y+38)
        bar_w = 320; bar_h = 10
        bx = SCREEN_W//2 - bar_w//2; by = panel_y+52
        pygame.draw.rect(surf, (12,8,8),   (bx, by, bar_w, bar_h))
        pygame.draw.rect(surf, (100,20,20),(bx, by, bar_w, bar_h), 1)
        fill = int(bar_w * task["progress"] / 100)
        if fill > 0:
            pygame.draw.rect(surf, task["col"], (bx, by, fill, bar_h))

    def _draw_flash_message(self, surf):
        if self.flash_timer <= 0: return
        alpha = min(255, self.flash_timer * 4)
        draw_text(surf, self.flash_msg, font_med, CYAN, SCREEN_W//2, SCREEN_H//2-60, alpha)