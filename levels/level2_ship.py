"""Level 2: ship interior repair tasks and Failed Experiment chase."""

import pygame
import random
import math
from settings import *
from utils import *
from core.particles import spawn_particles, update_particles
from graphics.sprites import *

# ─────────────────────────────────────────────
#  LEVEL 2 – SHIP INTERIOR MAP  (Skeld-style)
# ─────────────────────────────────────────────
#
#  World tile size
S2_TS   = 32          # pixels per tile
S2_COLS = 40          # world width in tiles
S2_ROWS = 28          # world height in tiles
S2_HUD  = 50          # HUD strip height

# Tile types
S2_VOID  = 0   # outside ship (black)
S2_FLOOR = 1   # walkable floor
S2_WALL  = 2   # solid wall

def _build_ship_map():
    """
    Build a Skeld-inspired ship floor plan as a tile grid.
    Rooms:
      CAFETERIA  – top centre
      WEAPONS    – top right
      NAVIGATION – far right
      SHIELDS    – bottom right
      LOWER ENGINE– bottom centre-right
      UPPER ENGINE– bottom centre-left
      REACTOR    – far left
      SECURITY   – left-centre
      MED-BAY    – centre
      ELECTRICAL – bottom-left
      STORAGE    – centre-bottom
    Corridors connect them.
    Returns: 2D list S2_ROWS × S2_COLS of tile type.
    """
    grid = [[S2_VOID] * S2_COLS for _ in range(S2_ROWS)]

    def fill(c0, r0, cw, rh, t=S2_FLOOR):
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + cw):
                if 0 <= c < S2_COLS and 0 <= r < S2_ROWS:
                    grid[r][c] = t

    # ── Rooms ──────────────────────────────────────────────
    fill(13,  1, 14,  9)   # CAFETERIA  (top centre)
    fill(28,  1,  8,  7)   # WEAPONS    (top right)
    fill(35,  3,  5,  5)   # NAVIGATION (far right)
    fill(30, 12,  8,  6)   # SHIELDS    (right mid)
    fill(24, 19,  8,  6)   # LOWER ENGINE
    fill(10, 19,  8,  6)   # UPPER ENGINE
    fill( 1, 10,  8,  8)   # REACTOR    (far left)
    fill( 9, 11,  8,  6)   # SECURITY   (left mid)
    fill(17, 12,  8,  7)   # MED-BAY    (centre)
    fill( 4, 19,  8,  6)   # ELECTRICAL (bottom left)
    fill(16, 19, 10,  6)   # STORAGE    (bottom centre)

    # ── Corridors ──────────────────────────────────────────
    fill(17,  9,  4,  4)   # Cafeteria → MedBay (vertical)
    fill(27,  3,  2,  5)   # Cafeteria → Weapons (horizontal stub)
    fill(33,  5,  3,  3)   # Weapons → Nav
    fill(38,  5,  2,  8)   # Nav → Shields (right edge)
    fill(30,  7,  2,  6)   # Weapons → Shields
    fill(25, 17,  4,  3)   # Shields → Lower Engine
    fill(17, 17,  2,  3)   # MedBay → Storage
    fill(12, 17,  6,  3)   # Security → Storage
    fill( 9, 17,  2,  3)   # Security → Upper Engine
    fill( 3, 17,  2,  3)   # Reactor → Electrical
    fill( 9, 14,  2,  6)   # Security → Electrical (vertical)
    fill( 1, 17, 10,  3)   # bottom-left corridor

    # ── Wall border around every floor tile ───────────────
    # (we'll compute this in draw instead)
    return grid

# Pre-build the map once
S2_MAP = _build_ship_map()

def _s2_floor_cells():
    return [(c, r) for r in range(S2_ROWS)
            for c in range(S2_COLS) if S2_MAP[r][c] == S2_FLOOR]

S2_FLOOR_CELLS = _s2_floor_cells()

# ── Room metadata  (name, tile rect, accent colour, decor type) ──────────
S2_ROOMS = [
    {"name": "CAFETERIA",     "rect": (13,  1, 14,  9), "col": (80,  60, 30),  "decor": "cafe"},
    {"name": "WEAPONS",       "rect": (28,  1,  8,  7), "col": (80,  20, 20),  "decor": "weapons"},
    {"name": "NAVIGATION",    "rect": (35,  3,  5,  5), "col": (20,  60, 120), "decor": "nav"},
    {"name": "SHIELDS",       "rect": (30, 12,  8,  6), "col": (20,  80, 80),  "decor": "shields"},
    {"name": "LOWER ENGINE",  "rect": (24, 19,  8,  6), "col": (100, 40, 20),  "decor": "engine"},
    {"name": "UPPER ENGINE",  "rect": (10, 19,  8,  6), "col": (100, 40, 20),  "decor": "engine"},
    {"name": "REACTOR",       "rect": ( 1, 10,  8,  8), "col": (100, 20, 100), "decor": "reactor"},
    {"name": "SECURITY",      "rect": ( 9, 11,  8,  6), "col": (40,  80, 40),  "decor": "security"},
    {"name": "MED-BAY",       "rect": (17, 12,  8,  7), "col": (20, 100, 60),  "decor": "medbay"},
    {"name": "ELECTRICAL",    "rect": ( 4, 19,  8,  6), "col": (100, 80, 20),  "decor": "electrical"},
    {"name": "STORAGE",       "rect": (16, 19, 10,  6), "col": (50,  50, 70),  "decor": "storage"},
]

# ── Repair tasks with world-tile positions ────────────────────────────────
S2_TASKS_DEF = [
    {"name": "ENGINE CORE",   "tile": (27, 21), "draw": "task_engine",   "col": ORANGE},
    {"name": "NAV MODULE",    "tile": (37,  5), "draw": "task_nav",      "col": CYAN},
    {"name": "REACTOR CORE",  "tile": ( 4, 13), "draw": "task_reactor",  "col": PURPLE},
    {"name": "LIFE SUPPORT",  "tile": (20, 14), "draw": "task_life",     "col": (80, 220, 80)},
    {"name": "COMM ARRAY",    "tile": (15,  4), "draw": "task_comms",    "col": GOLD},
]

def _tile_to_world(tc, tr):
    """Centre pixel of a tile in world coordinates."""
    return tc * S2_TS + S2_TS // 2, tr * S2_TS + S2_TS // 2

def _s2_bfs(sx, sy, gx, gy):
    """BFS path on S2_MAP from world-px (sx,sy) to (gx,gy).
    Returns list of (col,row) waypoints."""
    from collections import deque
    sc = int(sx / S2_TS); sr = int(sy / S2_TS)
    gc = int(gx / S2_TS); gr = int(gy / S2_TS)
    if sc == gc and sr == gr: return []
    q = deque([(sc, sr, [(sc, sr)])])
    vis = {(sc, sr)}
    while q:
        c, r, path = q.popleft()
        for dc, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
            nc, nr = c+dc, r+dr
            if (nc, nr) == (gc, gr):
                return path + [(nc, nr)]
            if (0 <= nc < S2_COLS and 0 <= nr < S2_ROWS
                    and (nc, nr) not in vis
                    and S2_MAP[nr][nc] == S2_FLOOR):
                vis.add((nc, nr))
                q.append((nc, nr, path + [(nc, nr)]))
    return []

def _s2_blocked(x, y, r=10):
    """True if a circle at (x,y) radius r overlaps a wall tile."""
    for dx2, dy2 in [(-r,-r),(r,-r),(-r,r),(r,r),(0,-r),(0,r),(-r,0),(r,0)]:
        tc = int((x+dx2) / S2_TS); tr = int((y+dy2) / S2_TS)
        if not (0 <= tc < S2_COLS and 0 <= tr < S2_ROWS):
            return True
        if S2_MAP[tr][tc] != S2_FLOOR:
            return True
    return False

# ── Detailed task panel drawers (world-space, x/y = centre) ──────────────
def _draw_task_panel_base(surf, x, y, w, h, col, done, progress):
    bg = (10, 30, 10) if done else (30, 10, 10)
    pygame.draw.rect(surf, bg,  (x-w//2, y-h//2, w, h))
    pygame.draw.rect(surf, col, (x-w//2, y-h//2, w, h), 2)
    # screws at corners
    for cx2, cy2 in [(x-w//2+3, y-h//2+3),(x+w//2-3, y-h//2+3),
                     (x-w//2+3, y+h//2-3),(x+w//2-3, y+h//2-3)]:
        pygame.draw.circle(surf, MOON_GREY, (cx2, cy2), 2)
    # progress bar at bottom
    bw = w - 8
    pygame.draw.rect(surf, (20,20,20), (x-bw//2, y+h//2-8, bw, 5))
    pygame.draw.rect(surf, col, (x-bw//2, y+h//2-8, int(bw*progress/100), 5))
    if done:
        draw_text(surf, "✓ DONE", font_tiny, (60,200,60), x, y+h//2-14)

def draw_task_engine_panel(surf, x, y, done, progress, t):
    col = ORANGE
    _draw_task_panel_base(surf, x, y, 52, 44, col, done, progress)
    # Piston cylinders
    for i, cx2 in enumerate([x-12, x, x+12]):
        ph = int(10 + 6*math.sin(t*0.12 + i*1.2)) if not done else 14
        pygame.draw.rect(surf, (80,50,20), (cx2-4, y-16, 8, 20))
        pygame.draw.rect(surf, col,        (cx2-4, y-16, 8, 20), 1)
        pygame.draw.rect(surf, (200,140,60),(cx2-3, y-16+ph, 6, 5))
    # Crankshaft line
    pygame.draw.line(surf, MOON_GREY, (x-18, y+6), (x+18, y+6), 2)
    draw_text(surf, "ENGINE", font_tiny, col, x, y-20)

def draw_task_nav_panel(surf, x, y, done, progress, t):
    col = CYAN
    _draw_task_panel_base(surf, x, y, 52, 44, col, done, progress)
    # Circular radar screen
    pygame.draw.circle(surf, (0,20,30),  (x, y-4), 14)
    pygame.draw.circle(surf, col,         (x, y-4), 14, 1)
    # Sweep line
    angle = t * 0.08 if not done else 0
    ex2 = int(x + 12*math.cos(angle)); ey2 = int(y-4 + 12*math.sin(angle))
    pygame.draw.line(surf, (0,180,180), (x, y-4), (ex2, ey2), 2)
    # Blips
    for bx2,by2 in [(x+5,y-9),(x-7,y+1),(x+3,y+6)]:
        pygame.draw.circle(surf, (0,255,200), (bx2,by2), 2)
    draw_text(surf, "NAV", font_tiny, col, x, y-20)

def draw_task_reactor_panel(surf, x, y, done, progress, t):
    col = PURPLE
    _draw_task_panel_base(surf, x, y, 52, 44, col, done, progress)
    # Core circle with glow
    glow = int(150+80*math.sin(t*0.1)) if not done else 200
    pygame.draw.circle(surf, (glow//3, 0, glow//2), (x, y-4), 14)
    pygame.draw.circle(surf, col, (x, y-4), 14, 2)
    # Radiation symbol spokes
    for i in range(3):
        ang = i*math.pi*2/3 + t*0.04
        rx2 = int(x + 10*math.cos(ang)); ry2 = int(y-4 + 10*math.sin(ang))
        pygame.draw.line(surf, (180,0,180), (x,y-4), (rx2,ry2), 2)
    pygame.draw.circle(surf, (220,80,220), (x, y-4), 4)
    draw_text(surf, "REACTOR", font_tiny, col, x, y-20)

def draw_task_life_panel(surf, x, y, done, progress, t):
    col = (80, 220, 80)
    _draw_task_panel_base(surf, x, y, 52, 44, col, done, progress)
    # O2 tank (same as ship part but smaller)
    pygame.draw.rect(surf,  (20,80,30), (x-5, y-14, 10, 18))
    pygame.draw.ellipse(surf,(20,80,30),(x-5, y-18, 10,  8))
    pygame.draw.ellipse(surf,(20,80,30),(x-5, y+ 2, 10,  8))
    pygame.draw.rect(surf,  col,        (x-5, y-14, 10, 18), 1)
    pygame.draw.ellipse(surf,col,       (x-5, y-18, 10,  8), 1)
    draw_text(surf, "O2", font_tiny, col, x, y-6)
    # Bubbles if active
    if not done:
        for i in range(3):
            by2 = y + 6 - int((t*0.8 + i*20) % 18)
            pygame.draw.circle(surf, (100,255,150),
                               (x + random.choice([-4,0,4]), by2), 2)
    draw_text(surf, "LIFE SUP", font_tiny, col, x, y-20)

def draw_task_comms_panel(surf, x, y, done, progress, t):
    col = GOLD
    _draw_task_panel_base(surf, x, y, 52, 44, col, done, progress)
    # Dish
    dish_pts = [(x-14,y+2),(x-10,y-8),(x,y-13),(x+10,y-8),(x+14,y+2)]
    pygame.draw.polygon(surf, (80,65,10), dish_pts)
    pygame.draw.polygon(surf, col,        dish_pts, 2)
    pygame.draw.line(surf, MOON_GREY, (x,y+2),(x+8,y-8), 2)
    pygame.draw.circle(surf, WHITE, (x+8,y-8), 2)
    # Signal rings
    sig = (t*0.06) % (math.pi*2)
    for i in range(2):
        rr = int(5 + i*5 + (sig/(math.pi*2))*5)
        sa = pygame.Surface((rr*2,rr*2),pygame.SRCALPHA)
        pygame.draw.circle(sa,(255,215,0,max(0,140-rr*10)),(rr,rr),rr,1)
        surf.blit(sa,(x+8-rr,y-8-rr))
    draw_text(surf, "COMMS", font_tiny, col, x, y-20)

_TASK_DRAW_FN = {
    "task_engine":  draw_task_engine_panel,
    "task_nav":     draw_task_nav_panel,
    "task_reactor": draw_task_reactor_panel,
    "task_life":    draw_task_life_panel,
    "task_comms":   draw_task_comms_panel,
}

# ── Decorative items drawn into each room ─────────────────────────────────
def _draw_room_decor(surf, cam_x, cam_y, t):
    """Draw fixed decorative items that make the ship feel alive."""
    HUD = S2_HUD
    def wp(tx, ty):  # world-tile to screen
        return tx*S2_TS - int(cam_x), ty*S2_TS - int(cam_y) + HUD

    # CAFETERIA – table + chairs + food dispenser
    for row_off in range(3):
        tx2, ty2 = wp(16, 3+row_off*2)
        pygame.draw.rect(surf,(60,40,20),(tx2,ty2,S2_TS*3,S2_TS-8))   # table
        pygame.draw.rect(surf,(80,55,25),(tx2,ty2,S2_TS*3,S2_TS-8),2)
        for cx2 in [tx2+8, tx2+S2_TS*3-14]:
            pygame.draw.rect(surf,(50,35,15),(cx2,ty2+S2_TS-5,10,8))  # chair
    # Food dispenser
    dx2,dy2=wp(13,2); pygame.draw.rect(surf,(40,30,60),(dx2,dy2,16,32))
    pygame.draw.rect(surf,(80,60,120),(dx2,dy2,16,32),1)
    blink=(t//20)%2; pygame.draw.circle(surf,(0,200,0) if blink else (0,80,0),(dx2+8,dy2+8),3)

    # WEAPONS – turret consoles
    for i in range(2):
        tx2,ty2=wp(29+i*3,2)
        pygame.draw.rect(surf,(60,10,10),(tx2,ty2,S2_TS*2,S2_TS+4))
        pygame.draw.rect(surf,(120,20,20),(tx2,ty2,S2_TS*2,S2_TS+4),2)
        pygame.draw.circle(surf,RED,(tx2+S2_TS,ty2+10),8)
        pygame.draw.circle(surf,(220,80,80),(tx2+S2_TS,ty2+10),4)
        # targeting cross
        pygame.draw.line(surf,BLOOD_RED,(tx2+S2_TS-6,ty2+10),(tx2+S2_TS+6,ty2+10),1)
        pygame.draw.line(surf,BLOOD_RED,(tx2+S2_TS,ty2+4),(tx2+S2_TS,ty2+16),1)

    # NAVIGATION – star chart console spanning full room
    tx2,ty2=wp(35,4)
    pygame.draw.rect(surf,(0,20,50),(tx2,ty2,S2_TS*4,S2_TS*2))
    pygame.draw.rect(surf,(0,80,160),(tx2,ty2,S2_TS*4,S2_TS*2),2)
    for _ in range(10):
        sx2=tx2+random.randint(4,S2_TS*4-4); sy2=ty2+random.randint(4,S2_TS*2-4)
        pygame.draw.circle(surf,WHITE,(sx2,sy2),1)
    # animated crosshair
    ch_x=tx2+S2_TS+int(12*math.sin(t*0.05)); ch_y=ty2+S2_TS//2
    pygame.draw.circle(surf,CYAN,(ch_x,ch_y),6,1)
    pygame.draw.line(surf,CYAN,(ch_x-8,ch_y),(ch_x+8,ch_y),1)
    pygame.draw.line(surf,CYAN,(ch_x,ch_y-8),(ch_x,ch_y+8),1)

    # REACTOR – glowing core pillar
    rx2,ry2=wp(4,12); rc=int(150+80*math.sin(t*0.08))
    for rr in range(18,4,-4):
        a=max(0,int(80*(rr-4)/14))
        rs=pygame.Surface((rr*2,rr*2),pygame.SRCALPHA)
        pygame.draw.circle(rs,(rc//2,0,rc,a),(rr,rr),rr)
        surf.blit(rs,(rx2+S2_TS-rr,ry2+S2_TS-rr))
    pygame.draw.circle(surf,(rc,rc//2,255),(rx2+S2_TS,ry2+S2_TS),10)

    # SECURITY – camera monitors grid
    for i in range(3):
        mx2,my2=wp(10,12+i)
        pygame.draw.rect(surf,(10,20,10),(mx2,my2,S2_TS+4,S2_TS-4))
        pygame.draw.rect(surf,(30,80,30),(mx2,my2,S2_TS+4,S2_TS-4),1)
        # tiny room view on screen
        if (t//30+i)%2==0:
            pygame.draw.circle(surf,(0,150,0),(mx2+S2_TS//2,my2+S2_TS//2-2),4)

    # MED-BAY – med beds + cross
    for i in range(2):
        bx2,by2=wp(18+i*4,13)
        pygame.draw.rect(surf,(20,60,50),(bx2,by2,S2_TS*3,S2_TS))
        pygame.draw.rect(surf,(40,120,90),(bx2,by2,S2_TS*3,S2_TS),2)
        # pillow
        pygame.draw.rect(surf,(200,200,220),(bx2+S2_TS*2+2,by2+4,12,10))
    # Red cross sign
    cx2,cy2=wp(21,12)
    pygame.draw.rect(surf,RED,(cx2+S2_TS//2-3,cy2,6,14))
    pygame.draw.rect(surf,RED,(cx2+S2_TS//2-7,cy2+4,14,6))

    # ELECTRICAL – fuse boxes + wiring
    for i in range(3):
        ex2,ey2=wp(5+i*2,20)
        pygame.draw.rect(surf,(50,40,0),(ex2,ey2,S2_TS-2,S2_TS+4))
        pygame.draw.rect(surf,GOLD,(ex2,ey2,S2_TS-2,S2_TS+4),1)
        # fuses
        for j in range(3):
            fcol=(220,220,0) if (t//15+i+j)%3!=0 else (220,80,0)
            pygame.draw.rect(surf,fcol,(ex2+4,ey2+4+j*8,S2_TS-10,5))

    # ENGINES – big thruster nozzles
    for tx3,ty3 in [(11,22),(25,22)]:
        ex2,ey2=wp(tx3,ty3)
        pygame.draw.polygon(surf,(80,50,20),
                            [(ex2,ey2),(ex2+S2_TS*2,ey2),(ex2+S2_TS*2+8,ey2+S2_TS),
                             (ex2-8,ey2+S2_TS)])
        pygame.draw.polygon(surf,ORANGE,
                            [(ex2,ey2),(ex2+S2_TS*2,ey2),(ex2+S2_TS*2+8,ey2+S2_TS),
                             (ex2-8,ey2+S2_TS)],2)
        # flame
        fh=int(10+8*abs(math.sin(t*0.15)))
        flame_pts=[(ex2+4,ey2+S2_TS),(ex2+S2_TS,ey2+S2_TS+fh),(ex2+S2_TS*2-4,ey2+S2_TS)]
        pygame.draw.polygon(surf,(255,160,20),flame_pts)
        pygame.draw.polygon(surf,(255,240,80),
                            [(ex2+S2_TS//2,ey2+S2_TS),(ex2+S2_TS,ey2+S2_TS+fh-4),
                             (ex2+S2_TS+S2_TS//2,ey2+S2_TS)])

    # STORAGE – crates
    for cx3,cy3 in [(17,21),(19,21),(21,21),(17,23),(19,23)]:
        cx2,cy2=wp(cx3,cy3)
        pygame.draw.rect(surf,(50,40,30),(cx2+2,cy2+2,S2_TS-4,S2_TS-4))
        pygame.draw.rect(surf,(80,65,45),(cx2+2,cy2+2,S2_TS-4,S2_TS-4),2)
        pygame.draw.line(surf,(60,50,35),(cx2+2,cy2+S2_TS//2),(cx2+S2_TS-2,cy2+S2_TS//2),1)
        pygame.draw.line(surf,(60,50,35),(cx2+S2_TS//2,cy2+2),(cx2+S2_TS//2,cy2+S2_TS-2),1)

class Level2:
    HUD_H = S2_HUD

    def __init__(self):
        # ── Camera ──────────────────────────────────────────
        self.cam_x = 0.0
        self.cam_y = 0.0

        # ── Player start: cafeteria centre ──────────────────
        self.px, self.py = _tile_to_world(19, 5)
        self.px = float(self.px); self.py = float(self.py)
        self.player_frame = 0
        self.speed = 2.5
        self.facing = 1

        # ── Experiment monster: starts in reactor ────────────
        self.ex, self.ey = _tile_to_world(4, 14)
        self.ex = float(self.ex); self.ey = float(self.ey)
        self.exp_frame = 0
        self.exp_speed = 3.0
        self.exp_path  = []
        self.path_timer = 0

        # ── Repair tasks ─────────────────────────────────────
        self.tasks = []
        for td in S2_TASKS_DEF:
            wx, wy = _tile_to_world(td["tile"][0], td["tile"][1])
            self.tasks.append({
                "name":     td["name"],
                "draw":     td["draw"],
                "col":      td["col"],
                "wx":       wx,
                "wy":       wy,
                "progress": 0.0,
                "done":     False,
            })

        # ── State ────────────────────────────────────────────
        self.active_task  = None
        self.player_hp    = 15
        self.player_max   = 15
        self.immune_timer = 0
        self.flash_msg    = ""
        self.flash_timer  = 0
        self.done         = False
        self.lose         = False
        self.t            = 0
        self.atk_timer    = 0

        # ── Pre-render map surface for performance ───────────
        self._map_surf = self._render_map()

    def _render_map(self):
        """Render the static ship map to a surface once."""
        w = S2_COLS * S2_TS
        h = S2_ROWS * S2_TS
        surf = pygame.Surface((w, h))
        surf.fill((0, 0, 0))

        # Floor tiles
        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                x = c * S2_TS; y = r * S2_TS
                t = S2_MAP[r][c]
                if t == S2_VOID:
                    pygame.draw.rect(surf, (4, 4, 8), (x, y, S2_TS, S2_TS))
                elif t == S2_FLOOR:
                    # Checkerboard floor
                    fc = (32, 34, 46) if (c+r)%2==0 else (28, 30, 40)
                    pygame.draw.rect(surf, fc, (x, y, S2_TS, S2_TS))
                    pygame.draw.rect(surf, (22, 24, 34), (x, y, S2_TS, S2_TS), 1)

        # Room accent strips (coloured border inside each room)
        for room in S2_ROOMS:
            c0, r0, cw, rh = room["rect"]
            rc = room["col"]
            # Top + bottom inner strip
            for c in range(c0, c0+cw):
                for strip_r, alpha in [(r0, 80), (r0+rh-1, 60)]:
                    sx = c*S2_TS; sy = strip_r*S2_TS
                    s2 = pygame.Surface((S2_TS, 4), pygame.SRCALPHA)
                    s2.fill((*rc, alpha))
                    surf.blit(s2, (sx, sy))
            # Room name label
            lx = (c0 + cw//2) * S2_TS
            ly = (r0 + 1) * S2_TS + 4
            label = font_tiny.render(room["name"], False, (*rc, 200))
            surf.blit(label, (lx - label.get_width()//2, ly))

        # Wall outlines: draw a border line where floor meets void
        for r in range(S2_ROWS):
            for c in range(S2_COLS):
                if S2_MAP[r][c] != S2_FLOOR:
                    continue
                x = c*S2_TS; y = r*S2_TS
                for nc, nr, side in [(c,r-1,"top"),(c,r+1,"bot"),(c-1,r,"left"),(c+1,r,"right")]:
                    if not (0<=nc<S2_COLS and 0<=nr<S2_ROWS) or S2_MAP[nr][nc] != S2_FLOOR:
                        wall_col = (70, 80, 110)
                        if side == "top":
                            pygame.draw.line(surf, wall_col, (x,y),(x+S2_TS,y), 3)
                        elif side == "bot":
                            pygame.draw.line(surf, wall_col, (x,y+S2_TS),(x+S2_TS,y+S2_TS), 3)
                        elif side == "left":
                            pygame.draw.line(surf, wall_col, (x,y),(x,y+S2_TS), 3)
                        elif side == "right":
                            pygame.draw.line(surf, wall_col, (x+S2_TS,y),(x+S2_TS,y+S2_TS), 3)
        return surf

    def _move(self, x, y, dx, dy, radius=11):
        nx = x + dx
        if not _s2_blocked(nx, y, radius):
            x = nx
        ny = y + dy
        if not _s2_blocked(x, ny, radius):
            y = ny
        return x, y

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.done = True   # skip level

    def update(self):
        self.t += 1
        self.player_frame += 1
        self.exp_frame    += 1
        if self.flash_timer  > 0: self.flash_timer  -= 1
        if self.immune_timer > 0: self.immune_timer -= 1

        # ── Player movement ──────────────────────────────────
        keys = pygame.key.get_pressed()
        mdx = mdy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: mdx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: mdx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: mdy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: mdy += 1
        if mdx and mdy: mdx *= 0.707; mdy *= 0.707
        if mdx: self.facing = mdx
        self.px, self.py = self._move(self.px, self.py,
                                       mdx*self.speed, mdy*self.speed)

        # ── Camera follows player ────────────────────────────
        vw = SCREEN_W; vh = SCREEN_H - self.HUD_H
        self.cam_x += (self.px - vw/2 - self.cam_x) * 0.1
        self.cam_y += (self.py - vh/2 - self.cam_y) * 0.1
        self.cam_x = clamp(self.cam_x, 0, max(0, S2_COLS*S2_TS - vw))
        self.cam_y = clamp(self.cam_y, 0, max(0, S2_ROWS*S2_TS - vh))

        # ── Task interaction ─────────────────────────────────
        self.active_task = None
        for task in self.tasks:
            if task["done"]: continue
            d = math.hypot(self.px - task["wx"], self.py - task["wy"])
            if d < 36:
                self.active_task = task
                if keys[pygame.K_e] or keys[pygame.K_SPACE]:
                    task["progress"] = min(100, task["progress"] + 0.4)
                    if task["progress"] >= 100:
                        task["done"]  = True
                        self.flash_msg   = f"{task['name']} REPAIRED!"
                        self.flash_timer = 90
                        spawn_particles(
                            int(task["wx"] - self.cam_x),
                            int(task["wy"] - self.cam_y) + self.HUD_H,
                            task["col"], 14, 3, 45)
                break

        if all(t["done"] for t in self.tasks):
            self.done = True

        # ── Experiment BFS chase ─────────────────────────────
        self.path_timer += 1
        if self.path_timer >= 20:
            self.path_timer = 0
            self.exp_path = _s2_bfs(self.ex, self.ey, self.px, self.py)

        if self.exp_path:
            wc, wr = self.exp_path[0]
            twx, twy = _tile_to_world(wc, wr)
            ddx = twx - self.ex; ddy = twy - self.ey
            dist_wp = math.hypot(ddx, ddy)
            if dist_wp < self.exp_speed + 1:
                self.exp_path.pop(0)
            else:
                self.ex += (ddx/dist_wp)*self.exp_speed
                self.ey += (ddy/dist_wp)*self.exp_speed

        # ── Catch check ──────────────────────────────────────
        dist = math.hypot(self.px-self.ex, self.py-self.ey)
        if dist < 32 and self.immune_timer <= 0:
            self.player_hp -= 4
            self.immune_timer = 70
            spawn_particles(
                int(self.px - self.cam_x),
                int(self.py - self.cam_y) + self.HUD_H,
                BLOOD_RED, 10, 3, 30)
            self.flash_msg   = "IT'S ATTACKING YOU!"
            self.flash_timer = 60
            if self.player_hp <= 0:
                self.lose = True

    def _ws(self, wx, wy):
        """World → screen."""
        return int(wx - self.cam_x), int(wy - self.cam_y) + self.HUD_H

    def draw(self, surf):
        # ── Map ─────────────────────────────────────────────
        surf.blit(self._map_surf, (-int(self.cam_x), -int(self.cam_y) + self.HUD_H))

        # ── Room decor (dynamic / animated) ─────────────────
        _draw_room_decor(surf, self.cam_x, self.cam_y, self.t)

        # ── Repair task panels ───────────────────────────────
        for task in self.tasks:
            sx, sy = self._ws(task["wx"], task["wy"])
            # Only draw if on screen
            if -60 < sx < SCREEN_W+60 and self.HUD_H-60 < sy < SCREEN_H+60:
                fn = _TASK_DRAW_FN.get(task["draw"])
                if fn:
                    fn(surf, sx, sy, task["done"], task["progress"], self.t)
                # Interaction prompt
                d = math.hypot(self.px-task["wx"], self.py-task["wy"])
                if d < 36 and not task["done"]:
                    pulse = int(200+55*math.sin(self.t*0.15))
                    draw_text(surf, "▶ HOLD [E] TO REPAIR", font_small,
                              (pulse, pulse, 60), SCREEN_W//2, SCREEN_H - 28)

        # ── Experiment ───────────────────────────────────────
        esx, esy = self._ws(self.ex, self.ey)
        if -60 < esx < SCREEN_W+60 and self.HUD_H-60 < esy < SCREEN_H+60:
            # Danger vignette when close
            d2p = math.hypot(self.px-self.ex, self.py-self.ey)
            if d2p < 150:
                a = int(clamp((150-d2p)/80*120, 0, 120))
                vs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                vs.fill((120, 0, 0, a))
                surf.blit(vs, (0,0))
            draw_failed_experiment(surf, esx, esy, self.exp_frame)

        # ── Player ───────────────────────────────────────────
        psx, psy = self._ws(self.px, self.py)
        if self.immune_timer <= 0 or self.immune_timer % 6 < 3:
            draw_astronaut(surf, psx, psy, self.player_frame, self.facing)

        update_particles(surf)

        # ── HUD ─────────────────────────────────────────────
        pygame.draw.rect(surf, (8, 8, 16), (0, 0, SCREEN_W, self.HUD_H))
        pygame.draw.line(surf, (50,50,80), (0, self.HUD_H),(SCREEN_W, self.HUD_H), 2)
        done_n = sum(1 for t in self.tasks if t["done"])
        draw_text(surf, f"LEVEL 2  —  REPAIR THE SHIP  [{done_n}/{len(self.tasks)}]",
                  font_small, MOON_GREY, SCREEN_W//2, 15)
        draw_hp_bar(surf, SCREEN_W-180, 26, 160, 18, self.player_hp, self.player_max, "HP")
        draw_text(surf, "WASD MOVE  |  E REPAIR", font_tiny, (80,80,110), 100, 37)
        # Skip button (testing)
        pygame.draw.rect(surf, (60, 20, 20), (SCREEN_W - 110, 4, 100, 18), border_radius=3)
        pygame.draw.rect(surf, (180, 60, 60), (SCREEN_W - 110, 4, 100, 18), 1, border_radius=3)
        draw_text(surf, "[F1] SKIP", font_tiny, (220, 120, 120), SCREEN_W - 60, 13)

        # Task progress mini-list (bottom-left)
        for i, task in enumerate(self.tasks):
            col = (60,200,60) if task["done"] else (180,180,60)
            icon = "✓" if task["done"] else f"{int(task['progress'])}%"
            draw_text_left(surf, f"{task['name']}: {icon}", font_tiny, col, 8, SCREEN_H-22-i*14)

        if self.flash_timer > 0:
            alpha = min(255, self.flash_timer*4)
            draw_text(surf, self.flash_msg, font_med, CYAN,
                      SCREEN_W//2, SCREEN_H//2 - 60, alpha)

