"""Small drawing callbacks used by TextScene cutscenes."""

from settings import *
from graphics.sprites import *

def intro_draw(surf, t):
    draw_moon_eater(surf, SCREEN_W - 120, 200, t, 1.0)
    draw_ship(surf, 200, 380, t, True)

def cutscene1_draw(surf, t):
    draw_moon_surface(surf, 380)
    draw_ship(surf, 200, 354, t, True)
    draw_watcher(surf, SCREEN_W - 150, 300, t, 1.0)
    # Parts scattered
    for i, (px2, py2) in enumerate([(350, 340), (500, 340), (600, 360), (420, 320), (480, 370)]):
        draw_ship_part(surf, px2, py2, i)

def repair_intro_draw(surf, t):
    draw_ship(surf, SCREEN_W // 2, 280, t, True)
    draw_failed_experiment(surf, SCREEN_W - 130, 300, t, 1.0)

def boss_intro_draw(surf, t):
    draw_moon_eater(surf, SCREEN_W // 2, 220, t, 1.0)

def win_fly_draw(surf, t):
    draw_ship(surf, SCREEN_W // 2, 300, t, False)
