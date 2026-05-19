"""Title, dialogue, win/game-over, and transition screens."""

import pygame
import math
from settings import *
from utils import *
from core.particles import spawn_particles, update_particles
from graphics.sprites import *

# ─────────────────────────────────────────────
#  CUTSCENE / DIALOGUE SYSTEM
# ─────────────────────────────────────────────
class TextScene:
    """Shows scrolling text lines, press SPACE / ENTER to advance."""
    def __init__(self, lines, bg_colour=DARK_GREY, title="", draw_fn=None):
        self.lines     = lines
        self.bg_colour = bg_colour
        self.title     = title
        self.draw_fn   = draw_fn   # optional extra drawing
        self.idx       = 0         # current line
        self.char_idx  = 0         # typewriter char pos
        self.timer     = 0
        self.done      = False
        self.t         = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
            if self.done or self.idx >= len(self.lines):
                self.done = True
                return
            if self.char_idx < len(self.lines[self.idx]):
                self.char_idx = len(self.lines[self.idx])
            else:
                self.idx += 1
                self.char_idx = 0
                if self.idx >= len(self.lines):
                    self.done = True

    def update(self):
        self.t += 1
        if self.done or self.idx >= len(self.lines):
            self.done = True
            return
        if self.char_idx < len(self.lines[self.idx]):
            self.char_idx += 2   # typewriter speed

    def draw(self, surf):
        surf.fill(self.bg_colour)
        draw_stars(surf, self.t / 60)
        if self.draw_fn:
            self.draw_fn(surf, self.t)

        if self.title:
            draw_text(surf, self.title, font_large, GOLD, SCREEN_W // 2, 60)

        if self.done or self.idx >= len(self.lines):
            return

        # Text box
        box_y = SCREEN_H // 2 - 60
        pygame.draw.rect(surf, (5, 5, 15, 220),
                         (60, box_y, SCREEN_W - 120, 160))
        pygame.draw.rect(surf, MOON_GREY,
                         (60, box_y, SCREEN_W - 120, 160), 2)

        # Current line (typewriter)
        line  = self.lines[self.idx]
        shown = line[:self.char_idx]
        # Word-wrap at ~60 chars
        words   = shown.split(" ")
        rows    = []
        cur_row = ""
        for w in words:
            if len(cur_row) + len(w) + 1 <= 58:
                cur_row += ("" if cur_row == "" else " ") + w
            else:
                rows.append(cur_row)
                cur_row = w
        if cur_row:
            rows.append(cur_row)
        for i, row in enumerate(rows[-4:]):
            draw_text_left(surf, row, font_small, WHITE, 80, box_y + 16 + i * 28)

        # Prompt
        if self.char_idx >= len(line):
            blink = int(self.t * 0.1) % 2 == 0
            if blink:
                draw_text(surf, "▶ PRESS SPACE TO CONTINUE", font_tiny,
                          LIGHT_GREY, SCREEN_W // 2, box_y + 140)

        # Progress indicator
        draw_text(surf, f"[{self.idx + 1}/{len(self.lines)}]", font_tiny,
                  (80, 80, 100), SCREEN_W - 100, box_y + 150)

# ─────────────────────────────────────────────
#  TITLE SCREEN
# ─────────────────────────────────────────────
class TitleScreen:
    def __init__(self):
        self.t = 0
        self.done = False
        self.glitch_timer = 0
        self.glitch_offset = 0

        self.bg = pygame.image.load("assets/images/MENU.png").convert()
        self.bg = pygame.transform.scale(self.bg, (SCREEN_W, SCREEN_H))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.done = True

    def update(self):
        self.t += 1

        if random.random() < 0.08:
            self.glitch_timer = random.randint(3, 8)
            self.glitch_offset = random.randint(-6, 6)

        if self.glitch_timer > 0:
            self.glitch_timer -= 1
        else:
            self.glitch_offset = 0

    def draw_glitch_title(self, surf):
        title = "ERROR 1969"
        base_y = 145
        glitch_x = self.glitch_offset

        flicker = random.randint(180, 255) if self.t % 8 < 5 else random.randint(90, 170)

        if self.glitch_timer > 0:
            draw_text(
                surf, title, font_huge, (255, 0, 60),
                SCREEN_W // 2 + glitch_x - 4,
                base_y + random.randint(-2, 2),
                flicker
            )

            draw_text(
                surf, title, font_huge, (0, 220, 255),
                SCREEN_W // 2 + glitch_x + 4,
                base_y + random.randint(-2, 2),
                flicker
            )

            for _ in range(5):
                y = random.randint(90, 190)
                x = random.randint(120, 260)
                w = random.randint(180, 420)
                h = random.randint(2, 6)
                pygame.draw.rect(surf, (180, 0, 40), (x, y, w, h))

        draw_text(
            surf, title, font_huge, (235, 235, 220),
            SCREEN_W // 2 + glitch_x,
            base_y,
            flicker
        )

        if self.t % 120 < 90:
            draw_text(
                surf,
                "SIGNAL CORRUPTED // LUNAR ENTITY DETECTED",
                font_tiny,
                (150, 40, 60),
                SCREEN_W // 2,
                base_y + 58
            )

    def draw(self, surf):
        # Draw PNG background first
        surf.blit(self.bg, (0, 0))

        # Optional dark overlay for horror mood
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 45))
        surf.blit(overlay, (0, 0))

        # Glitch title
        self.draw_glitch_title(surf)

        # Warning text
        if self.t % 180 < 120:
            draw_text(
                surf,
                "DO NOT LOOK DIRECTLY AT THE MOON",
                font_small,
                (160, 45, 55),
                SCREEN_W // 2,
                235
            )

        # Press space
        blink = int(self.t * 0.045) % 2 == 0
        if blink:
            draw_text(
                surf,
                "▶ PRESS SPACE TO START ◀",
                font_med,
                (230, 230, 210),
                SCREEN_W // 2,
                430
            )

        draw_text(
            surf,
            "GROUP // APD2F2509CSAI",
            font_tiny,
            (80, 80, 95),
            SCREEN_W // 2,
            SCREEN_H - 14
        )

# ─────────────────────────────────────────────
#  GAME OVER / WIN SCREENS
# ─────────────────────────────────────────────
class GameOverScreen:
    def __init__(self, win=False):
        self.win  = win
        self.t    = 0
        self.done = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
            self.done = True

    def update(self):
        self.t += 1

    def draw(self, surf):
        surf.fill(DARK_GREY)
        draw_stars(surf, self.t / 60)

        if self.win:
            # Flying ship
            ship_x = int(SCREEN_W * 0.1 + (SCREEN_W * 0.8) * min(1, self.t / 200))
            ship_y = int(SCREEN_H // 2 - self.t * 0.5)
            draw_ship(surf, ship_x, clamp(ship_y, 50, SCREEN_H - 50),
                      self.t, False)
            spawn_particles(ship_x, clamp(ship_y + 12, 50, SCREEN_H - 50),
                            ORANGE, 2, 1.5, 20, 3)
            update_particles(surf)

            glow = int(200 + 55 * math.sin(self.t * 0.05))
            draw_text(surf, "MISSION COMPLETE!", font_title, (glow, glow, 80),
                      SCREEN_W // 2, 180)
            draw_text(surf, "YOU MADE IT HOME!", font_large, GOLD,
                      SCREEN_W // 2, 250)
            draw_text(surf, "PEW PEW — THE MOON EATER IS DEFEATED!", font_med, CYAN,
                      SCREEN_W // 2, 310)
            draw_text(surf, "APOLLO ERROR 1969 — MISSION SUCCESS", font_small, MOON_GREY,
                      SCREEN_W // 2, 360)
        else:
            draw_text(surf, "GAME OVER", font_huge, BLOOD_RED,
                      SCREEN_W // 2, 200)
            draw_text(surf, "THE MOON HAS CLAIMED YOU...", font_large, MOON_GREY,
                      SCREEN_W // 2, 290)
            draw_text(surf, "STRANDED ON THE LUNAR SURFACE", font_med, (150, 150, 170),
                      SCREEN_W // 2, 340)

        blink = int(self.t * 0.04) % 2 == 0
        if blink:
            draw_text(surf, "PRESS SPACE TO RETURN TO TITLE", font_med,
                      WHITE, SCREEN_W // 2, 440)

# ─────────────────────────────────────────────
#  TRANSITION OVERLAY
# ─────────────────────────────────────────────
class Transition:
    def __init__(self, fade_in=True, duration=60):
        self.fade_in  = fade_in
        self.duration = duration
        self.timer    = 0
        self.done     = False

    def update(self):
        self.timer += 1
        if self.timer >= self.duration:
            self.done = True

    def draw(self, surf):
        ratio = self.timer / self.duration
        alpha = int(255 * (1 - ratio) if self.fade_in else 255 * ratio)
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.fill(BLACK)
        s.set_alpha(alpha)
        surf.blit(s, (0, 0))
