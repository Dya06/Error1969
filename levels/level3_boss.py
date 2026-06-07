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

ASTRO3_FRAME_DIR = "assets/images/monsters/astro3"

ASTRO_FRAME_COUNT = 5       # ASTRO0 - ASTRO4
ASTRO_SHOOT_COUNT = 4       # ASTROS0 - ASTROS3
BULLET_FRAME_COUNT = 9      # BULLET1 - BULLET9

ME_FRAME_DIR = "assets/images/monsters/moon_eater"
ME_FRAME_COUNT = 8

ACID_FRAME_DIR = ME_FRAME_DIR
ACID_FRAME_COUNT = 8


# ─────────────────────────────────────────────
# LEVEL SETTINGS
# ─────────────────────────────────────────────

GROUND_Y = SCREEN_H - 105
BOTTOM_HUD_H = 82
PLAY_AREA_BOTTOM = SCREEN_H - BOTTOM_HUD_H

PLAYER_W = 100
PLAYER_H = 100
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


class DisintegrationParticle:
    def __init__(self, x, y, color=(255, 80, 30), block_size=6):
        self.x = x
        self.y = y
        self.dx = random.uniform(-3.5, 3.5)
        self.dy = random.uniform(-4.5, 2.0)
        self.life = random.randint(45, 95)
        self.max_life = self.life
        self.block_size = block_size
        self.color = color

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.12
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return

        alpha = int(255 * (self.life / self.max_life))
        particle_surf = pygame.Surface((self.block_size, self.block_size), pygame.SRCALPHA)
        particle_surf.fill((*self.color, alpha))
        surf.blit(particle_surf, (int(self.x), int(self.y)))

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
        self.astro_frames = self._load_astro3_frames()
        self.astro_shoot_frames = self._load_astro3_shoot_frames()
        self.bullet_frames = self._load_bullet_frames()

        self.player_frame = 0
        self.astro_anim_speed = 6

        self.shooting_timer = 0
        self.shooting_anim_speed = 4

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
        self.me_frames = self._load_moon_eater_frames()
        self.me_anim_speed = 7
        self.acid_frames = self._load_acid_frames()
        self.acid_anim_speed = 4

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
        self.screen_shake = 22
        self.intro_shake_timer = 90
        self.flash_msg = ""
        self.flash_timer = 0
        self.warning_timer = 120

        # Intro reveal
        self.reveal_timer = 120

        self.death_particles = []
        self.boss_dying = False
        self.boss_death_timer = 0

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

    def _load_moon_eater_frames(self):
        frames = []

        for i in range(ME_FRAME_COUNT):
            path = os.path.join(ME_FRAME_DIR, f"ME{i}.png")

            if not os.path.exists(path):
                print(f"[WARNING] Missing Moon Eater frame: {path}")
                frames.append(self._make_missing_moon_eater_frame(i))
                continue

            img = pygame.image.load(path).convert_alpha()

            # Adjust this size depending on your sprite.
            # Since Moon Eater is a boss, it should be large.
            img = pygame.transform.scale(img, (210, 260))

            frames.append(img)

        return frames

    def _load_acid_frames(self):
        frames = []

        for i in range(ACID_FRAME_COUNT):
            path = os.path.join(ACID_FRAME_DIR, f"acid{i}.png")

            if not os.path.exists(path):
                print(f"[WARNING] Missing acid frame: {path}")
                frames.append(self._make_missing_acid_frame(i))
                continue

            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (46, 46))
            frames.append(img)

        return frames


    def _make_missing_acid_frame(self, i):
        """Fallback if acid frames are missing."""
        surf = pygame.Surface((46, 46), pygame.SRCALPHA)

        draw_text(surf, str(i), font_tiny, RED, 23, 37)

        return surf
    

    def _make_missing_moon_eater_frame(self, i):
        surf = pygame.Surface((210, 260), pygame.SRCALPHA)

        pygame.draw.ellipse(surf, (10, 0, 20), (35, 20, 140, 220))
        pygame.draw.ellipse(surf, (90, 0, 100), (35, 20, 140, 220), 3)

        draw_text(surf, f"ME{i}", font_tiny, RED, 105, 235)
        return surf

    def _make_missing_astro_frame(self, i):
        surf = pygame.Surface((PLAYER_W, PLAYER_H), pygame.SRCALPHA)

        pygame.draw.rect(surf, (210, 210, 210), (13, 20, 18, 24))
        pygame.draw.rect(surf, (20, 70, 95), (16, 10, 12, 7))
        pygame.draw.line(surf, (230, 230, 230), (30, 28), (42, 25), 3)
        pygame.draw.rect(surf, (255, 90, 30), (40, 23, 8, 4))

        draw_text(surf, str(i), font_tiny, RED, PLAYER_W // 2, PLAYER_H - 8)
        return surf

    def _load_astronaut_frames(self):
        """Load astronaut PNG frames."""
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

    def _load_astro3_frames(self):
        frames = []

        for i in range(ASTRO_FRAME_COUNT):
            path = os.path.join(ASTRO3_FRAME_DIR, f"ASTROF{i}.png")

            if not os.path.exists(path):
                print(f"[WARNING] Missing astronaut frame: {path}")
                frames.append(self._make_missing_astro_frame(i))
                continue

            img = pygame.image.load(path).convert_alpha()

            # Adjust size if needed
            img = pygame.transform.scale(img, (PLAYER_W, PLAYER_H))
            frames.append(img)

        return frames


    def _load_astro3_shoot_frames(self):
        """Load shooting astronaut frames: ASTROS0.png - ASTROS3.png"""
        frames = []

        for i in range(ASTRO_SHOOT_COUNT):
            path = os.path.join(ASTRO3_FRAME_DIR, f"ASTROS{i}.png")

            if not os.path.exists(path):
                print(f"[WARNING] Missing astronaut shooting frame: {path}")
                frames.append(self._make_missing_astro_frame(i))
                continue

            img = pygame.image.load(path).convert_alpha()

            # Same size as normal astronaut
            img = pygame.transform.scale(img, (PLAYER_W, PLAYER_H))
            frames.append(img)

        return frames


    def _load_bullet_frames(self):
        """Load bullet animation frames: BULLET1.png - BULLET9.png"""
        frames = []

        for i in range(1, BULLET_FRAME_COUNT + 1):
            path = os.path.join(ASTRO3_FRAME_DIR, f"BULLET{i}.png")

            if not os.path.exists(path):
                print(f"[WARNING] Missing bullet frame: {path}")
                frames.append(self._make_missing_bullet_frame(i))
                continue

            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (44, 22))
            frames.append(img)

        return frames


    def _make_missing_bullet_frame(self, i):
        """Fallback bullet if PNG missing."""
        surf = pygame.Surface((44, 22), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 220, 80), (5, 8, 28, 6))
        pygame.draw.rect(surf, (255, 90, 30), (30, 6, 10, 10))
        draw_text(surf, str(i), font_tiny, RED, 22, 12)
        return surf

    def _make_missing_astro_frame(self, i):
        """Fallback only if astronaut PNG files are missing."""
        surf = pygame.Surface((PLAYER_W, PLAYER_H), pygame.SRCALPHA)

        pygame.draw.rect(surf, (210, 210, 210), (13, 20, 18, 24))
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

        if self.shooting_timer > 0:
            self.shooting_timer -= 1

        if self.intro_shake_timer > 0:
            self.intro_shake_timer -= 1

            # Strong at first, then slowly settles
            self.screen_shake = max(0, int(22 * (self.intro_shake_timer / 90)))

        elif self.screen_shake > 0:
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

        if self.boss_hp <= 0 and not self.boss_dying:
            self.boss_hp = 0
            self.boss_dying = True
            self.boss_death_timer = 180
            self.screen_shake = 22
            self.flash_msg = "MOON EATER DESTROYED"
            self.flash_timer = 120
            self._spawn_boss_disintegration()

        if self.boss_dying:
            self.boss_death_timer -= 1

            for p in self.death_particles:
                p.update()

            if self.boss_death_timer <= 0:
                self.done = True

            return
        

    def _update_player(self):
        keys = pygame.key.get_pressed()

        self.vx = 0

        if keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
            self.facing = -1

        if keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
            self.facing = 1

        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.on_ground:
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

            bullet["anim_timer"] += 1
            if bullet["anim_timer"] >= 3:
                bullet["anim_timer"] = 0
                bullet["frame"] = (bullet["frame"] + 1) % len(self.bullet_frames)

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

            # animate projectile
            proj["anim_timer"] += 1
            if proj["anim_timer"] >= self.acid_anim_speed:
                proj["anim_timer"] = 0
                proj["frame"] = (proj["frame"] + 1) % len(self.acid_frames)

            if (
                proj["life"] <= 0
                or proj["x"] < -60
                or proj["x"] > SCREEN_W + 60
                or proj["y"] > PLAY_AREA_BOTTOM - 15
            ):
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
        self.shooting_timer = self.shooting_anim_speed * ASTRO_SHOOT_COUNT

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
            "frame": 0,
            "anim_timer": 0,
        })

    def _spawn_enemy_projectile(self):
        start_x = self.boss_x - 35
        start_y = self.boss_y + random.randint(-40, 55)

        target_y = min(self.py - 28, PLAY_AREA_BOTTOM - 35)

        dx = self.px - start_x
        dy = target_y - start_y
        dist = max(1, math.hypot(dx, dy))

        speed = 4.1 + self.boss_phase * 0.6

        self.enemy_projectiles.append({
            "x": start_x,
            "y": start_y,
            "vx": dx / dist * speed,
            "vy": dy / dist * speed,
            "life": 170,
            "frame": random.randint(0, len(self.acid_frames) - 1),
            "anim_timer": 0,
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

    def _spawn_boss_disintegration(self):
        self.death_particles = []

        # Spawn particles around boss body
        for _ in range(180):
            px = self.boss_x + random.randint(-80, 80)
            py = self.boss_y + random.randint(-120, 120)

            color = random.choice([
                (255, 80, 25),
                (180, 0, 45),
                (90, 0, 120),
                (255, 180, 60),
            ])

            self.death_particles.append(
                DisintegrationParticle(px, py, color=color, block_size=random.choice([4, 5, 6]))
            )



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
        if not self.boss_dying:
            self._draw_boss(surf)
            self._draw_weak_point(surf)
        else:
            for p in self.death_particles:
                p.draw(surf)
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
        return

    def _draw_boss(self, surf):
        bx = int(self.boss_x)
        by = int(self.boss_y)

        # Organic aura behind sprite
        aura_size = 280
        aura = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
        pulse = int(45 + 25 * math.sin(self.t * 0.08))

        pygame.draw.circle(
            aura,
            (90, 0, 100, pulse),
            (aura_size // 2, aura_size // 2),
            aura_size // 2 - 20
        )

        pygame.draw.circle(
            aura,
            (150, 20, 30, 30),
            (aura_size // 2, aura_size // 2),
            aura_size // 2 - 55
        )

        surf.blit(aura, (bx - aura_size // 2, by - aura_size // 2))

        # Select animation frame
        frame_index = (self.boss_anim // self.me_anim_speed) % len(self.me_frames)
        img = self.me_frames[frame_index]

        # Boss is on the right, player is on the left.
        # If your ME sprite already faces left, leave it.
        # If it faces right, uncomment the flip below.
        # img = pygame.transform.flip(img, True, False)

        rect = img.get_rect(center=(bx, by))
        surf.blit(img, rect)

        # Phase corruption outline / danger flicker
        if self.boss_phase >= 2 and self.t % 12 < 6:
            ghost = img.copy()
            ghost.fill((140, 0, 40, 80), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(ghost, rect.move(random.randint(-3, 3), random.randint(-2, 2)))

        # Extra rage flicker in phase 3
        if self.boss_phase >= 3 and self.t % 8 < 4:
            for _ in range(8):
                px = random.randint(rect.left, rect.right)
                py = random.randint(rect.top, rect.bottom)
                pygame.draw.rect(
                    surf,
                    random.choice([(180, 0, 40), (90, 0, 130), (255, 70, 30)]),
                    (px, py, random.randint(2, 5), random.randint(2, 5))
                )

        for i in range(0, 360, 45):
            angle = math.radians(i + self.t * 3)
            orbit_r = 42 + int(6 * math.sin(self.t * 0.08))

            ox = int(self.weak_point["x"] + math.cos(angle) * orbit_r)
            oy = int(self.weak_point["y"] + math.sin(angle) * orbit_r)

            pygame.draw.rect(
                surf,
                (255, 90, 30),
                (ox, oy, 4, 4)
            )

    def _draw_weak_point(self, surf):
        """
        Invisible weak point.
        Hit detection still works, but no ugly target circle is drawn.
        """
        return

    def _draw_player(self, surf):
        if self.immune_timer > 0 and self.immune_timer % 8 >= 4:
            return

        # Shooting animation has priority
        if self.shooting_timer > 0 and len(self.astro_shoot_frames) > 0:
            frame_index = ((self.shooting_anim_speed * ASTRO_SHOOT_COUNT - self.shooting_timer) // self.shooting_anim_speed)
            frame_index = clamp(frame_index, 0, len(self.astro_shoot_frames) - 1)
            img = self.astro_shoot_frames[int(frame_index)]
        else:
            frame_index = (self.player_frame // self.astro_anim_speed) % len(self.astro_frames)
            img = self.astro_frames[frame_index]

        # Assumes sprite faces right by default
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)

        rect = img.get_rect(midbottom=(int(self.px), int(self.py)))
        surf.blit(img, rect)

    def _draw_bullets(self, surf):
        if not self.bullet_frames:
            return

        for bullet in self.bullets:
            frame_index = bullet.get("frame", 0) % len(self.bullet_frames)
            img = self.bullet_frames[frame_index]

            if bullet["vx"] < 0:
                img = pygame.transform.flip(img, True, False)

            if bullet.get("power", False):
                img = pygame.transform.scale(img, (58, 30))

            rect = img.get_rect(center=(int(bullet["x"]), int(bullet["y"])))
            surf.blit(img, rect)
                

    def _draw_enemy_projectiles(self, surf):
        for proj in self.enemy_projectiles:
            if proj["y"] > PLAY_AREA_BOTTOM - 15:
                continue

            frame = self.acid_frames[proj["frame"]]

            angle = math.degrees(math.atan2(-proj["vy"], proj["vx"]))
            rotated = pygame.transform.rotate(frame, angle)

            rect = rotated.get_rect(center=(int(proj["x"]), int(proj["y"])))
            surf.blit(rotated, rect)

    def _draw_lighting(self, surf):
        if self.blackout_active:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))

            # Visibility around player
            pygame.draw.circle(
                overlay,
                (0, 0, 0, 45),
                (int(self.px), int(self.py - 30)),
                110
            )

            # Boss weak point glow
            pygame.draw.circle(
                overlay,
                (0, 0, 0, 70),
                (int(self.weak_point["x"]), int(self.weak_point["y"])),
                90
            )

            surf.blit(overlay, (0, 0))

        # CRT scanline effect
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 5):
            pygame.draw.line(scan, (255, 255, 255, 7), (0, y), (SCREEN_W, y))
        surf.blit(scan, (0, 0))

    def _draw_hud(self, surf):
        # ─────────────────────────────────────────────
        # TOP BOSS HUD
        # ─────────────────────────────────────────────
        top_h = 48

        BG = (3, 4, 8)
        PANEL = (7, 6, 10)
        RED = (230, 45, 35)
        RED_DIM = (105, 22, 18)
        ORANGE = (255, 130, 35)
        GREEN = (0, 235, 95)
        GREEN_DIM = (0, 110, 55)
        TEXT_DIM = (130, 65, 55)
        FAINT = (60, 35, 35)

        pygame.draw.rect(surf, BG, (0, 0, SCREEN_W, top_h))
        pygame.draw.line(surf, RED_DIM, (0, top_h - 1), (SCREEN_W, top_h - 1), 2)

        # Subtle scanlines
        for y in range(2, top_h, 5):
            pygame.draw.line(surf, (18, 5, 5), (0, y), (SCREEN_W, y), 1)

        # Boss HP bar
        boss_bar_w = 430
        boss_bar_h = 12
        boss_bar_x = SCREEN_W // 2 - boss_bar_w // 2
        boss_bar_y = 22

        draw_text(
            surf,
            "MOON EATER",
            font_tiny,
            ORANGE,
            SCREEN_W // 2,
            11
        )

        pygame.draw.rect(surf, (28, 5, 5), (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h))
        pygame.draw.rect(surf, RED_DIM, (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h), 1)

        hp_ratio = self.boss_hp / self.boss_max_hp
        hp_w = int(boss_bar_w * hp_ratio)

        if hp_w > 0:
            pygame.draw.rect(surf, RED, (boss_bar_x, boss_bar_y, hp_w, boss_bar_h))

        draw_text(
            surf,
            f"PHASE {self.boss_phase}",
            font_tiny,
            TEXT_DIM,
            SCREEN_W // 2,
            40
        )

        # ─────────────────────────────────────────────
        # BOTTOM SPACECRAFT CONSOLE HUD
        # ─────────────────────────────────────────────
        bottom_h = 82
        bottom_y = SCREEN_H - bottom_h

        pygame.draw.rect(surf, BG, (0, bottom_y, SCREEN_W, bottom_h))
        pygame.draw.line(surf, RED_DIM, (0, bottom_y), (SCREEN_W, bottom_y), 2)

        # Console scanline / metal plate texture
        for y in range(bottom_y + 3, SCREEN_H, 5):
            pygame.draw.line(surf, (16, 4, 4), (0, y), (SCREEN_W, y), 1)

        for x in range(0, SCREEN_W, 40):
            pygame.draw.line(surf, (10, 8, 12), (x, bottom_y), (x, SCREEN_H), 1)

        # Layout sections
        left_rect = pygame.Rect(16, bottom_y + 12, 245, 56)
        mid_rect = pygame.Rect(280, bottom_y + 12, 245, 56)
        right_rect = pygame.Rect(SCREEN_W - 255, bottom_y + 12, 240, 56)

        for rect in [left_rect, mid_rect, right_rect]:
            pygame.draw.rect(surf, PANEL, rect)
            pygame.draw.rect(surf, RED_DIM, rect, 1)

        # ─────────────────────────────────────────────
        # LEFT: CONTROLS + SECTOR LORE
        # ─────────────────────────────────────────────
        draw_text_left(
            surf,
            "SECTOR: 04-B // LAUNCH CHAMBER",
            font_tiny,
            TEXT_DIM,
            left_rect.x + 10,
            left_rect.y + 8
        )

        draw_text_left(
            surf,
            "A/D MOVE   W JUMP",
            font_tiny,
            (160, 100, 70),
            left_rect.x + 10,
            left_rect.y + 25
        )

        draw_text_left(
            surf,
            "J SHOOT   HOLD R BOOST",
            font_tiny,
            ORANGE,
            left_rect.x + 10,
            left_rect.y + 40
        )

        # Small warning light
        if self.t % 50 < 25:
            pygame.draw.rect(surf, RED, (left_rect.right - 18, left_rect.y + 10, 6, 6))
        else:
            pygame.draw.rect(surf, FAINT, (left_rect.right - 18, left_rect.y + 10, 6, 6))

        # ─────────────────────────────────────────────
        # MIDDLE: HEART RATE / BIO-SCANNER
        # ─────────────────────────────────────────────
       # ─────────────────────────────────────────────
# MIDDLE: SYSTEM MESSAGE DISPLAY
# ─────────────────────────────────────────────

        draw_text_left(
            surf,
            "SYSTEM MESSAGE",
            font_tiny,
            TEXT_DIM,
            mid_rect.x + 10,
            mid_rect.y + 8
        )

        # Choose what message appears in the HUD
        if self.flash_timer > 0 and self.flash_msg:
            message = self.flash_msg.upper()
            msg_col = ORANGE

            # Damage-related messages turn red
            if "DAMAGE" in message or "HIT" in message or "FAILURE" in message:
                msg_col = RED

        elif self.blackout_active:
            message = "POWER FAILURE"
            msg_col = RED

        elif self.boss_voice_timer > 0 and self.boss_voice:
            message = "HOSTILE SIGNAL DETECTED"
            msg_col = RED_DIM

        else:
            message = "NO STABLE SIGNAL"
            msg_col = TEXT_DIM

        # Flicker urgent messages
        if msg_col == RED and self.t % 20 < 8:
            msg_col = (120, 20, 18)

        draw_text(
            surf,
            message,
            font_small,
            msg_col,
            mid_rect.centerx,
            mid_rect.y + 30
        )

        # Small fake terminal line
        terminal_line = "LOG // COMBAT SYSTEM ACTIVE"

        draw_text(
            surf,
            terminal_line,
            font_tiny,
            FAINT,
            mid_rect.centerx,
            mid_rect.y + 48
        )

        # ─────────────────────────────────────────────
        # RIGHT: SUIT + BOOST CHARGE
        # ─────────────────────────────────────────────
        draw_text_left(
            surf,
            "SUIT INTEGRITY",
            font_tiny,
            GREEN_DIM,
            right_rect.x + 10,
            right_rect.y + 8
        )

        hp_percent = self.player_hp / self.player_max
        danger = hp_percent <= 0.35
        heart_col = RED if danger else GREEN

        # Suit HP bar
        suit_bar_x = right_rect.x + 10
        suit_bar_y = right_rect.y + 24
        suit_bar_w = 95
        suit_bar_h = 9

        pygame.draw.rect(surf, (5, 22, 8), (suit_bar_x, suit_bar_y, suit_bar_w, suit_bar_h))
        pygame.draw.rect(surf, GREEN_DIM, (suit_bar_x, suit_bar_y, suit_bar_w, suit_bar_h), 1)

        suit_fill = int(suit_bar_w * hp_percent)

        if suit_fill > 0:
            pygame.draw.rect(surf, heart_col, (suit_bar_x, suit_bar_y, suit_fill, suit_bar_h))

        draw_text_left(
            surf,
            f"{self.player_hp}/{self.player_max}",
            font_tiny,
            heart_col,
            suit_bar_x + suit_bar_w + 12,
            suit_bar_y - 2
        )

        # Boost charge bar
        boost_y = right_rect.y + 43
        charge_ratio = self.boost_charge / BOOST_CHARGE_TIME

        pygame.draw.rect(surf, (28, 8, 5), (suit_bar_x, boost_y, 135, 8))
        pygame.draw.rect(
            surf,
            ORANGE,
            (suit_bar_x, boost_y, int(135 * charge_ratio), 8)
        )
        pygame.draw.rect(surf, RED_DIM, (suit_bar_x, boost_y, 135, 8), 1)

        if self.boost_ready:
            boost_text = "BOOST READY"
            boost_col = ORANGE if self.t % 30 < 15 else RED
        elif self.boost_charging:
            boost_text = "BOOST CHARGING"
            boost_col = (180, 95, 45)
        else:
            boost_text = "BOOST"
            boost_col = TEXT_DIM

        draw_text_left(
            surf,
            boost_text,
            font_tiny,
            boost_col,
            suit_bar_x + 145,
            boost_y - 2
        )

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

        if self.intro_shake_timer > 0:
            alpha = min(255, self.intro_shake_timer * 4)

            draw_text(
                surf,
                "STRUCTURAL FAILURE DETECTED",
                font_med,
                (255, 55, 35),
                SCREEN_W // 2,
                120,
                alpha
    )