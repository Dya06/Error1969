"""Level 3: final Moon Eater boss fight."""

import pygame
import math
from settings import *
from utils import *
from core.particles import spawn_particles, update_particles
from graphics.sprites import *

# ─────────────────────────────────────────────
#  LEVEL 3 – BOSS FIGHT
# ─────────────────────────────────────────────
class Level3:
    def __init__(self):
        self.player_x = SCREEN_W // 2
        self.player_y = SCREEN_H - 90
        self.player_frame = 0
        self.speed      = 4
        self.boss_x     = SCREEN_W // 2
        self.boss_y     = 160
        self.boss_frame = 0
        self.boss_hp    = 200
        self.boss_max   = 200
        self.player_hp  = 20
        self.player_max = 20
        self.bullets    = []   # player bullets [(x,y,vy)]
        self.boss_proj  = []   # boss projectiles [(x,y,vx,vy)]
        self.shoot_cd   = 0
        self.immune_timer = 0
        self.atk_timer  = 0
        self.flash_msg  = ""
        self.flash_timer = 0
        self.done       = False
        self.lose       = False
        self.t          = 0
        self.phase      = 1   # phase 2 at 50% HP
        self.phase_changed = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.done = True   # skip level
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if self.shoot_cd <= 0:
                    self.bullets.append([self.player_x, self.player_y - 20, -8])
                    self.shoot_cd = 12
                    spawn_particles(int(self.player_x), int(self.player_y - 20),
                                    YELLOW, 4, 1.5, 12)

    def update(self):
        self.t += 1
        self.player_frame += 1
        self.boss_frame   += 1
        if self.flash_timer > 0:  self.flash_timer -= 1
        if self.immune_timer > 0: self.immune_timer -= 1
        if self.shoot_cd > 0:     self.shoot_cd    -= 1

        # Player movement
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        self.player_x = clamp(self.player_x + dx * self.speed, 20, SCREEN_W - 20)

        # Shoot if space/up held
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.shoot_cd <= 0:
            self.bullets.append([self.player_x, self.player_y - 20, -8])
            self.shoot_cd = 12
            spawn_particles(int(self.player_x), int(self.player_y - 20),
                            YELLOW, 3, 1.5, 12)

        # Move player bullets
        for b in self.bullets[:]:
            b[1] += b[2]
            if b[1] < 0:
                self.bullets.remove(b)
                continue
            # Hit boss
            if (math.hypot(b[0] - self.boss_x, b[1] - self.boss_y) < 55):
                self.boss_hp -= 2
                self.bullets.remove(b)
                spawn_particles(int(self.boss_x), int(self.boss_y),
                                BLUE_GLOW, 5, 2, 20)
                if self.boss_hp <= 0:
                    self.boss_hp = 0
                    self.done    = True

        # Phase 2
        if self.boss_hp < self.boss_max * 0.5 and self.phase == 1:
            self.phase = 2
            self.flash_msg   = "MOON EATER ENRAGES!"
            self.flash_timer = 100
            spawn_particles(self.boss_x, self.boss_y, RED, 20, 5, 60, 5)

        # Boss movement (figure-8 / sine)
        spd = 1.2 if self.phase == 1 else 1.8
        self.boss_x = SCREEN_W // 2 + int(200 * math.sin(self.t * 0.015 * spd))
        self.boss_y = 160 + int(40  * math.sin(self.t * 0.03 * spd))

        # Boss shoots
        self.atk_timer += 1
        interval = 55 if self.phase == 1 else 30
        if self.atk_timer > interval:
            self.atk_timer = 0
            # Spray pattern
            shot_count = 3 if self.phase == 1 else 5
            for i in range(shot_count):
                angle = math.pi / 2 + (i - (shot_count - 1) / 2) * 0.35
                bvx = math.cos(angle) * 4.5
                bvy = math.sin(angle) * 4.5
                self.boss_proj.append([self.boss_x, self.boss_y + 50, bvx, bvy])

        # Move boss projectiles
        for b in self.boss_proj[:]:
            b[0] += b[2]; b[1] += b[3]
            if not (0 <= b[0] <= SCREEN_W and 0 <= b[1] <= SCREEN_H + 50):
                self.boss_proj.remove(b)
                continue
            if (math.hypot(b[0] - self.player_x, b[1] - self.player_y) < 18
                    and self.immune_timer <= 0):
                self.player_hp -= 4
                self.immune_timer = 50
                self.boss_proj.remove(b)
                spawn_particles(int(self.player_x), int(self.player_y),
                                BLOOD_RED, 8, 2, 25)
                if self.player_hp <= 0:
                    self.lose = True

    def draw(self, surf):
        # Space background
        surf.fill(COSMIC_BLU)
        draw_stars(surf, self.t / 60)

        # Cosmic nebula blobs
        for i in range(3):
            cx2 = 150 + i * 250
            cy2 = 80 + int(20 * math.sin(self.t * 0.01 + i))
            s = pygame.Surface((120, 80), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (40, 20, 80, 60), (0, 0, 120, 80))
            surf.blit(s, (cx2 - 60, cy2 - 40))

        # Moon Eater
        draw_moon_eater(surf, self.boss_x, self.boss_y,
                        self.boss_frame, self.boss_hp / self.boss_max)

        # Boss projectiles
        for b in self.boss_proj:
            draw_bullet(surf, b[0], b[1], BLUE_GLOW)

        # Player bullets
        for b in self.bullets:
            draw_bullet(surf, b[0], b[1], YELLOW)

        # Player ship (bottom)
        if self.immune_timer <= 0 or self.immune_timer % 6 < 3:
            draw_ship(surf, int(self.player_x), int(self.player_y), self.player_frame, False)

        update_particles(surf)

        # HUD
        pygame.draw.rect(surf, (10, 10, 20), (0, 0, SCREEN_W, 55))
        draw_text(surf, "LEVEL 3  –  DEFEAT THE MOON EATER!", font_small, MOON_GREY,
                  SCREEN_W // 2, 14)
        draw_hp_bar(surf, 20, 22, 160, 20, self.player_hp, self.player_max, "SHIP")
        draw_hp_bar(surf, SCREEN_W - 180, 22, 160, 20, self.boss_hp, self.boss_max, "BOSS")
        ph_col = RED if self.phase == 2 else CYAN
        draw_text(surf, f"PHASE {self.phase}", font_small, ph_col, SCREEN_W // 2, 38)
        draw_text(surf, "← → MOVE  |  Z / SPACE TO SHOOT", font_tiny, (100, 100, 130),
                  SCREEN_W // 2, SCREEN_H - 12)
        # Skip button (testing)
        pygame.draw.rect(surf, (60, 20, 20), (SCREEN_W - 110, 4, 100, 18), border_radius=3)
        pygame.draw.rect(surf, (180, 60, 60), (SCREEN_W - 110, 4, 100, 18), 1, border_radius=3)
        draw_text(surf, "[F1] SKIP", font_tiny, (220, 120, 120), SCREEN_W - 60, 13)

        if self.flash_timer > 0:
            alpha = min(255, self.flash_timer * 3)
            draw_text(surf, self.flash_msg, font_med, RED,
                      SCREEN_W // 2, SCREEN_H // 2, alpha)

