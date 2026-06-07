import os
import math
import random
import pygame

from settings import *
from utils import *


# ─────────────────────────────────────────────
# ASSET PATHS
# ─────────────────────────────────────────────

BG_PATHS = [
    "assets/images/LVL3.png",
    "assets/images/LVL3.jpg",
    "assets/images/backgrounds/LVL3.png",
    "assets/images/backgrounds/LVL3.jpg",
]

ASTRO_FRAME_DIR = "assets/images/monsters/astronaut"
ASTRO_FRAME_COUNT = 10


# ─────────────────────────────────────────────
# LEVEL SETTINGS
# ─────────────────────────────────────────────

GROUND_Y = SCREEN_H - 105

PLAYER_W = 42
PLAYER_H = 52
PLAYER_SPEED = 4.2
PLAYER_JUMP = -12.5
GRAVITY = 0.65
BULLET_SPEED = 12

NORMAL_DAMAGE = 3
BOOST_DAMAGE = 5
BOOST_CHARGE_TIME = 90

BOOST_CHARGE_TIME = 90   # hold R for about 1.5 seconds at 60 FPS

BOSS_MAX_HP = 50
PLAYER_MAX_HP = 30


class Level3:
    def __init__(self):
        self.done = False
        self.lose = False
        self.t = 0

        # Background
        self.bg = self._load_background()

        # Player
        self.px = 110
        self.py = GROUND_Y
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.facing = 1
        self.player_hp = PLAYER_MAX_HP
        self.player_max = PLAYER_MAX_HP
        self.immune_timer = 0

        # Astronaut sprite frames
        self.astro_frames = self._load_astronaut_frames()
        self.player_frame = 0
        self.astro_anim_speed = 6

        # Weapon
        self.bullets = []
        self.shoot_cooldown = 0

        # Boost shot
        self.boost_charge = 0
        self.boost_ready = False
        self.boost_charging = False
        self.boost_flash_timer = 0

        # Boss
        self.boss_x = SCREEN_W - 165
        self.boss_y = GROUND_Y - 150
        self.boss_hp = BOSS_MAX_HP
        self.boss_max_hp = BOSS_MAX_HP
        self.boss_phase = 1
        self.boss_anim = 0
        self.boss_attack_timer = 0
        self.boss_voice_timer = 0
        self.boss_voice = ""

        # Weak point
        self.weak_point = {
            "x": self.boss_x,
            "y": self.boss_y,
            "r": 34,
            "active": True,
            "timer": 0,
        }

        # Boss attacks
        self.enemy_projectiles = []
        self.corruption_zones = []
        self.blackout_timer = 0
        self.blackout_active = False

        # Screen effects
        self.screen_shake = 0
        self.flash_msg = ""
        self.flash_timer = 0
        self.warning_timer = 120

        # Intro reveal
        self.reveal_timer = 120

    # ─────────────────────────────────────────────
    # ASSETS
    # ─────────────────────────────────────────────

    def _load_background(self):
        for path in BG_PATHS:
            if os.path.exists(path):
                img = pygame.image.load(path).convert()
                return pygame.transform.scale(img, (SCREEN_W, SCREEN_H))

        print("[WARNING] LVL3 background not found. Using fallback background.")
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        surf.fill((5, 5, 12))

        pygame.draw.rect(surf, (22, 22, 30), (0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
        pygame.draw.line(surf, (140, 30, 25), (0, GROUND_Y), (SCREEN_W, GROUND_Y), 2)

        for x in range(0, SCREEN_W, 80):
            pygame.draw.rect(surf, (18, 20, 30), (x, 80, 50, 260))
            pygame.draw.rect(surf, (70, 20, 20), (x, 80, 50, 260), 1)

        return surf

    def _load_astronaut_frames(self):
        frames = []

        for i in range(ASTRO_FRAME_COUNT):
            path = os.path.join(ASTRO_FRAME_DIR, f"ASTRO{i}.png")

            if not os.path.exists(path):
                print(f"[WARNING] Missing astronaut frame: {path}")
                frames.append(self._make_missing_astro_frame(i))
                continue

            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (PLAYER_W, PLAYER_H))
            frames.append(img)

        return frames

    def _make_missing_astro_frame(self, i):
        surf = pygame.Surface((PLAYER_W, PLAYER_H), pygame.SRCALPHA)

        pygame.draw.rect(surf, (210, 210, 210), (13, 20, 18, 24))
        pygame.draw.circle(surf, (220, 220, 220), (22, 14), 11)
        pygame.draw.rect(surf, (20, 70, 95), (16, 10, 12, 7))
        pygame.draw.line(surf, (230, 230, 230), (30, 28), (42, 25), 3)
        pygame.draw.rect(surf, (255, 90, 30), (40, 23, 8, 4))

        draw_text(surf, str(i), font_tiny, RED, PLAYER_W // 2, PLAYER_H - 8)
        return surf

    # ─────────────────────────────────────────────
    # INPUT
    # ─────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_j:
                self._shoot()

            elif event.key == pygame.K_r:
                self.boost_charging = True

            elif event.key == pygame.K_F1:
                self.done = True

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_r:
                # Release R to fire boost shot if fully charged
                if self.boost_ready:
                    self._shoot(boost=True)

                # Reset charge either way
                self.boost_charging = False
                self.boost_ready = False
                self.boost_charge = 0

    # ─────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────

    def update(self):
        if self.done or self.lose:
            return

        self.t += 1
        self.player_frame += 1
        self.boss_anim += 1

        if self.reveal_timer > 0:
            self.reveal_timer -= 1

        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.boost_flash_timer > 0:
            self.boost_flash_timer -= 1

        if self.immune_timer > 0:
            self.immune_timer -= 1

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.screen_shake > 0:
            self.screen_shake -= 1

        self._update_player()
        self._update_boost_charge()
        self._update_bullets()
        self._update_boss()
        self._update_enemy_projectiles()
        self._update_corruption_zones()
        self._update_blackout()

        if self.player_hp <= 0:
            self.lose = True

        if self.boss_hp <= 0:
            self.boss_hp = 0
            self.flash_msg = "MOON EATER DESTROYED"
            self.flash_timer = 120
            self.done = True

    def _update_player(self):
        keys = pygame.key.get_pressed()

        self.vx = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -PLAYER_SPEED
            self.facing = -1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = PLAYER_SPEED
            self.facing = 1

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = PLAYER_JUMP
            self.on_ground = False

        self.vy += GRAVITY

        self.px += self.vx
        self.py += self.vy

        # Arena boundaries
        self.px = clamp(self.px, 45, SCREEN_W - 250)

        # Floor collision
        if self.py >= GROUND_Y:
            self.py = GROUND_Y
            self.vy = 0
            self.on_ground = True

        # Corruption slow/damage
        player_rect = self._player_rect()

        for zone in self.corruption_zones:
            if player_rect.colliderect(zone["rect"]):
                if self.t % 35 == 0:
                    self._damage_player(1)
                self.px -= self.vx * 0.35

    def _update_boost_charge(self):
        if not self.boost_charging:
            return

        if self.boost_ready:
            return

        self.boost_charge += 1

        if self.boost_charge >= BOOST_CHARGE_TIME:
            self.boost_charge = BOOST_CHARGE_TIME
            self.boost_ready = True
            self.boost_flash_timer = 45
            self.flash_msg = "BOOST SHOT READY"
            self.flash_timer = 45

    def _update_bullets(self):
        for bullet in self.bullets[:]:
            bullet["x"] += bullet["vx"]
            bullet["life"] -= 1

            if bullet["x"] < -40 or bullet["x"] > SCREEN_W + 40 or bullet["life"] <= 0:
                self.bullets.remove(bullet)
                continue

            hit = False

            # 1. Weak point hit = full damage
            if self.weak_point["active"]:
                dx = bullet["x"] - self.weak_point["x"]
                dy = bullet["y"] - self.weak_point["y"]
                dist = math.hypot(dx, dy)

                if dist <= self.weak_point["r"] + 10:
                    self.boss_hp -= bullet["damage"]
                    self.screen_shake = 8 if bullet["power"] else 3

                    self.flash_msg = "CORE HIT"
                    self.flash_timer = 35

                    if bullet["power"]:
                        self.flash_msg = "BOOST HIT"
                        self.flash_timer = 60

                    hit = True

            # 2. Boss body hit = smaller damage
            # This prevents Phase 2 from feeling broken.
            if not hit:
                boss_body_rect = pygame.Rect(
                    int(self.boss_x - 80),
                    int(self.boss_y - 115),
                    160,
                    230
                )

                if boss_body_rect.collidepoint(bullet["x"], bullet["y"]):
                    body_damage = max(1, bullet["damage"] // 2)

                    self.boss_hp -= body_damage
                    self.screen_shake = 3

                    self.flash_msg = "BODY HIT"
                    self.flash_timer = 25

                    hit = True

            if hit:
                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                self._update_boss_phase()
                continue

    def _update_boss(self):
        self.boss_attack_timer += 1
        self.weak_point["timer"] += 1

        # Boss weak point pulses / shifts
        pulse_x = math.sin(self.t * 0.035) * 18
        pulse_y = math.sin(self.t * 0.055) * 14

        if self.boss_phase == 1:
            self.weak_point["x"] = self.boss_x + pulse_x
            self.weak_point["y"] = self.boss_y + pulse_y

        elif self.boss_phase == 2:
            self.weak_point["x"] = self.boss_x - 18 + pulse_x
            self.weak_point["y"] = self.boss_y - 35 + pulse_y

        else:
            self.weak_point["x"] = self.boss_x + pulse_x
            self.weak_point["y"] = self.boss_y + 42 + pulse_y

        # Attacks become faster by phase
        attack_rate = 115 if self.boss_phase == 1 else 85 if self.boss_phase == 2 else 62

        if self.boss_attack_timer >= attack_rate:
            self.boss_attack_timer = 0

            choice = random.choice(["projectile", "projectile", "corruption"])

            if self.boss_phase >= 3:
                choice = random.choice(["projectile", "corruption", "blackout"])

            if choice == "projectile":
                self._spawn_enemy_projectile()

            elif choice == "corruption":
                self._spawn_corruption_zone()

            elif choice == "blackout":
                self._trigger_blackout()

        # Voice line occasionally
        if self.boss_voice_timer > 0:
            self.boss_voice_timer -= 1
        elif random.random() < 0.004:
            self._boss_speak()

    def _update_boss_phase(self):
        hp_ratio = self.boss_hp / self.boss_max_hp

        old_phase = self.boss_phase

        if hp_ratio <= 0.33:
            self.boss_phase = 3
        elif hp_ratio <= 0.66:
            self.boss_phase = 2
        else:
            self.boss_phase = 1

        if self.boss_phase != old_phase:
            self.screen_shake = 16
            self._trigger_blackout()
            self._boss_speak(force=True)

    def _move_weak_point(self):
        # Brief flicker, mostly visual through phase positioning
        self.weak_point["active"] = True
        self.weak_point["timer"] = 0

    def _update_enemy_projectiles(self):
        for proj in self.enemy_projectiles[:]:
            proj["x"] += proj["vx"]
            proj["y"] += proj["vy"]
            proj["life"] -= 1

            if proj["life"] <= 0 or proj["x"] < -60:
                self.enemy_projectiles.remove(proj)
                continue

            if self._player_rect().collidepoint(proj["x"], proj["y"]):
                self._damage_player(2)

                if proj in self.enemy_projectiles:
                    self.enemy_projectiles.remove(proj)

    def _update_corruption_zones(self):
        for zone in self.corruption_zones[:]:
            zone["timer"] -= 1

            if zone["timer"] <= 0:
                self.corruption_zones.remove(zone)

    def _update_blackout(self):
        if self.blackout_timer > 0:
            self.blackout_timer -= 1
            self.blackout_active = True
        else:
            self.blackout_active = False

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _shoot(self, boost=False):
        if self.shoot_cooldown > 0:
            return

        self.shoot_cooldown = 10

        damage = BOOST_DAMAGE if boost else NORMAL_DAMAGE
        bullet_boost = boost

        if boost:
            self.screen_shake = 8
            self.flash_msg = "BOOST SHOT FIRED"
            self.flash_timer = 40

        bx = self.px + (28 * self.facing)
        by = self.py - 28

        self.bullets.append({
            "x": bx,
            "y": by,
            "vx": BULLET_SPEED * self.facing,
            "damage": damage,
            "power": bullet_boost,
            "life": 80,
        })

    def _spawn_enemy_projectile(self):
        start_x = self.boss_x - 35
        start_y = self.boss_y + random.randint(-40, 55)

        dx = self.px - start_x
        dy = (self.py - 28) - start_y
        dist = max(1, math.hypot(dx, dy))

        speed = 4.1 + self.boss_phase * 0.6

        self.enemy_projectiles.append({
            "x": start_x,
            "y": start_y,
            "vx": dx / dist * speed,
            "vy": dy / dist * speed,
            "life": 170,
        })

    def _spawn_corruption_zone(self):
        zone_w = random.randint(90, 150)
        zone_x = random.randint(90, SCREEN_W - 330)

        # Sometimes place near player, but not directly under them every time.
        if random.random() < 0.55:
            zone_x = int(clamp(self.px + random.randint(-120, 120), 70, SCREEN_W - 330))

        rect = pygame.Rect(zone_x, GROUND_Y - 16, zone_w, 18)

        self.corruption_zones.append({
            "rect": rect,
            "timer": 230 if self.boss_phase < 3 else 290,
        })

    def _trigger_blackout(self):
        self.blackout_timer = 95 if self.boss_phase < 3 else 130
        self.screen_shake = 12
        self.flash_msg = "POWER FAILURE"
        self.flash_timer = 70

    def _boss_speak(self, force=False):
        lines = [
            "YOU FIXED NOTHING.",
            "THE SHIP IS MINE.",
            "EARTH WILL NOT SEE YOU.",
            "YOUR SUIT IS A SHELL.",
            "COME CLOSER.",
        ]

        self.boss_voice = random.choice(lines)
        self.boss_voice_timer = 150 if force else 110

    def _damage_player(self, amount):
        if self.immune_timer > 0:
            return

        self.player_hp -= amount
        self.immune_timer = 55
        self.screen_shake = 8
        self.flash_msg = "SUIT DAMAGED"
        self.flash_timer = 40

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    def _player_rect(self):
        return pygame.Rect(
            int(self.px - PLAYER_W // 2),
            int(self.py - PLAYER_H),
            PLAYER_W,
            PLAYER_H,
        )

    def _apply_shake_offset(self):
        if self.screen_shake <= 0:
            return 0, 0

        return random.randint(-self.screen_shake, self.screen_shake), random.randint(-self.screen_shake, self.screen_shake)

    # ─────────────────────────────────────────────
    # DRAW
    # ─────────────────────────────────────────────

    def draw(self, surf):
        ox, oy = self._apply_shake_offset()

        # Background
        surf.blit(self.bg, (ox, oy))

        # Extra darkness over background
        dark = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 45))
        surf.blit(dark, (0, 0))

        # Ground overlay
        pygame.draw.rect(surf, (8, 8, 12), (0, GROUND_Y + 5, SCREEN_W, SCREEN_H - GROUND_Y))
        pygame.draw.line(surf, (160, 35, 25), (0, GROUND_Y), (SCREEN_W, GROUND_Y), 2)

        self._draw_environment_effects(surf)
        self._draw_corruption_zones(surf)
        self._draw_boss(surf)
        self._draw_weak_point(surf)
        self._draw_player(surf)
        self._draw_bullets(surf)
        self._draw_enemy_projectiles(surf)
        self._draw_lighting(surf)
        self._draw_hud(surf)
        self._draw_messages(surf)

    def _draw_environment_effects(self, surf):
        # Emergency flicker
        if self.t % 100 < 8:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((130, 0, 0, 35))
            surf.blit(overlay, (0, 0))

        # Sparks
        if self.t % 18 < 4:
            for _ in range(4):
                x = random.randint(120, SCREEN_W - 160)
                y = random.randint(120, GROUND_Y - 70)
                pygame.draw.rect(surf, (255, 150, 40), (x, y, 3, 3))
                pygame.draw.line(surf, (180, 50, 20), (x, y), (x + random.randint(-8, 8), y + random.randint(4, 12)), 1)

    def _draw_corruption_zones(self, surf):
        for zone in self.corruption_zones:
            rect = zone["rect"]
            pulse = int(45 + 25 * math.sin(self.t * 0.15))

            pygame.draw.rect(surf, (5, 0, 8), rect)
            pygame.draw.rect(surf, (80 + pulse, 0, 55), rect, 2)

            # veins
            for i in range(4):
                x1 = rect.x + 8 + i * 25
                y1 = rect.y + random.randint(2, 12)
                x2 = x1 + random.randint(15, 35)
                y2 = rect.y + random.randint(2, 14)
                pygame.draw.line(surf, (150, 10, 40), (x1, y1), (x2, y2), 1)

    def _draw_boss(self, surf):
        bx = int(self.boss_x)
        by = int(self.boss_y)

        pulse = math.sin(self.t * 0.06)
        body_w = int(135 + pulse * 8)
        body_h = int(210 + pulse * 10)

        # Organic aura
        aura = pygame.Surface((260, 330), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (80, 0, 90, 50), (40, 40, 180, 250))
        pygame.draw.ellipse(aura, (25, 0, 35, 160), (55, 55, 150, 220))
        surf.blit(aura, (bx - 130, by - 155))

        # Main dark body
        pygame.draw.ellipse(
            surf,
            (8, 0, 16),
            (bx - body_w // 2, by - body_h // 2, body_w, body_h)
        )

        pygame.draw.ellipse(
            surf,
            (70, 0, 85),
            (bx - body_w // 2, by - body_h // 2, body_w, body_h),
            3
        )

        # Tendrils
        for i in range(9):
            ang = i * 0.7 + self.t * 0.035
            length = 85 + 20 * math.sin(self.t * 0.04 + i)
            sx = bx + int(math.cos(ang) * 35)
            sy = by + int(math.sin(ang) * 70)
            ex = sx + int(math.cos(ang) * length)
            ey = sy + int(math.sin(ang) * length * 0.4)

            pygame.draw.line(surf, (20, 0, 35), (sx, sy), (ex, ey), 8)
            pygame.draw.line(surf, (105, 0, 90), (sx, sy), (ex, ey), 2)

        # Boss core glow
        core_r = int(28 + 5 * math.sin(self.t * 0.12))
        pygame.draw.circle(surf, (120, 20, 0), (bx, by), core_r + 12)
        pygame.draw.circle(surf, (255, 85, 20), (bx, by), core_r)
        pygame.draw.circle(surf, (255, 210, 70), (bx, by), max(5, core_r // 3))

    def _draw_weak_point(self, surf):
        if not self.weak_point["active"]:
            return

        x = int(self.weak_point["x"])
        y = int(self.weak_point["y"])
        r = self.weak_point["r"]

        pulse = int(180 + 60 * math.sin(self.t * 0.18))

        pygame.draw.circle(surf, (255, 120, 20), (x, y), r + 8, 2)
        pygame.draw.circle(surf, (pulse, 45, 20), (x, y), r)
        pygame.draw.circle(surf, (255, 220, 80), (x, y), max(4, r // 3))

    def _draw_player(self, surf):
        if self.immune_timer > 0 and self.immune_timer % 8 >= 4:
            return

        moving = abs(self.vx) > 0.1
        frame_index = (self.player_frame // self.astro_anim_speed) % len(self.astro_frames)
        img = self.astro_frames[frame_index]

        # Assumes ASTRO faces right by default
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)

        rect = img.get_rect(midbottom=(int(self.px), int(self.py)))
        surf.blit(img, rect)

        # Weapon line if sprite does not visibly show gun
        gun_y = int(self.py - 30)
        gun_x = int(self.px + self.facing * 22)
        pygame.draw.line(surf, (180, 180, 160), (int(self.px), gun_y), (gun_x, gun_y - 2), 3)
        pygame.draw.rect(surf, (255, 110, 30), (gun_x, gun_y - 4, 8 * self.facing, 4))

    def _draw_bullets(self, surf):
        for bullet in self.bullets:
            x = int(bullet["x"])
            y = int(bullet["y"])

            if bullet["power"]:
                pygame.draw.circle(surf, (255, 145, 20), (x, y), 8)
                pygame.draw.circle(surf, (255, 40, 30), (x, y), 15, 2)
            else:
                pygame.draw.circle(surf, (255, 220, 80), (x, y), 4)

    def _draw_enemy_projectiles(self, surf):
        for proj in self.enemy_projectiles:
            x = int(proj["x"])
            y = int(proj["y"])

            pygame.draw.circle(surf, (60, 255, 100), (x, y), 7)
            pygame.draw.circle(surf, (0, 120, 50), (x, y), 13, 2)

    def _draw_lighting(self, surf):
        if self.blackout_active:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))

            # Cut visibility around player and boss core
            pygame.draw.circle(overlay, (0, 0, 0, 30), (int(self.px), int(self.py - 30)), 105)
            pygame.draw.circle(overlay, (0, 0, 0, 60), (int(self.weak_point["x"]), int(self.weak_point["y"])), 95)

            surf.blit(overlay, (0, 0))

        # subtle scanlines
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 5):
            pygame.draw.line(scan, (255, 255, 255, 7), (0, y), (SCREEN_W, y))
        surf.blit(scan, (0, 0))

    def _draw_hud(self, surf):
        hud_h = 78

        pygame.draw.rect(surf, (3, 4, 8), (0, 0, SCREEN_W, hud_h))
        pygame.draw.line(surf, (120, 25, 18), (0, hud_h - 1), (SCREEN_W, hud_h - 1), 2)

        # Mission
        draw_text_left(surf, "MISSION", font_tiny, (120, 55, 45), 18, 10)
        draw_text_left(surf, "ELIMINATE THREAT", font_small, (235, 55, 35), 18, 28)

        # Boss HP
        boss_bar_x = 250
        boss_bar_y = 18
        boss_bar_w = 290
        boss_bar_h = 14

        draw_text(surf, "MOON EATER", font_tiny, (255, 125, 20), boss_bar_x + boss_bar_w // 2, 10)

        pygame.draw.rect(surf, (30, 5, 5), (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h))
        pygame.draw.rect(surf, (160, 25, 20), (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h), 1)

        hp_w = int(boss_bar_w * (self.boss_hp / self.boss_max_hp))
        if hp_w > 0:
            pygame.draw.rect(surf, (220, 45, 35), (boss_bar_x, boss_bar_y, hp_w, boss_bar_h))

        draw_text(surf, f"PHASE {self.boss_phase}", font_tiny, (120, 55, 45), boss_bar_x + boss_bar_w // 2, 40)

        # Ammo
        # Weapon info
        draw_text_left(
            surf,
            "J SHOOT  |  HOLD R BOOST",
            font_tiny,
            (255, 220, 80),
            18,
            54
        )

        # Boost charge
        charge_x = 250
        charge_y = 55
        charge_w = 210
        charge_h = 8

        pygame.draw.rect(surf, (25, 8, 5), (charge_x, charge_y, charge_w, charge_h))

        charge_ratio = self.boost_charge / BOOST_CHARGE_TIME
        pygame.draw.rect(
            surf,
            (255, 125, 20),
            (charge_x, charge_y, int(charge_w * charge_ratio), charge_h)
        )
        pygame.draw.rect(surf, (160, 25, 20), (charge_x, charge_y, charge_w, charge_h), 1)

        if self.boost_ready:
            text_col = (255, 150, 40) if self.t % 30 < 15 else (255, 50, 40)
            draw_text_left(surf, "BOOST READY - RELEASE R", font_tiny, text_col, charge_x + charge_w + 12, 50)
        elif self.boost_charging:
            draw_text_left(surf, "CHARGING BOOST", font_tiny, (180, 90, 45), charge_x + charge_w + 12, 50)
        else:
            draw_text_left(surf, "BOOST SHOT", font_tiny, (120, 65, 45), charge_x + charge_w + 12, 50)

        # Player HP
        suit_x = SCREEN_W - 175
        draw_text_left(surf, "SUIT", font_tiny, (0, 130, 55), suit_x, 10)

        bar_x = suit_x
        bar_y = 29
        bar_w = 115
        bar_h = 11

        pygame.draw.rect(surf, (5, 25, 8), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surf, (0, 120, 45), (bar_x, bar_y, bar_w, bar_h), 1)

        fill = int(bar_w * (self.player_hp / self.player_max))
        if fill > 0:
            pygame.draw.rect(surf, (0, 235, 80), (bar_x, bar_y, fill, bar_h))

        draw_text_left(surf, f"{self.player_hp}/{self.player_max}", font_small, (0, 235, 80), suit_x, 47)

    def _draw_messages(self, surf):
        if self.boss_voice_timer > 0 and self.boss_voice:
            draw_text(
                surf,
                f'"{self.boss_voice}"',
                font_med,
                (180, 40, 50),
                SCREEN_W // 2,
                110
            )

        if self.flash_timer > 0 and self.flash_msg:
            alpha = min(255, self.flash_timer * 5)
            draw_text(
                surf,
                self.flash_msg,
                font_med,
                (255, 140, 40),
                SCREEN_W // 2,
                SCREEN_H - 55,
                alpha
            )

        if self.reveal_timer > 0:
            alpha = min(255, self.reveal_timer * 3)
            draw_text(
                surf,
                "FINAL ENCOUNTER",
                font_large,
                (235, 55, 35),
                SCREEN_W // 2,
                SCREEN_H // 2 - 80,
                alpha
            )
            draw_text(
                surf,
                "THE MOON EATER HAS ENTERED THE SHIP",
                font_small,
                (160, 75, 60),
                SCREEN_W // 2,
                SCREEN_H // 2 - 35,
                alpha
            )