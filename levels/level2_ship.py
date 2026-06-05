"""Level 2: ship interior repair tasks + Failed Experiment PNG chase.

Save this as: levels/level2_ship_repair.py
Monster frames expected:
assets/images/monsters/failed_experiment/FE_0.png ... FE_7.png
"""

import os
import math
import pygame

from settings import *
from utils import *
from core.particles import spawn_particles, update_particles
from graphics.sprites import draw_astronaut

# ─────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────
S2_TS = 32
S2_COLS = 44
S2_ROWS = 30
S2_HUD = 58
S2_VOID = 0
S2_FLOOR = 1
WORLD_W = S2_COLS * S2_TS
WORLD_H = S2_ROWS * S2_TS

FE_FRAME_DIR = "assets/images/monsters/failed_experiment"
FE_FRAME_COUNT = 8

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

    # Rooms - Among Us inspired but original layout
    fill(15, 2, 14, 8)    # Cafeteria
    fill(30, 2, 8, 7)     # Weapons
    fill(38, 4, 5, 5)     # Navigation
    fill(31, 12, 8, 6)    # Shields
    fill(25, 21, 8, 6)    # Lower Engine
    fill(10, 21, 8, 6)    # Upper Engine
    fill(2, 11, 8, 8)     # Reactor
    fill(10, 12, 7, 6)    # Security
    fill(18, 12, 8, 7)    # Med-Bay
    fill(4, 21, 7, 6)     # Electrical
    fill(17, 21, 9, 6)    # Storage

    # Corridors
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
    {"name": "CAFETERIA", "rect": (15, 2, 14, 8), "col": (180, 135, 55)},
    {"name": "WEAPONS", "rect": (30, 2, 8, 7), "col": (200, 55, 55)},
    {"name": "NAVIGATION", "rect": (38, 4, 5, 5), "col": (55, 150, 230)},
    {"name": "SHIELDS", "rect": (31, 12, 8, 6), "col": (55, 210, 210)},
    {"name": "LOWER ENGINE", "rect": (25, 21, 8, 6), "col": (230, 120, 40)},
    {"name": "UPPER ENGINE", "rect": (10, 21, 8, 6), "col": (230, 120, 40)},
    {"name": "REACTOR", "rect": (2, 11, 8, 8), "col": (185, 70, 210)},
    {"name": "SECURITY", "rect": (10, 12, 7, 6), "col": (70, 200, 90)},
    {"name": "MED-BAY", "rect": (18, 12, 8, 7), "col": (80, 230, 140)},
    {"name": "ELECTRICAL", "rect": (4, 21, 7, 6), "col": (230, 200, 55)},
    {"name": "STORAGE", "rect": (17, 21, 9, 6), "col": (120, 130, 165)},
]

S2_TASKS_DEF = [
    {"name": "ENGINE CORE", "desc": "Stabilise main engine output", "tile": (28, 23), "col": ORANGE, "kind": "engine"},
    {"name": "NAV MODULE", "desc": "Recalibrate flight path", "tile": (40, 6), "col": CYAN, "kind": "nav"},
    {"name": "REACTOR CORE", "desc": "Cool unstable reactor", "tile": (5, 14), "col": PURPLE, "kind": "reactor"},
    {"name": "LIFE SUPPORT", "desc": "Restore oxygen circulation", "tile": (21, 15), "col": (80, 230, 120), "kind": "life"},
    {"name": "COMM ARRAY", "desc": "Reconnect distress signal", "tile": (18, 5), "col": GOLD, "kind": "comms"},
]

def _tile_to_world(tc, tr):
    return tc * S2_TS + S2_TS // 2, tr * S2_TS + S2_TS // 2

def _is_floor_tile(c, r):
    return 0 <= c < S2_COLS and 0 <= r < S2_ROWS and S2_MAP[r][c] == S2_FLOOR

def _blocked_world(x, y, radius=11):
    checks = [(-radius, -radius), (radius, -radius), (-radius, radius), (radius, radius),
              (0, -radius), (0, radius), (-radius, 0), (radius, 0)]
    for ox, oy in checks:
        c = int((x + ox) / S2_TS)
        r = int((y + oy) / S2_TS)
        if not _is_floor_tile(c, r):
            return True
    return False

def _bfs_path(sx, sy, gx, gy):
    from collections import deque
    start = (int(sx / S2_TS), int(sy / S2_TS))
    goal = (int(gx / S2_TS), int(gy / S2_TS))
    if start == goal:
        return []
    q = deque([(start, [start])])
    visited = {start}
    while q:
        (c, r), path = q.popleft()
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nc, nr = c + dc, r + dr
            if (nc, nr) == goal:
                return path + [(nc, nr)]
            if (nc, nr) not in visited and _is_floor_tile(nc, nr):
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
        self.player_frame = 0
        self.facing = 1
        self.speed = 2.7

        self.ex, self.ey = _tile_to_world(5, 15)
        self.ex = float(self.ex)
        self.ey = float(self.ey)
        self.exp_frame = 0
        self.exp_speed = 2.55
        self.exp_path = []
        self.path_timer = 0
        self.fe_frames = self._load_failed_experiment_frames()
        self.fe_anim_speed = 5

        self.tasks = []
        for td in S2_TASKS_DEF:
            wx, wy = _tile_to_world(*td["tile"])
            self.tasks.append({
                "name": td["name"],
                "desc": td["desc"],
                "kind": td["kind"],
                "col": td["col"],
                "wx": wx,
                "wy": wy,
                "progress": 0.0,
                "done": False,
            })

        self.active_task = None
        self.player_hp = 15
        self.player_max = 15
        self.immune_timer = 0
        self.flash_msg = ""
        self.flash_timer = 0
        self.done = False
        self.lose = False
        self.t = 0
        self.attack_cooldown = 0
        self.room_name_timer = 90
        self.last_room_name = _room_at_world(self.px, self.py)["name"]
        self._map_surf = self._render_map()

    # ─────────────────────────────────────────────
    # ASSETS
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
            img = pygame.transform.smoothscale(img, (76, 76))
            frames.append(img)
        return frames

    def _make_missing_fe_frame(self, i):
        # Only a fallback so the game can still open while you fix file paths.
        s = pygame.Surface((76, 76), pygame.SRCALPHA)
        pygame.draw.circle(s, (90, 0, 0), (38, 38), 28)
        pygame.draw.circle(s, (240, 230, 230), (28, 30), 8)
        pygame.draw.circle(s, (0, 0, 0), (28, 30), 4)
        pygame.draw.line(s, (180, 0, 0), (18, 52), (58, 52), 3)
        draw_text(s, str(i), font_tiny, WHITE, 38, 10)
        return s

    # ─────────────────────────────────────────────
    # STATIC MAP
    # ─────────────────────────────────────────────
    def _render_map(self):
        surf = pygame.Surface((WORLD_W, WORLD_H))
        surf.fill((1, 2, 8))

        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                x = c * S2_TS
                y = r * S2_TS
                if S2_MAP[r][c] == S2_FLOOR:
                    base = (25, 29, 42) if (c + r) % 2 == 0 else (21, 25, 36)
                    pygame.draw.rect(surf, base, (x, y, S2_TS, S2_TS))
                    pygame.draw.rect(surf, (14, 17, 26), (x, y, S2_TS, S2_TS), 1)
                else:
                    pygame.draw.rect(surf, (2, 3, 9), (x, y, S2_TS, S2_TS))

        for room in S2_ROOMS:
            c0, r0, cw, rh = room["rect"]
            col = room["col"]
            rect = pygame.Rect(c0 * S2_TS, r0 * S2_TS, cw * S2_TS, rh * S2_TS)
            overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            overlay.fill((*col, 18))
            surf.blit(overlay, rect.topleft)
            pygame.draw.rect(surf, tuple(max(0, int(v * 0.55)) for v in col), rect, 3)
            pygame.draw.rect(surf, col, rect.inflate(-8, -8), 1)
            label = font_tiny.render(room["name"], False, col)
            surf.blit(label, (rect.centerx - label.get_width() // 2, rect.top + 8))

        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                if S2_MAP[r][c] != S2_FLOOR:
                    continue
                x = c * S2_TS
                y = r * S2_TS
                wall_col = (75, 88, 120)
                shadow_col = (10, 12, 20)
                for nc, nr, side in [(c, r - 1, "top"), (c, r + 1, "bottom"), (c - 1, r, "left"), (c + 1, r, "right")]:
                    if not _is_floor_tile(nc, nr):
                        if side == "top":
                            pygame.draw.line(surf, wall_col, (x, y), (x + S2_TS, y), 4)
                            pygame.draw.line(surf, shadow_col, (x, y + 4), (x + S2_TS, y + 4), 1)
                        elif side == "bottom":
                            pygame.draw.line(surf, wall_col, (x, y + S2_TS), (x + S2_TS, y + S2_TS), 4)
                        elif side == "left":
                            pygame.draw.line(surf, wall_col, (x, y), (x, y + S2_TS), 4)
                        elif side == "right":
                            pygame.draw.line(surf, wall_col, (x + S2_TS, y), (x + S2_TS, y + S2_TS), 4)

        self._draw_static_decor_to_map(surf)
        return surf

    def _draw_static_decor_to_map(self, surf):
        def tile_rect(tc, tr, cw, rh):
            return pygame.Rect(tc * S2_TS, tr * S2_TS, cw * S2_TS, rh * S2_TS)

        for tr in [4, 6, 8]:
            rect = tile_rect(18, tr, 4, 1)
            pygame.draw.rect(surf, (70, 52, 32), rect, border_radius=8)
            pygame.draw.rect(surf, (155, 120, 65), rect, 2, border_radius=8)

        for tc in [31, 34]:
            rect = tile_rect(tc, 3, 2, 2)
            pygame.draw.rect(surf, (70, 15, 18), rect, border_radius=6)
            pygame.draw.rect(surf, (180, 45, 45), rect, 2, border_radius=6)

        rect = tile_rect(39, 5, 3, 2)
        pygame.draw.rect(surf, (5, 35, 70), rect, border_radius=6)
        pygame.draw.rect(surf, CYAN, rect, 2, border_radius=6)

        for tc in [19, 23]:
            rect = tile_rect(tc, 14, 3, 1)
            pygame.draw.rect(surf, (20, 70, 58), rect, border_radius=6)
            pygame.draw.rect(surf, (100, 230, 170), rect, 2, border_radius=6)

        for tc, tr in [(18, 22), (20, 22), (22, 22), (18, 24), (21, 24)]:
            rect = tile_rect(tc, tr, 1, 1).inflate(-4, -4)
            pygame.draw.rect(surf, (70, 55, 35), rect)
            pygame.draw.rect(surf, (145, 110, 65), rect, 2)

        for tc in [5, 7, 9]:
            rect = tile_rect(tc, 22, 1, 2).inflate(-3, -3)
            pygame.draw.rect(surf, (60, 50, 12), rect)
            pygame.draw.rect(surf, GOLD, rect, 1)

        for tc in [11, 26]:
            rect = tile_rect(tc, 23, 3, 2)
            points = [rect.topleft, rect.topright, (rect.right + 16, rect.centery), rect.bottomright, rect.bottomleft]
            pygame.draw.polygon(surf, (75, 45, 25), points)
            pygame.draw.polygon(surf, ORANGE, points, 2)

        rect = tile_rect(4, 13, 3, 3)
        pygame.draw.rect(surf, (60, 15, 70), rect, border_radius=8)
        pygame.draw.rect(surf, PURPLE, rect, 2, border_radius=8)

    # ─────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.done = True

    def update(self):
        self.t += 1
        self.player_frame += 1
        self.exp_frame += 1
        if self.flash_timer > 0: self.flash_timer -= 1
        if self.immune_timer > 0: self.immune_timer -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.room_name_timer > 0: self.room_name_timer -= 1

        self._update_player()
        self._update_camera()
        self._update_room_name()
        self._update_task_interaction()
        self._update_experiment()

        if all(t["done"] for t in self.tasks):
            self.flash_msg = "SHIP SYSTEMS RESTORED!"
            self.flash_timer = 90
            self.done = True

    def _update_player(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1
        if dx and dy:
            dx *= 0.707
            dy *= 0.707
        if dx:
            self.facing = dx

        speed = self.speed
        if self.active_task is not None and (keys[pygame.K_e] or keys[pygame.K_SPACE]):
            speed *= 0.35

        self.px, self.py = self._move(self.px, self.py, dx * speed, dy * speed)

    def _move(self, x, y, dx, dy, radius=11):
        nx = x + dx
        if not _blocked_world(nx, y, radius):
            x = nx
        ny = y + dy
        if not _blocked_world(x, ny, radius):
            y = ny
        return x, y

    def _update_camera(self):
        view_w = SCREEN_W
        view_h = SCREEN_H - self.HUD_H
        self.cam_x += (self.px - view_w / 2 - self.cam_x) * 0.10
        self.cam_y += (self.py - view_h / 2 - self.cam_y) * 0.10
        self.cam_x = clamp(self.cam_x, 0, max(0, WORLD_W - view_w))
        self.cam_y = clamp(self.cam_y, 0, max(0, WORLD_H - view_h))

    def _update_room_name(self):
        room_name = _room_at_world(self.px, self.py)["name"]
        if room_name != self.last_room_name:
            self.last_room_name = room_name
            self.room_name_timer = 90

    def _update_task_interaction(self):
        keys = pygame.key.get_pressed()
        self.active_task = None
        for task in self.tasks:
            if task["done"]:
                continue
            d = math.hypot(self.px - task["wx"], self.py - task["wy"])
            if d < 42:
                self.active_task = task
                if keys[pygame.K_e] or keys[pygame.K_SPACE]:
                    task["progress"] = min(100, task["progress"] + 0.55)
                    if task["progress"] >= 100:
                        task["done"] = True
                        self.flash_msg = f"{task['name']} REPAIRED!"
                        self.flash_timer = 100
                        sx, sy = self._world_to_screen(task["wx"], task["wy"])
                        spawn_particles(sx, sy, task["col"], 24, 3, 55)
                        repaired = self._repaired_count()
                        self.exp_speed = 2.55 + repaired * 0.22
                break

    def _update_experiment(self):
        self.path_timer += 1
        repaired = self._repaired_count()
        refresh = max(10, 22 - repaired * 2)
        if self.path_timer >= refresh:
            self.path_timer = 0
            self.exp_path = _bfs_path(self.ex, self.ey, self.px, self.py)

        if self.exp_path:
            tc, tr = self.exp_path[0]
            tx, ty = _tile_to_world(tc, tr)
            dx = tx - self.ex
            dy = ty - self.ey
            dist = math.hypot(dx, dy)
            if dist < self.exp_speed + 1:
                self.exp_path.pop(0)
            elif dist > 0:
                self.ex += (dx / dist) * self.exp_speed
                self.ey += (dy / dist) * self.exp_speed

        dist_to_player = math.hypot(self.px - self.ex, self.py - self.ey)
        if dist_to_player < 34 and self.attack_cooldown <= 0:
            self.player_hp -= 4
            self.immune_timer = 75
            self.attack_cooldown = 80
            self.flash_msg = "FAILED EXPERIMENT IS ATTACKING!"
            self.flash_timer = 65
            sx, sy = self._world_to_screen(self.px, self.py)
            spawn_particles(sx, sy, BLOOD_RED, 14, 3, 40)
            if self.player_hp <= 0:
                self.lose = True

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────
    def _repaired_count(self):
        return sum(1 for t in self.tasks if t["done"])

    def _world_to_screen(self, wx, wy):
        return int(wx - self.cam_x), int(wy - self.cam_y) + self.HUD_H

    # ─────────────────────────────────────────────
    # DRAWING
    # ─────────────────────────────────────────────
    def draw(self, surf):
        surf.blit(self._map_surf, (-int(self.cam_x), -int(self.cam_y) + self.HUD_H))
        self._draw_dynamic_room_lights(surf)
        self._draw_tasks(surf)
        self._draw_failed_experiment(surf)
        self._draw_player(surf)
        update_particles(surf)
        self._draw_horror_lighting(surf)
        self._draw_hud(surf)
        self._draw_room_overlay(surf)
        self._draw_task_prompt(surf)
        self._draw_flash_message(surf)

    def _draw_dynamic_room_lights(self, surf):
        if (self.t // 45) % 2 == 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((45, 0, 0, 18))
            surf.blit(overlay, (0, 0))

        rx, ry = _tile_to_world(5, 14)
        sx, sy = self._world_to_screen(rx, ry)
        glow_size = int(70 + 10 * math.sin(self.t * 0.08))
        gs = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (150, 0, 210, 55), (glow_size, glow_size), glow_size)
        surf.blit(gs, (sx - glow_size, sy - glow_size))

        for tx, ty in [(12, 24), (28, 24)]:
            wx, wy = _tile_to_world(tx, ty)
            sx, sy = self._world_to_screen(wx, wy)
            pygame.draw.circle(surf, (255, 120, 35), (sx, sy), 6 + int(3 * math.sin(self.t * 0.12)))

    def _draw_tasks(self, surf):
        for task in self.tasks:
            sx, sy = self._world_to_screen(task["wx"], task["wy"])
            if -80 < sx < SCREEN_W + 80 and self.HUD_H - 80 < sy < SCREEN_H + 80:
                self._draw_task_panel(surf, sx, sy, task)

    def _draw_task_panel(self, surf, x, y, task):
        col = task["col"]
        done = task["done"]
        progress = task["progress"]

        glow_r = 34 if not done else 24
        gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*col, 80 if not done else 45), (glow_r, glow_r), glow_r)
        surf.blit(gs, (x - glow_r, y - glow_r))

        w, h = 68, 52
        bg = (8, 35, 20) if done else (35, 12, 14)
        rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        pygame.draw.rect(surf, bg, rect, border_radius=8)
        pygame.draw.rect(surf, col, rect, 2, border_radius=8)

        kind = task["kind"]
        if kind == "engine":
            for i in range(3):
                px = x - 16 + i * 16
                pygame.draw.rect(surf, (85, 50, 20), (px - 4, y - 16, 8, 22))
                pygame.draw.rect(surf, col, (px - 4, y - 16, 8, 22), 1)
            pygame.draw.line(surf, col, (x - 20, y + 8), (x + 20, y + 8), 2)
        elif kind == "nav":
            pygame.draw.circle(surf, (0, 25, 35), (x, y - 3), 16)
            pygame.draw.circle(surf, col, (x, y - 3), 16, 2)
            angle = self.t * 0.08
            pygame.draw.line(surf, col, (x, y - 3), (x + int(14 * math.cos(angle)), y - 3 + int(14 * math.sin(angle))), 2)
        elif kind == "reactor":
            pulse = int(100 + 60 * math.sin(self.t * 0.12))
            pygame.draw.circle(surf, (pulse, 0, 160), (x, y - 3), 16)
            pygame.draw.circle(surf, col, (x, y - 3), 16, 2)
        elif kind == "life":
            pygame.draw.rect(surf, (20, 80, 35), (x - 8, y - 18, 16, 28), border_radius=6)
            pygame.draw.rect(surf, col, (x - 8, y - 18, 16, 28), 2, border_radius=6)
            draw_text(surf, "O2", font_tiny, col, x, y - 4)
        elif kind == "comms":
            points = [(x - 18, y + 8), (x - 10, y - 10), (x, y - 18), (x + 10, y - 10), (x + 18, y + 8)]
            pygame.draw.polygon(surf, (80, 65, 10), points)
            pygame.draw.polygon(surf, col, points, 2)

        bar_w = w - 14
        pygame.draw.rect(surf, (8, 8, 12), (x - bar_w // 2, y + 18, bar_w, 6), border_radius=3)
        pygame.draw.rect(surf, col, (x - bar_w // 2, y + 18, int(bar_w * progress / 100), 6), border_radius=3)
        if done:
            draw_text(surf, "DONE", font_tiny, (80, 230, 110), x, y + 31)

    def _draw_failed_experiment(self, surf):
        sx, sy = self._world_to_screen(self.ex, self.ey)
        if not (-100 < sx < SCREEN_W + 100 and self.HUD_H - 100 < sy < SCREEN_H + 100):
            return

        d = math.hypot(self.px - self.ex, self.py - self.ey)
        glow_r = 44
        gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (180, 0, 0, 65), (glow_r, glow_r), glow_r)
        surf.blit(gs, (sx - glow_r, sy - glow_r))

        frame_index = (self.exp_frame // self.fe_anim_speed) % len(self.fe_frames)
        img = self.fe_frames[frame_index]
        if self.ex < self.px:
            img = pygame.transform.flip(img, True, False)
        rect = img.get_rect(center=(sx, sy))
        surf.blit(img, rect)

        if d < 150:
            draw_text(surf, "FAILED EXPERIMENT", font_tiny, BLOOD_RED, sx, sy - 52)

    def _draw_player(self, surf):
        sx, sy = self._world_to_screen(self.px, self.py)
        if self.immune_timer <= 0 or self.immune_timer % 8 < 4:
            draw_astronaut(surf, sx, sy, self.player_frame, self.facing)

    def _draw_horror_lighting(self, surf):
        # Vignette
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for r in range(520, 120, -40):
            alpha = int((520 - r) * 0.20)
            pygame.draw.circle(vignette, (0, 0, 0, alpha), (SCREEN_W // 2, SCREEN_H // 2), r, 18)
        surf.blit(vignette, (0, 0))

        d = math.hypot(self.px - self.ex, self.py - self.ey)
        if d < 190:
            alpha = int(clamp((190 - d) / 190 * 125, 0, 125))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((130, 0, 0, alpha))
            surf.blit(overlay, (0, 0))
            pulse = int(210 + 45 * math.sin(self.t * 0.22))
            draw_text(surf, "FE SIGNAL CLOSE", font_med, (pulse, 35, 35), SCREEN_W // 2, SCREEN_H - 80)

    def _draw_hud(self, surf):
        hud = pygame.Surface((SCREEN_W, self.HUD_H), pygame.SRCALPHA)
        hud.fill((5, 8, 18, 238))
        surf.blit(hud, (0, 0))
        pygame.draw.line(surf, (85, 105, 135), (0, self.HUD_H), (SCREEN_W, self.HUD_H), 2)

        repaired = self._repaired_count()
        total = len(self.tasks)
        room = _room_at_world(self.px, self.py)

        pygame.draw.rect(surf, (14, 20, 36), (12, 9, 205, 38), border_radius=8)
        pygame.draw.rect(surf, (80, 105, 135), (12, 9, 205, 38), 1, border_radius=8)
        draw_text_left(surf, "LEVEL 2", font_tiny, (125, 145, 170), 24, 15)
        draw_text_left(surf, "REPAIR THE SHIP", font_small, MOON_GREY, 24, 30)

        draw_text(surf, f"{room['name']} // SYSTEM FAILURE", font_small, (185, 200, 215), SCREEN_W // 2, 17)

        pygame.draw.rect(surf, (30, 24, 10), (SCREEN_W // 2 - 85, 31, 170, 17), border_radius=6)
        pygame.draw.rect(surf, GOLD, (SCREEN_W // 2 - 85, 31, 170, 17), 1, border_radius=6)
        draw_text(surf, f"REPAIRS {repaired}/{total}", font_tiny, GOLD, SCREEN_W // 2, 39)

        draw_hp_bar(surf, SCREEN_W - 190, 15, 165, 20, self.player_hp, self.player_max, "SUIT")
        draw_text(surf, "WASD MOVE  |  HOLD E REPAIR", font_tiny, (90, 110, 135), SCREEN_W - 110, 43)
        self._draw_repair_pips(surf)

    def _draw_repair_pips(self, surf):
        start_x = 238
        y = 25
        size = 9
        for i, task in enumerate(self.tasks):
            x = start_x + i * 18
            col = task["col"] if task["done"] else (45, 50, 65)
            pygame.draw.rect(surf, col, (x, y, size, size), border_radius=2)
            pygame.draw.rect(surf, (120, 130, 150), (x, y, size, size), 1, border_radius=2)

    def _draw_room_overlay(self, surf):
        if self.room_name_timer <= 0:
            return
        alpha = min(210, self.room_name_timer * 4)
        room = _room_at_world(self.px, self.py)
        draw_text(surf, room["name"], font_large, room["col"], SCREEN_W // 2, SCREEN_H // 2 - 130, alpha)

    def _draw_task_prompt(self, surf):
        if self.active_task is None:
            return
        task = self.active_task
        panel = pygame.Surface((SCREEN_W, 76), pygame.SRCALPHA)
        panel.fill((5, 8, 18, 220))
        surf.blit(panel, (0, SCREEN_H - 76))
        pygame.draw.line(surf, task["col"], (0, SCREEN_H - 76), (SCREEN_W, SCREEN_H - 76), 2)
        draw_text(surf, f"HOLD [E] TO REPAIR: {task['name']}", font_small, task["col"], SCREEN_W // 2, SCREEN_H - 56)
        draw_text(surf, task["desc"], font_tiny, (180, 190, 205), SCREEN_W // 2, SCREEN_H - 37)
        bar_w = 320
        pygame.draw.rect(surf, (18, 20, 28), (SCREEN_W // 2 - bar_w // 2, SCREEN_H - 22, bar_w, 10), border_radius=5)
        pygame.draw.rect(surf, task["col"], (SCREEN_W // 2 - bar_w // 2, SCREEN_H - 22, int(bar_w * task["progress"] / 100), 10), border_radius=5)
        pygame.draw.rect(surf, (120, 130, 150), (SCREEN_W // 2 - bar_w // 2, SCREEN_H - 22, bar_w, 10), 1, border_radius=5)

    def _draw_flash_message(self, surf):
        if self.flash_timer <= 0:
            return
        alpha = min(255, self.flash_timer * 4)
        draw_text(surf, self.flash_msg, font_med, CYAN, SCREEN_W // 2, SCREEN_H // 2 - 60, alpha)
