"""Global settings, colours, and fonts for ERROR 1969."""

import pygame
pygame.init()
pygame.font.init()

SCREEN_W, SCREEN_H = 800, 600
FPS = 60
GAME_TITLE = "ERROR 1969"

# ─────────────────────────────────────────────
#  COLOURS  (pixel-art palette)
# ─────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
DARK_GREY  = (20,  20,  30)
MOON_GREY  = (180, 180, 190)
MOON_DARK  = (90,  90, 100)
CRATER     = (60,  60,  70)
STAR_COL   = (220, 220, 255)
PURPLE     = (100,  40, 160)
DEEP_PURP  = (40,  10,  70)
CYAN       = (0,  220, 220)
GREEN_MON  = (60, 160,  60)
BLOOD_RED  = (180,  20,  20)
ORANGE     = (220, 140,  20)
GOLD       = (255, 215,   0)
RED        = (220,  30,  30)
BLUE_GLOW  = (40,  80, 220)
COSMIC_BLU = (20,  40, 120)
HP_GREEN   = (40, 200,  40)
HP_RED     = (200,  40,  40)
PANEL_BG   = (10,  10,  20, 200)
YELLOW     = (255, 240,  50)
LIGHT_GREY = (200, 200, 210)
LASER_RED  = (255,  40,  60)
VORTEX_PUR = (140,  30, 200)
SHIELD_BLU = (60, 180, 255)
POWER_GRN  = (40, 230,  80)

# ─────────────────────────────────────────────
#  FONTS  (pixel-style)
# ─────────────────────────────────────────────
def load_font(size):
    # Use monospace for a retro pixel feel
    for name in ("Courier New", "Courier", "monospace"):
        try:
            return pygame.font.SysFont(name, size, bold=True)
        except Exception:
            pass
    return pygame.font.Font(None, size)

font_tiny   = load_font(12)
font_small  = load_font(16)
font_med    = load_font(22)
font_large  = load_font(32)
font_title  = load_font(48)
font_huge   = load_font(64)
