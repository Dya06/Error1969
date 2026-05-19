"""Level 1: moon maze, ship-part collection, fog of war, and The Watcher."""

import pygame
import random
import math
from settings import *
from utils import *
from core.particles import spawn_particles, update_particles
from graphics.sprites import *

# ─────────────────────────────────────────────
#  LEVEL 1 – MAZE MAP WITH FOG OF WAR + JUMPSCARE
# ─────────────────────────────────────────────

# Maze tile constants
TILE_FLOOR = 0
TILE_WALL = 1

# Maze dimensions (in tiles)
MAZE_COLS = 25
MAZE_ROWS = 19
TILE_SIZE = 40
MAZE_PX_W = MAZE_COLS * TILE_SIZE
MAZE_PX_H = MAZE_ROWS * TILE_SIZE

# Visibility radius in pixels
VIS_RADIUS = 260


def generate_maze(cols, rows):
    """
    Generate a maze, then open extra paths so it does not feel too one-way.
    Recursive backtracker creates a perfect maze, so we 'braid' it after generation.
    """
    c = cols if cols % 2 == 1 else cols - 1
    r = rows if rows % 2 == 1 else rows - 1
    grid = [[TILE_WALL] * c for _ in range(r)]

    def carve(cx, cy):
        dirs = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(dirs)

        for dx, dy in dirs:
            nx, ny = cx + dx, cy + dy

            if 0 <= nx < c and 0 <= ny < r and grid[ny][nx] == TILE_WALL:
                grid[cy + dy // 2][cx + dx // 2] = TILE_FLOOR
                grid[ny][nx] = TILE_FLOOR
                carve(nx, ny)

    grid[1][1] = TILE_FLOOR
    carve(1, 1)

    # Pad/trim to exact cols × rows
    result = []
    for row in grid[:rows]:
        result.append((row + [TILE_WALL] * cols)[:cols])

    while len(result) < rows:
        result.append([TILE_WALL] * cols)

    # Add extra connections so the maze has loops and alternate paths
    result = braid_maze(result, chance=0.65)

    return result


def braid_maze(maze, chance=0.65):
    """
    Open extra walls near dead ends.
    This makes the maze less linear and gives the player more route choices.
    """
    rows = len(maze)
    cols = len(maze[0])

    def floor_neighbours(c, r):
        count = 0
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nc, nr = c + dc, r + dr
            if 0 <= nc < cols and 0 <= nr < rows:
                if maze[nr][nc] == TILE_FLOOR:
                    count += 1
        return count

    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if maze[r][c] != TILE_FLOOR:
                continue

            # If it is a dead end, maybe open another path
            if floor_neighbours(c, r) <= 1 and random.random() < chance:
                candidates = []

                for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    wall_c = c + dc
                    wall_r = r + dr
                    next_c = c + dc * 2
                    next_r = r + dr * 2

                    if 0 <= next_c < cols and 0 <= next_r < rows:
                        if maze[wall_r][wall_c] == TILE_WALL and maze[next_r][next_c] == TILE_FLOOR:
                            candidates.append((wall_c, wall_r))

                if candidates:
                    open_c, open_r = random.choice(candidates)
                    maze[open_r][open_c] = TILE_FLOOR

    return maze


def _maze_floor_cells(maze):
    """Return list of (col, row) floor tiles."""
    cells = []
    for r, row in enumerate(maze):
        for c, tile in enumerate(row):
            if tile == TILE_FLOOR:
                cells.append((c, r))
    return cells


def _make_floor_tile(seed):
    """Moon floor tile with brighter dusty texture."""
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    rng = random.Random(seed)

    base = rng.randint(60, 82)
    s.fill((base, base, base + 8))

    # Dust texture
    for _ in range(18):
        px = rng.randint(0, TILE_SIZE - 1)
        py = rng.randint(0, TILE_SIZE - 1)
        v = rng.randint(-18, 18)

        col = (
            clamp(base + v, 35, 120),
            clamp(base + v, 35, 120),
            clamp(base + 8 + v, 40, 130)
        )
        pygame.draw.circle(s, col, (px, py), rng.choice([1, 1, 2]))

    # Subtle moon cracks
    if rng.random() < 0.35:
        x1 = rng.randint(4, TILE_SIZE - 8)
        y1 = rng.randint(4, TILE_SIZE - 8)
        x2 = x1 + rng.randint(-12, 12)
        y2 = y1 + rng.randint(-12, 12)
        pygame.draw.line(s, (45, 45, 55), (x1, y1), (x2, y2), 1)

    return s


def _make_wall_tile(seed):
    """Rock wall tile, brighter with visible edges."""
    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    rng = random.Random(seed + 1000)

    base = rng.randint(42, 58)
    s.fill((base, base, base + 8))

    # Rock chunks
    for _ in range(8):
        x = rng.randint(0, TILE_SIZE - 8)
        y = rng.randint(0, TILE_SIZE - 8)
        w = rng.randint(6, 16)
        h = rng.randint(4, 12)
        shade = rng.randint(-12, 14)

        col = (
            clamp(base + shade, 25, 90),
            clamp(base + shade, 25, 90),
            clamp(base + 8 + shade, 30, 100)
        )
        pygame.draw.rect(s, col, (x, y, w, h))

    # Cracks
    for _ in range(4):
        x1 = rng.randint(2, TILE_SIZE - 2)
        y1 = rng.randint(2, TILE_SIZE - 2)
        x2 = x1 + rng.randint(-12, 12)
        y2 = y1 + rng.randint(-12, 12)
        pygame.draw.line(s, (25, 25, 35), (x1, y1), (x2, y2), 1)

    # Top highlight and bottom shadow
    pygame.draw.line(s, (85, 85, 100), (0, 0), (TILE_SIZE, 0), 2)
    pygame.draw.line(s, (25, 25, 35), (0, TILE_SIZE - 1), (TILE_SIZE, TILE_SIZE - 1), 2)

    return s


class Level1:
    HUD_H = 55

    def __init__(self):
        # ── Maze ──────────────────────────────────────
        self.maze = generate_maze(MAZE_COLS, MAZE_ROWS)
        self.floor_cells = _maze_floor_cells(self.maze)

        # Pre-render tile surfaces for performance
        self._floor_tiles = {(c, r): _make_floor_tile(c * 100 + r)
                             for c, r in self.floor_cells}

        # Pre-rendered wall tiles per cell
        self._wall_tiles = {}
        for r in range(MAZE_ROWS):
            for c in range(MAZE_COLS):
                if self.maze[r][c] == TILE_WALL:
                    self._wall_tiles[(c, r)] = _make_wall_tile(c * 77 + r * 13)

        # ── Camera ────────────────────────────────────
        self.cam_x = 0.0
        self.cam_y = 0.0

        # ── Player ────────────────────────────────────
        self.px = 1.5 * TILE_SIZE
        self.py = 1.5 * TILE_SIZE
        self.speed = 2.5
        self.player_frame = 0
        self.facing = 0

        # ── Watcher ───────────────────────────────────
        wx_tile, wy_tile = self._far_floor_cell(1, 1)
        self.wx = (wx_tile + 0.5) * TILE_SIZE
        self.wy = (wy_tile + 0.5) * TILE_SIZE
        self.watcher_frame = 0
        self.watcher_speed = 1.0
        self.watcher_path = []
        self.path_timer = 0

        # ── Ship parts ────────────────────────────────
        self.parts_total = 5
        self.parts = []
        self._place_parts()
        self.collected = 0

        # ── State ─────────────────────────────────────
        self.player_hp = 10
        self.player_max = 10
        self.immune_timer = 0
        self.flash_msg = ""
        self.flash_timer = 0
        self.done = False
        self.lose = False
        self.t = 0
        self.atk_timer = 0

        # ── Jumpscare ─────────────────────────────────
        self.jumpscare_active = False
        self.jumpscare_timer = 0
        self.jumpscare_scale = 0.0
        self.JUMPSCARE_DUR = 120

        # ── Fog surface ───────────────────────────────
        self._fog = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # ── Minimap ───────────────────────────────────
        self.visited = {(1, 1)}

        # ── Sounds ────────────────────────────────────
        self._init_sounds()

    # ─── helpers ───────────────────────────────────────────────────────────

    def _far_floor_cell(self, start_col, start_row, min_dist=10):
        best = (MAZE_COLS - 2, MAZE_ROWS - 2)
        best_d = 0

        for c, r in self.floor_cells:
            d = abs(c - start_col) + abs(r - start_row)
            if d > best_d:
                best_d = d
                best = (c, r)

        return best

    def _place_parts(self):
        """
        Place ship parts in better positions:
        - not too close to spawn
        - not all clustered together
        - preferably in more open areas
        """
        taken = {(1, 1)}
        self.parts = []

        def neighbour_count(cell):
            c, r = cell
            count = 0

            for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nc, nr = c + dc, r + dr

                if 0 <= nc < MAZE_COLS and 0 <= nr < MAZE_ROWS:
                    if self.maze[nr][nc] == TILE_FLOOR:
                        count += 1

            return count

        candidates = []

        for cell in self.floor_cells:
            c, r = cell
            dist_from_start = abs(c - 1) + abs(r - 1)

            # Avoid spawn area and avoid annoying dead ends
            if dist_from_start > 6 and neighbour_count(cell) >= 2:
                candidates.append(cell)

        random.shuffle(candidates)

        for cell in candidates:
            if len(self.parts) >= self.parts_total:
                break

            # Avoid placing parts too close together
            too_close = False

            for part in self.parts:
                d = abs(cell[0] - part["col"]) + abs(cell[1] - part["row"])
                if d < 5:
                    too_close = True
                    break

            if too_close:
                continue

            taken.add(cell)

            self.parts.append({
                "col": cell[0],
                "row": cell[1],
                "x": (cell[0] + 0.5) * TILE_SIZE,
                "y": (cell[1] + 0.5) * TILE_SIZE,
                "type": len(self.parts),
                "collected": False
            })

        # Fallback, just in case not enough candidates were found
        while len(self.parts) < self.parts_total:
            cell = random.choice(self.floor_cells)

            if cell not in taken:
                taken.add(cell)

                self.parts.append({
                    "col": cell[0],
                    "row": cell[1],
                    "x": (cell[0] + 0.5) * TILE_SIZE,
                    "y": (cell[1] + 0.5) * TILE_SIZE,
                    "type": len(self.parts),
                    "collected": False
                })

    def _tile_at_px(self, x, y):
        c = int(x / TILE_SIZE)
        r = int(y / TILE_SIZE)

        if 0 <= c < MAZE_COLS and 0 <= r < MAZE_ROWS:
            return self.maze[r][c]

        return TILE_WALL

    def _move_with_collision(self, x, y, dx, dy, radius=10):
        """Slide movement with wall collision."""
        nx = x + dx
        ny = y + dy

        def blocked(tx, ty):
            return self._tile_at_px(tx, ty) == TILE_WALL

        # X axis
        if (not blocked(nx - radius, y - radius) and
                not blocked(nx + radius, y - radius) and
                not blocked(nx - radius, y + radius) and
                not blocked(nx + radius, y + radius)):
            x = nx

        # Y axis
        if (not blocked(x - radius, ny - radius) and
                not blocked(x + radius, ny - radius) and
                not blocked(x - radius, ny + radius) and
                not blocked(x + radius, ny + radius)):
            y = ny

        return x, y

    def _bfs_path(self, sx, sy, gx, gy):
        """BFS on tile grid from (sx, sy) to (gx, gy)."""
        from collections import deque

        start = (int(sx / TILE_SIZE), int(sy / TILE_SIZE))
        goal = (int(gx / TILE_SIZE), int(gy / TILE_SIZE))

        if start == goal:
            return []

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            (c, r), path = queue.popleft()

            for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nc, nr = c + dc, r + dr

                if (nc, nr) == goal:
                    return path + [(nc, nr)]

                if (0 <= nc < MAZE_COLS and 0 <= nr < MAZE_ROWS
                        and (nc, nr) not in visited
                        and self.maze[nr][nc] == TILE_FLOOR):
                    visited.add((nc, nr))
                    queue.append(((nc, nr), path + [(nc, nr)]))

        return []

    def _init_sounds(self):
        """Generate simple tones/noise for ambience and jumpscare."""
        self.snd_collect = self._gen_tone(880, 0.12, shape="square")
        self.snd_heartbeat = self._gen_tone(60, 0.18, shape="pulse")
        self.snd_jumpscare = self._gen_noise(0.5)
        self.heartbeat_timer = 0

    def _gen_tone(self, freq, duration, shape="sine", volume=0.3):
        try:
            import numpy as np

            sr = 44100
            n = int(sr * duration)
            t = np.linspace(0, duration, n, endpoint=False)

            if shape == "sine":
                wave = np.sin(2 * np.pi * freq * t)
            elif shape == "square":
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

            # Low-pass: running average to make it more bassy
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

    # ─── update ────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
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

        if self.immune_timer > 0:
            self.immune_timer -= 1

        if self.atk_timer > 0:
            self.atk_timer -= 1

        # ── Player movement ────────────────────────────
        keys = pygame.key.get_pressed()
        mdx = 0
        mdy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            mdx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            mdx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            mdy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            mdy += 1

        if mdx and mdy:
            mdx *= 0.707
            mdy *= 0.707

        if mdx or mdy:
            self.facing = mdx

        self.px, self.py = self._move_with_collision(
            self.px,
            self.py,
            mdx * self.speed,
            mdy * self.speed,
            radius=11
        )

        # ── Camera follows player ──────────────────────
        view_w = SCREEN_W
        view_h = SCREEN_H - self.HUD_H

        target_cx = self.px - view_w / 2
        target_cy = self.py - view_h / 2

        self.cam_x += (target_cx - self.cam_x) * 0.12
        self.cam_y += (target_cy - self.cam_y) * 0.12

        self.cam_x = clamp(self.cam_x, 0, max(0, MAZE_PX_W - view_w))
        self.cam_y = clamp(self.cam_y, 0, max(0, MAZE_PX_H - view_h))

        # ── Mark visited tiles ─────────────────────────
        pc = int(self.px / TILE_SIZE)
        pr = int(self.py / TILE_SIZE)

        for dr in range(-3, 4):
            for dc in range(-3, 4):
                self.visited.add((pc + dc, pr + dr))

        # ── Part collection ────────────────────────────
        for part in self.parts:
            if part["collected"]:
                continue

            if math.hypot(self.px - part["x"], self.py - part["y"]) < 20:
                part["collected"] = True
                self.collected += 1
                self.flash_msg = f"PART {self.collected}/{self.parts_total} FOUND!"
                self.flash_timer = 90

                spawn_particles(
                    int(self.px),
                    int(self.py) + self.HUD_H,
                    GOLD,
                    16,
                    3,
                    45
                )

                self._play(self.snd_collect)

                if self.collected >= self.parts_total:
                    self.flash_msg = "ALL PARTS FOUND! HEAD BACK TO THE SHIP!"
                    self.flash_timer = 150
                    self.done = True

        # ── Watcher AI ─────────────────────────────────
        self.path_timer += 1

        if self.path_timer >= 40:
            self.path_timer = 0
            self.watcher_path = self._bfs_path(self.wx, self.wy, self.px, self.py)

        if self.watcher_path:
            next_tile = self.watcher_path[0]
            target_x = (next_tile[0] + 0.5) * TILE_SIZE
            target_y = (next_tile[1] + 0.5) * TILE_SIZE

            ddx = target_x - self.wx
            ddy = target_y - self.wy
            dist_to_wp = math.hypot(ddx, ddy)

            if dist_to_wp < self.watcher_speed + 1:
                self.watcher_path.pop(0)
            else:
                self.wx += (ddx / dist_to_wp) * self.watcher_speed
                self.wy += (ddy / dist_to_wp) * self.watcher_speed

        # ── Watcher catch check ────────────────────────
        dist = math.hypot(self.px - self.wx, self.py - self.wy)

        self.heartbeat_timer -= 1

        if dist < VIS_RADIUS * 0.8:
            interval = max(10, int(dist / 4))

            if self.heartbeat_timer <= 0:
                self._play(self.snd_heartbeat)
                self.heartbeat_timer = interval

        if dist < 28 and not self.jumpscare_active:
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

    # ─── draw ──────────────────────────────────────────────────────────────

    def _world_to_screen(self, wx, wy):
        """Convert world pixel coords to screen coords."""
        return int(wx - self.cam_x), int(wy - self.cam_y) + self.HUD_H

    def draw(self, surf):
        if self.jumpscare_active:
            self._draw_jumpscare(surf)
            return

        surf.fill((8, 9, 14))

        view_w = SCREEN_W
        view_h = SCREEN_H - self.HUD_H

        tc_min = max(0, int(self.cam_x / TILE_SIZE) - 1)
        tc_max = min(MAZE_COLS, int((self.cam_x + view_w) / TILE_SIZE) + 2)
        tr_min = max(0, int(self.cam_y / TILE_SIZE) - 1)
        tr_max = min(MAZE_ROWS, int((self.cam_y + view_h) / TILE_SIZE) + 2)

        psx, psy = self._world_to_screen(self.px, self.py)

        # ── Draw floor & walls ─────────────────────────
        for r in range(tr_min, tr_max):
            for c in range(tc_min, tc_max):
                sx = int(c * TILE_SIZE - self.cam_x)
                sy = int(r * TILE_SIZE - self.cam_y) + self.HUD_H
                tile = self.maze[r][c]

                dx = sx + TILE_SIZE // 2 - psx
                dy = sy + TILE_SIZE // 2 - psy
                d = math.hypot(dx, dy)

                if d > VIS_RADIUS + TILE_SIZE:
                    pygame.draw.rect(surf, (0, 0, 0), (sx, sy, TILE_SIZE, TILE_SIZE))
                    continue

                if tile == TILE_FLOOR:
                    ts = self._floor_tiles.get((c, r))

                    if ts:
                        surf.blit(ts, (sx, sy))
                    else:
                        pygame.draw.rect(surf, (60, 60, 70), (sx, sy, TILE_SIZE, TILE_SIZE))

                    pygame.draw.rect(surf, (42, 42, 52), (sx, sy, TILE_SIZE, TILE_SIZE), 1)

                else:
                    ts = self._wall_tiles.get((c, r))

                    if ts:
                        surf.blit(ts, (sx, sy))
                    else:
                        pygame.draw.rect(surf, (42, 42, 52), (sx, sy, TILE_SIZE, TILE_SIZE))

                    pygame.draw.line(surf, (85, 85, 100), (sx, sy), (sx + TILE_SIZE, sy), 1)

        # ── Watcher glow and sprite ────────────────────
        wsx, wsy = self._world_to_screen(self.wx, self.wy)
        watcher_dist = math.hypot(self.px - self.wx, self.py - self.wy)

        if watcher_dist < VIS_RADIUS * 1.5:
            glow_alpha = int(clamp((VIS_RADIUS * 1.5 - watcher_dist) / VIS_RADIUS * 80, 0, 80))
            gs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(gs, (80, 0, 120, glow_alpha), (wsx, wsy), 60)
            surf.blit(gs, (0, 0))

        if watcher_dist < VIS_RADIUS:
            draw_watcher(surf, wsx, wsy, self.watcher_frame)

        # ── Ship parts ─────────────────────────────────
        for part in self.parts:
            if part["collected"]:
                continue

            sx, sy = self._world_to_screen(part["x"], part["y"])
            d = math.hypot(sx - psx, sy - psy)

            if d < VIS_RADIUS:
                draw_ship_part(surf, sx, sy, part["type"])

        # ── Player ─────────────────────────────────────
        draw_astronaut(surf, psx, psy, self.player_frame, self.facing)

        update_particles(surf)

        # ── Fog and minimap ────────────────────────────
        self._draw_fog(surf, psx, psy)
        self._draw_minimap(surf)

        # ── HUD ────────────────────────────────────────
        self._draw_hud(surf)

        # ── Proximity warning ──────────────────────────
        if watcher_dist < VIS_RADIUS * 0.9:
            alpha = int(clamp((VIS_RADIUS * 0.9 - watcher_dist) / (VIS_RADIUS * 0.5) * 160, 0, 160))
            ws = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ws.fill((120, 0, 0, alpha))
            surf.blit(ws, (0, 0))

            pulse = int(200 + 55 * math.sin(self.t * 0.2))
            draw_text(
                surf,
                "IT'S CLOSE...",
                font_med,
                (pulse, 30, 30),
                SCREEN_W // 2,
                SCREEN_H // 2 + 80
            )

        # ── Flash message ──────────────────────────────
        if self.flash_timer > 0:
            alpha = min(255, self.flash_timer * 4)
            draw_text(
                surf,
                self.flash_msg,
                font_med,
                YELLOW,
                SCREEN_W // 2,
                SCREEN_H // 2 - 60,
                alpha
            )

    def _draw_hud(self, surf):
        """Cleaner HUD design."""
        hud = pygame.Surface((SCREEN_W, self.HUD_H), pygame.SRCALPHA)
        hud.fill((6, 8, 18, 230))
        surf.blit(hud, (0, 0))

        pygame.draw.line(surf, (90, 90, 120), (0, self.HUD_H), (SCREEN_W, self.HUD_H), 2)

        # Left objective panel
        pygame.draw.rect(surf, (18, 20, 34), (12, 9, 210, 36), border_radius=8)
        pygame.draw.rect(surf, (90, 90, 120), (12, 9, 210, 36), 1, border_radius=8)

        draw_text_left(surf, "LEVEL 1", font_tiny, (120, 120, 150), 24, 14)
        draw_text_left(surf, "FIND SHIP PARTS", font_small, MOON_GREY, 24, 27)

        # Centre title
        draw_text(
            surf,
            "LUNAR SURFACE // SIGNAL LOST",
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
            f"PARTS {self.collected}/{self.parts_total}",
            font_tiny,
            GOLD,
            SCREEN_W // 2,
            37
        )

        # Health bar on right
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

        # Control hint
        draw_text(
            surf,
            "WASD MOVE",
            font_tiny,
            (90, 90, 120),
            SCREEN_W - 105,
            43
        )

    def _draw_fog(self, surf, cx, cy):
        """Softer fog-of-war so the level is still scary but playable."""
        fog = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fog.fill((0, 0, 0, 185))

        steps = 28

        for i in range(steps, 0, -1):
            r = int(VIS_RADIUS * i / steps)
            alpha = int(185 * (1 - (i / steps) ** 0.75))

            pygame.draw.circle(
                fog,
                (0, 0, 0, alpha),
                (cx, cy),
                r
            )

        surf.blit(fog, (0, 0))

    def _draw_minimap(self, surf):
        """Tiny minimap in the top-right corner showing visited tiles."""
        mm_tile = 3
        mm_w = MAZE_COLS * mm_tile
        mm_h = MAZE_ROWS * mm_tile
        mm_x = SCREEN_W - mm_w - 8
        mm_y = 4

        pygame.draw.rect(surf, (5, 5, 10), (mm_x - 1, mm_y - 1, mm_w + 2, mm_h + 2))

        for r in range(MAZE_ROWS):
            for c in range(MAZE_COLS):
                if (c, r) not in self.visited:
                    continue

                colour = (35, 35, 50) if self.maze[r][c] == TILE_WALL else (90, 90, 110)

                pygame.draw.rect(
                    surf,
                    colour,
                    (mm_x + c * mm_tile, mm_y + r * mm_tile, mm_tile, mm_tile)
                )

        # Parts on minimap
        for part in self.parts:
            if not part["collected"] and (part["col"], part["row"]) in self.visited:
                pygame.draw.rect(
                    surf,
                    GOLD,
                    (mm_x + part["col"] * mm_tile,
                     mm_y + part["row"] * mm_tile,
                     mm_tile,
                     mm_tile)
                )

        # Player dot
        pc = int(self.px / TILE_SIZE)
        pr = int(self.py / TILE_SIZE)

        pygame.draw.rect(
            surf,
            CYAN,
            (mm_x + pc * mm_tile, mm_y + pr * mm_tile, mm_tile, mm_tile)
        )

        pygame.draw.rect(surf, (80, 80, 110), (mm_x - 1, mm_y - 1, mm_w + 2, mm_h + 2), 1)

    def _draw_jumpscare(self, surf):
        """Full-screen animated jumpscare when caught by The Watcher."""
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

            pygame.draw.ellipse(
                surf,
                (230, 220, 220),
                (cx - size, cy - size // 3, size * 2, size // 3 * 2),
                3
            )

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
