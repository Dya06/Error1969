"""Reusable UI/math helper functions."""

import pygame
import math
import random
from settings import *

def draw_text(surf, text, font, colour, cx, cy, alpha=255):
    s = font.render(text, False, colour)
    s.set_alpha(alpha)
    r = s.get_rect(center=(cx, cy))
    surf.blit(s, r)

def draw_text_left(surf, text, font, colour, x, y):
    s = font.render(text, False, colour)
    surf.blit(s, (x, y))

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def draw_pixel_rect(surf, colour, rect, border=0):
    pygame.draw.rect(surf, colour, rect, border)

def draw_pixel_circle(surf, colour, pos, r):
    pygame.draw.circle(surf, colour, pos, r)

def draw_hp_bar(surf, x, y, w, h, hp, max_hp, label="HP"):
    ratio = max(0, hp / max_hp)
    pygame.draw.rect(surf, (40, 40, 40), (x, y, w, h))
    bar_col = HP_GREEN if ratio > 0.5 else (ORANGE if ratio > 0.25 else HP_RED)
    pygame.draw.rect(surf, bar_col, (x, y, int(w * ratio), h))
    pygame.draw.rect(surf, WHITE, (x, y, w, h), 1)
    draw_text(surf, f"{label} {int(hp)}/{int(max_hp)}", font_tiny, WHITE, x + w // 2, y + h // 2)

def load_sound(path, volume=1.0):
    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(volume)
        return snd
    except Exception as e:
        print(f"[WARNING] Failed to load sound {path}: {e}")
        return None

def play_music(path, loops=-1, volume=0.6):
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
    except Exception as e:
        print(f"[WARNING] Failed to play music {path}: {e}")

def stop_music(fade_ms=0):
    try:
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
    except Exception:
        pass

stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
          random.randint(1, 3), random.random()) for _ in range(200)]

def draw_stars(surf, t):
    for sx, sy, sr, phase in stars:
        brightness = int(180 + 75 * math.sin(t * 2 + phase * 10))
        pygame.draw.circle(surf, (brightness, brightness, min(255, brightness + 40)), (sx, sy), sr)