"""Level 3 – Full 2D arena boss fight against the Moon Eater.

Three phases of escalating attacks, power-ups, screen shake,
damage numbers, and a cinematic death sequence.
"""

import pygame
import math
import random
from settings import (BLACK, WHITE, DARK_GREY, MOON_GREY, CYAN, PURPLE,
                       DEEP_PURP, BLOOD_RED, ORANGE, GOLD, RED, BLUE_GLOW,
                       COSMIC_BLU, HP_GREEN, HP_RED, YELLOW, LIGHT_GREY,
                       LASER_RED, VORTEX_PUR, SHIELD_BLU, POWER_GRN)
from utils import (draw_text, draw_hp_bar, draw_stars, clamp, lerp,
                   font_tiny, font_small, font_med, font_large, font_title,
                   SCREEN_W, SCREEN_H)
from core.particles import spawn_particles, update_particles
from graphics.sprites import (draw_moon_eater, draw_ship, draw_bullet,
                               draw_homing_orb, draw_mini_eye,
                               draw_laser_telegraph, draw_asteroid,
                               draw_powerup, draw_gravity_well)

# ═════════════════════════════════════════════
#  CONSTANTS
# ═════════════════════════════════════════════
PLAYER_SPEED    = 4
PLAYER_MAX_HP   = 25
BOSS_MAX_HP     = 200
BOSS_RADIUS     = 55
BULLET_DMG      = 2
SHOOT_COOLDOWN  = 10
IMMUNITY_FRAMES = 50
MARGIN          = 20

# Power-up HP thresholds: (boss_hp_threshold, kind)
POWERUP_THRESHOLDS = [
    (150, 'health'), (120, 'health'), (80, 'damage'),
    (50, 'health'),  (30, 'shield'),
]


# ═════════════════════════════════════════════
#  LEVEL 3 CLASS
# ═════════════════════════════════════════════
class Level3:
    """Final boss arena – defeat the Moon Eater."""

    # ─────────────────────────────────────────
    #  INIT
    # ─────────────────────────────────────────
    def __init__(self):
        # --- Player state ---
        self.player_x     = SCREEN_W // 2
        self.player_y     = SCREEN_H - 90
        self.player_hp    = PLAYER_MAX_HP
        self.player_max   = PLAYER_MAX_HP
        self.player_frame = 0
        self.shoot_cd     = 0
        self.immune_timer = 0
        self.shield_hits  = 0
        self.damage_boost_timer = 0

        # --- Boss state ---
        self.boss_x     = SCREEN_W // 2
        self.boss_y     = 140
        self.boss_hp    = BOSS_MAX_HP
        self.boss_max   = BOSS_MAX_HP
        self.boss_frame = 0
        self.phase      = 1           # 1=Awakening, 2=Rage, 3=Desperation

        # --- Projectiles & entities ---
        self.bullets      = []        # player bullets [{x, y, vy}]
        self.boss_proj    = []        # boss bullets   [{x, y, vx, vy}]
        self.homing_orbs  = []        # [{x, y, vx, vy, hp}]
        self.mini_eyes    = []        # [{x, y, hp, shoot_timer, frame}]
        self.meteors      = []        # [{x, y, vy, size, seed}]
        self.powerups     = []        # [{x, y, kind, timer}]
        self.damage_nums  = []        # [{x, y, text, timer, color}]

        # --- Laser beam (Phase 2) ---
        self.laser = None             # {telegraph_timer, active_timer, y, sweep_x}

        # --- Gravity well (Phase 3) ---
        self.gravity_well = None      # {x, y, timer}

        # --- Timers & attack clocks ---
        self.t          = 0
        self.atk_timer  = 0
        self.atk2_timer = 0
        self.atk3_timer = 0
        self.teleport_timer = 0

        # --- Screen shake ---
        self.shake_timer     = 0
        self.shake_intensity = 0

        # --- Boss death sequence ---
        self.death_timer = 0
        self.boss_dead   = False

        # --- Flash message ---
        self.flash_msg   = ''
        self.flash_timer = 0

        # --- Level flow ---
        self.done = False
        self.lose = False

        # --- Phase-transition tracking ---
        self.phase_changed_2 = False
        self.phase_changed_3 = False
        self.dropped_thresholds = set()

        # --- Parallax star layers (generated once) ---
        self.star_layers = []
        for layer in range(3):
            stars = []
            for _ in range(60):
                stars.append({
                    'x': random.randint(0, SCREEN_W),
                    'y': random.randint(0, SCREEN_H),
                    'r': random.randint(1, 2 + layer),
                    'phase': random.random() * 6.28,
                })
            self.star_layers.append(stars)

        # --- Floating background asteroids ---
        self.bg_asteroids = []
        for _ in range(random.randint(5, 8)):
            self.bg_asteroids.append({
                'x': random.randint(0, SCREEN_W),
                'y': random.randint(0, SCREEN_H),
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(0.15, 0.4),
                'size': random.randint(6, 14),
                'seed': random.randint(0, 9999),
            })

        # --- Background image & scroll ---
        try:
            self.bg_img = pygame.transform.scale(
                pygame.image.load("assets/images/level3_bg.png").convert(),
                (SCREEN_W, SCREEN_H)
            )
        except Exception as e:
            print(f"[ERROR] Failed to load level3_bg.png: {e}. Falling back to default.")
            self.bg_img = None
        self.bg_scroll_y = 0.0

    # ─────────────────────────────────────────
    #  EVENT HANDLING
    # ─────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.done = True


    # ─── Player ──────────────────────────────
    def _update_player(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        # Diagonal normalisation
        if dx and dy:
            dx *= 0.707
            dy *= 0.707
        self.player_x = clamp(self.player_x + dx * PLAYER_SPEED, MARGIN, SCREEN_W - MARGIN)
        self.player_y = clamp(self.player_y + dy * PLAYER_SPEED, MARGIN + 55, SCREEN_H - MARGIN)

        # Auto-fire while held
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.shoot_cd <= 0:
            self.bullets.append({'x': self.player_x, 'y': self.player_y - 20, 'vy': -9})
            self.shoot_cd = SHOOT_COOLDOWN
            spawn_particles(int(self.player_x), int(self.player_y - 20), YELLOW, 3, 1.5, 12)

    # ─── Phase transitions ───────────────────
    def _update_phase_transitions(self):
        hp = self.boss_hp
        if hp <= 120 and self.phase == 1 and not self.phase_changed_2:
            self.phase = 2
            self.phase_changed_2 = True
            self.flash_msg   = 'MOON EATER ENRAGES!'
            self.flash_timer = 120
            self._start_shake(8, 30)
            spawn_particles(self.boss_x, self.boss_y, RED, 25, 5, 60, 5)
        if hp <= 60 and self.phase == 2 and not self.phase_changed_3:
            self.phase = 3
            self.phase_changed_3 = True
            self.flash_msg   = 'THE VOID OPENS!'
            self.flash_timer = 120
            self._start_shake(10, 40)
            spawn_particles(self.boss_x, self.boss_y, VORTEX_PUR, 30, 6, 70, 6)
            spawn_particles(self.boss_x, self.boss_y, WHITE, 15, 4, 50, 3)

    # ─── Boss movement ───────────────────────
    def _update_boss_movement(self):
        t = self.t
        if self.phase == 1:
            self.boss_x = SCREEN_W // 2 + int(200 * math.sin(t * 0.015))
            self.boss_y = 140 + int(40 * math.sin(t * 0.03))
        elif self.phase == 2:
            self.boss_x = SCREEN_W // 2 + int(220 * math.sin(t * 0.022))
            self.boss_y = 130 + int(60 * math.sin(t * 0.045)) + int(30 * math.cos(t * 0.018))
        else:  # Phase 3 — teleport-dash + orbit
            self.teleport_timer += 1
            if self.teleport_timer >= 120:
                self.teleport_timer = 0
                old_x, old_y = self.boss_x, self.boss_y
                self.boss_x = random.randint(100, 700)
                self.boss_y = random.randint(80, 200)
                spawn_particles(old_x, old_y, VORTEX_PUR, 15, 4, 40, 4)
                self._start_shake(4, 8)
            else:
                self.boss_x += int(math.cos(t * 0.04) * 3)
                self.boss_y += int(math.sin(t * 0.04) * 2)
            self.boss_x = clamp(self.boss_x, 60, SCREEN_W - 60)
            self.boss_y = clamp(self.boss_y, 60, 250)

    # ─── Boss attacks ────────────────────────
    def _update_boss_attacks(self):
        self.atk_timer  += 1
        self.atk2_timer += 1
        self.atk3_timer += 1
        t = self.t

        if self.phase == 1:
            # Attack 1: 3-bullet spread every 55 frames
            if self.atk_timer >= 55:
                self.atk_timer = 0
                for i in range(3):
                    angle = math.pi / 2 + (i - 1) * 0.35
                    self.boss_proj.append({
                        'x': self.boss_x, 'y': self.boss_y + 50,
                        'vx': math.cos(angle) * 4.5,
                        'vy': math.sin(angle) * 4.5,
                    })
            # Attack 2: homing orb every 180 frames
            if self.atk2_timer >= 180:
                self.atk2_timer = 0
                self.homing_orbs.append({
                    'x': self.boss_x, 'y': self.boss_y,
                    'vx': 0, 'vy': 0, 'hp': 3,
                })

        elif self.phase == 2:
            # Attack 1: 5-bullet spread every 35 frames
            if self.atk_timer >= 35:
                self.atk_timer = 0
                for i in range(5):
                    angle = math.pi / 2 + (i - 2) * 0.35
                    self.boss_proj.append({
                        'x': self.boss_x, 'y': self.boss_y + 50,
                        'vx': math.cos(angle) * 5,
                        'vy': math.sin(angle) * 5,
                    })
            # Attack 2: laser beam every 200 frames
            if self.atk2_timer >= 200 and self.laser is None:
                self.atk2_timer = 0
                self.laser = {
                    'telegraph_timer': 60,
                    'active_timer': 0,
                    'y': self.boss_y + 120,
                    'sweep_x': 0,
                }
            # Attack 3: mini-eyes every 300 frames
            if self.atk3_timer >= 300:
                self.atk3_timer = 0
                for _ in range(2):
                    self.mini_eyes.append({
                        'x': self.boss_x + random.randint(-20, 20),
                        'y': self.boss_y + random.randint(-10, 10),
                        'hp': 6, 'shoot_timer': 90,
                        'frame': 0,
                    })

        else:  # Phase 3
            # Attack 1: spiral bullet pattern every 25 frames
            if self.atk_timer >= 25:
                self.atk_timer = 0
                rot = t * 0.08
                for i in range(4):
                    angle = rot + i * math.pi / 2
                    self.boss_proj.append({
                        'x': self.boss_x, 'y': self.boss_y + 30,
                        'vx': math.cos(angle) * 4,
                        'vy': math.sin(angle) * 4,
                    })
            # Attack 2: gravity well every 250 frames
            if self.atk2_timer >= 250 and self.gravity_well is None:
                self.atk2_timer = 0
                self.gravity_well = {
                    'x': self.boss_x, 'y': self.boss_y, 'timer': 180,
                }
            # Attack 3: meteor every 60 frames
            if self.atk3_timer >= 60:
                self.atk3_timer = 0
                size = random.randint(18, 25)
                self.meteors.append({
                    'x': random.randint(40, SCREEN_W - 40), 'y': -30,
                    'vy': 3.5, 'size': size,
                    'seed': random.randint(0, 9999),
                })

    # ─── Player bullets ──────────────────────
    def _update_bullets(self):
        for b in self.bullets[:]:
            b['y'] += b['vy']
            if b['y'] < -10:
                self.bullets.remove(b)
                continue
            # Hit boss
            if math.hypot(b['x'] - self.boss_x, b['y'] - self.boss_y) < BOSS_RADIUS:
                dmg = BULLET_DMG * (2 if self.damage_boost_timer > 0 else 1)
                self.boss_hp -= dmg
                self.bullets.remove(b)
                self._start_shake(2, 3)
                spawn_particles(int(b['x']), int(b['y']), BLUE_GLOW, 4, 2, 18)
                self.damage_nums.append({
                    'x': b['x'] + random.randint(-10, 10),
                    'y': b['y'], 'text': str(dmg),
                    'timer': 40,
                    'color': GOLD if self.damage_boost_timer > 0 else WHITE,
                })
                self._check_powerup_thresholds()
                if self.boss_hp <= 0:
                    self.boss_hp = 0
                    self.boss_dead = True
                    self.death_timer = 180
                    self._start_shake(10, 60)
                continue
            # Hit homing orbs
            for orb in self.homing_orbs[:]:
                if math.hypot(b['x'] - orb['x'], b['y'] - orb['y']) < 10:
                    dmg = BULLET_DMG * (2 if self.damage_boost_timer > 0 else 1)
                    orb['hp'] -= dmg
                    if b in self.bullets:
                        self.bullets.remove(b)
                    spawn_particles(int(orb['x']), int(orb['y']), VORTEX_PUR, 3, 2, 15)
                    if orb['hp'] <= 0 and orb in self.homing_orbs:
                        self.homing_orbs.remove(orb)
                        spawn_particles(int(orb['x']), int(orb['y']), VORTEX_PUR, 8, 3, 25)
                    break
            # Hit mini-eyes
            for eye in self.mini_eyes[:]:
                if b not in self.bullets:
                    break
                if math.hypot(b['x'] - eye['x'], b['y'] - eye['y']) < 15:
                    dmg = BULLET_DMG * (2 if self.damage_boost_timer > 0 else 1)
                    eye['hp'] -= dmg
                    if b in self.bullets:
                        self.bullets.remove(b)
                    spawn_particles(int(eye['x']), int(eye['y']), PURPLE, 3, 2, 15)
                    if eye['hp'] <= 0 and eye in self.mini_eyes:
                        self.mini_eyes.remove(eye)
                        spawn_particles(int(eye['x']), int(eye['y']), PURPLE, 10, 3, 30)
                    break

    # ─── Boss projectiles ────────────────────
    def _update_boss_proj_collisions(self):
        """Check boss projectiles against player."""
        for b in self.boss_proj[:]:
            b['x'] += b['vx']
            b['y'] += b['vy']
            if not (-20 <= b['x'] <= SCREEN_W + 20 and -20 <= b['y'] <= SCREEN_H + 50):
                self.boss_proj.remove(b)
                continue
            if math.hypot(b['x'] - self.player_x, b['y'] - self.player_y) < 18:
                if self.immune_timer <= 0:
                    self._hit_player(3)
                    self.boss_proj.remove(b)

    # ─── Homing orbs ─────────────────────────
    def _update_homing_orbs(self):
        for orb in self.homing_orbs[:]:
            angle = math.atan2(self.player_y - orb['y'], self.player_x - orb['x'])
            orb['vx'] = math.cos(angle) * 2.0
            orb['vy'] = math.sin(angle) * 2.0
            orb['x'] += orb['vx']
            orb['y'] += orb['vy']
            # Contact with player
            if math.hypot(orb['x'] - self.player_x, orb['y'] - self.player_y) < 18:
                if self.immune_timer <= 0:
                    self._hit_player(3)
                if orb in self.homing_orbs:
                    self.homing_orbs.remove(orb)
            # Off-screen cleanup
            elif orb['y'] > SCREEN_H + 40:
                self.homing_orbs.remove(orb)

    # ─── Mini-eyes ───────────────────────────
    def _update_mini_eyes(self):
        for eye in self.mini_eyes[:]:
            eye['frame'] += 1
            # Drift toward player
            angle = math.atan2(self.player_y - eye['y'], self.player_x - eye['x'])
            eye['x'] += math.cos(angle) * 1.5
            eye['y'] += math.sin(angle) * 1.5
            # Shoot
            eye['shoot_timer'] -= 1
            if eye['shoot_timer'] <= 0:
                eye['shoot_timer'] = 90
                a2 = math.atan2(self.player_y - eye['y'], self.player_x - eye['x'])
                self.boss_proj.append({
                    'x': eye['x'], 'y': eye['y'],
                    'vx': math.cos(a2) * 3.5,
                    'vy': math.sin(a2) * 3.5,
                })
            # Contact damage
            if math.hypot(eye['x'] - self.player_x, eye['y'] - self.player_y) < 22:
                if self.immune_timer <= 0:
                    self._hit_player(3)

    # ─── Meteors ─────────────────────────────
    def _update_meteors(self):
        for m in self.meteors[:]:
            m['y'] += m['vy']
            if m['y'] > SCREEN_H + 40:
                self.meteors.remove(m)
                continue
            if math.hypot(m['x'] - self.player_x, m['y'] - self.player_y) < m['size'] + 12:
                if self.immune_timer <= 0:
                    self._hit_player(3)
                self.meteors.remove(m)
                spawn_particles(int(m['x']), int(m['y']), ORANGE, 8, 3, 25)

    # ─── Laser beam ──────────────────────────
    def _update_laser(self):
        if self.laser is None:
            return
        ls = self.laser
        if ls['telegraph_timer'] > 0:
            ls['telegraph_timer'] -= 1
        else:
            if ls['active_timer'] == 0:
                ls['sweep_x'] = 0
            ls['active_timer'] += 1
            ls['sweep_x'] = int(SCREEN_W * (ls['active_timer'] / 40))
            # Hit player
            if (abs(self.player_y - ls['y']) < 15 and
                    self.player_x < ls['sweep_x'] and self.immune_timer <= 0):
                self._hit_player(5)
                self.player_y = min(SCREEN_H - MARGIN, self.player_y + 30)
            if ls['active_timer'] >= 40:
                self.laser = None

    # ─── Gravity well ────────────────────────
    def _update_gravity_well(self):
        if self.gravity_well is None:
            return
        gw = self.gravity_well
        gw['timer'] -= 1
        # Pull player
        angle = math.atan2(gw['y'] - self.player_y, gw['x'] - self.player_x)
        self.player_x += math.cos(angle) * 1.5
        self.player_y += math.sin(angle) * 1.5
        self.player_x = clamp(self.player_x, MARGIN, SCREEN_W - MARGIN)
        self.player_y = clamp(self.player_y, MARGIN + 55, SCREEN_H - MARGIN)
        if gw['timer'] <= 0:
            self.gravity_well = None

    # ─── Power-ups ───────────────────────────
    def _update_powerups(self):
        for pu in self.powerups[:]:
            pu['timer'] -= 1
            if pu['timer'] <= 0:
                self.powerups.remove(pu)
                continue
            if math.hypot(pu['x'] - self.player_x, pu['y'] - self.player_y) < 20:
                self._collect_powerup(pu)
                self.powerups.remove(pu)

    def _collect_powerup(self, pu):
        kind = pu['kind']
        if kind == 'health':
            self.player_hp = min(self.player_max, self.player_hp + 5)
            self.flash_msg = '+5 HP!'
        elif kind == 'damage':
            self.damage_boost_timer = 300
            self.flash_msg = 'DAMAGE BOOST!'
        elif kind == 'shield':
            self.shield_hits = 2
            self.flash_msg = 'SHIELD ACTIVE!'
        self.flash_timer = 60
        spawn_particles(int(pu['x']), int(pu['y']), POWER_GRN, 12, 3, 30)

    def _check_powerup_thresholds(self):
        for threshold, kind in POWERUP_THRESHOLDS:
            if self.boss_hp <= threshold and threshold not in self.dropped_thresholds:
                self.dropped_thresholds.add(threshold)
                self.powerups.append({
                    'x': self.boss_x + random.randint(-40, 40),
                    'y': self.boss_y + random.randint(30, 60),
                    'kind': kind, 'timer': 600,
                })

    # ─── Damage numbers ──────────────────────
    def _update_damage_numbers(self):
        for dn in self.damage_nums[:]:
            dn['y'] -= 1
            dn['timer'] -= 1
            if dn['timer'] <= 0:
                self.damage_nums.remove(dn)

    # ─── Background asteroids ────────────────
    def _update_bg_asteroids(self):
        for a in self.bg_asteroids:
            a['x'] += a['vx']
            a['y'] += a['vy']
            if a['y'] > SCREEN_H + 20:
                a['y'] = -20
                a['x'] = random.randint(0, SCREEN_W)
            if a['x'] < -20: a['x'] = SCREEN_W + 20
            if a['x'] > SCREEN_W + 20: a['x'] = -20

    # ─── Death sequence ──────────────────────
    def _update_death_sequence(self):
        self.death_timer -= 1
        # Continuous explosions
        if self.death_timer % 8 == 0:
            ox = self.boss_x + random.randint(-50, 50)
            oy = self.boss_y + random.randint(-50, 50)
            spawn_particles(ox, oy, random.choice([RED, ORANGE, WHITE, VORTEX_PUR]),
                            10, 4, 35, 4)
            self._start_shake(6, 5)
        if self.death_timer <= 0:
            self.done = True

    # ─── Helpers ─────────────────────────────
    def _hit_player(self, dmg):
        """Apply damage to player, respecting shield."""
        if self.shield_hits > 0:
            self.shield_hits -= 1
            spawn_particles(int(self.player_x), int(self.player_y), SHIELD_BLU, 8, 3, 20)
            self.immune_timer = IMMUNITY_FRAMES // 2
            return
        self.player_hp -= dmg
        self.immune_timer = IMMUNITY_FRAMES
        self._start_shake(5, 10)
        spawn_particles(int(self.player_x), int(self.player_y), BLOOD_RED, 8, 2, 25)
        if self.player_hp <= 0:
            self.player_hp = 0
            self.lose = True

    def _start_shake(self, intensity, duration):
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_timer = max(self.shake_timer, duration)

    # ─────────────────────────────────────────
    #  UPDATE  (main tick)
    # ─────────────────────────────────────────
    def update(self):
        self.t += 1
        self.player_frame += 1
        self.boss_frame   += 1

        if self.flash_timer > 0:        self.flash_timer -= 1
        if self.immune_timer > 0:       self.immune_timer -= 1
        if self.shoot_cd > 0:           self.shoot_cd -= 1
        if self.shake_timer > 0:        self.shake_timer -= 1
        if self.damage_boost_timer > 0: self.damage_boost_timer -= 1

        if self.boss_dead:
            self._update_death_sequence()
            return

        self._update_player()
        self._update_phase_transitions()
        self._update_boss_movement()
        self._update_boss_attacks()
        self._update_bullets()
        self._update_boss_proj_collisions()
        self._update_homing_orbs()
        self._update_mini_eyes()
        self._update_meteors()
        self._update_laser()
        self._update_gravity_well()
        self._update_powerups()
        self._update_damage_numbers()
        self._update_bg_asteroids()

    # ═════════════════════════════════════════
    #  DRAW
    # ═════════════════════════════════════════
    def draw(self, surf):
        # Compute shake offset
        sx = sy = 0
        if self.shake_timer > 0:
            sx = random.randint(-self.shake_intensity, self.shake_intensity)
            sy = random.randint(-self.shake_intensity, self.shake_intensity)

        # ── 1. Background ────────────────────
        if self.bg_img:
            # Draw static spaceship corridor room with screen shake offsets
            surf.blit(self.bg_img, (sx, sy))
        else:
            surf.fill(COSMIC_BLU)

        # Intruder warning light (flickering red alert overlay in background corridor)
        base_alpha = 15 + 15 * math.sin(self.t * 0.07)
        # Occasional rapid flicker/drop simulating electrical warning system instability
        if (self.t % 110 < 6) or (self.t % 170 < 10):
            base_alpha = max(0, base_alpha - 12)
        intruder_tint = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        intruder_tint.fill((255, 20, 20, int(base_alpha)))
        surf.blit(intruder_tint, (0, 0))

        # Phase color tint overlays for atmospheric effect (emergency warning flashes)
        if self.phase == 2:
            tint = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            tint.fill((255, 40, 60, 20))  # Subtle enrage red overlay
            surf.blit(tint, (0, 0))
        elif self.phase == 3:
            tint = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            tint.fill((140, 30, 200, 30))  # Purple reactor overload overlay
            surf.blit(tint, (0, 0))

        # Floating glowing electrical sparks/embers rising from damaged ship corridor
        for li, layer in enumerate(self.star_layers):
            speed = (li + 1) * 0.25
            for s in layer:
                # Scroll upward to look like rising embers
                sy2 = (s['y'] - self.t * speed) % SCREEN_H
                bright = int(160 + 95 * math.sin(self.t * 0.05 + s['phase']))
                # Glowing orange/gold color
                col = (255, clamp(int(100 + bright * 0.5), 0, 255), 40)
                pygame.draw.circle(surf, col,
                                   (int(s['x']) + sx, int(sy2) + sy), max(1, s['r'] - 1))

        # Floating background asteroids
        for a in self.bg_asteroids:
            draw_asteroid(surf, int(a['x']) + sx, int(a['y']) + sy, a['size'], a['seed'])

        # ── 2. Gravity well (behind entities) ─
        if self.gravity_well:
            gw = self.gravity_well
            draw_gravity_well(surf, int(gw['x']) + sx, int(gw['y']) + sy, 60, self.t)

        # ── 3. Boss ──────────────────────────
        if not self.boss_dead or self.death_timer % 4 < 3:
            draw_moon_eater(surf, self.boss_x + sx, self.boss_y + sy,
                            self.boss_frame, max(0, self.boss_hp) / self.boss_max)

        # ── 4. Boss projectiles ──────────────
        for b in self.boss_proj:
            draw_bullet(surf, b['x'] + sx, b['y'] + sy, BLUE_GLOW)

        # ── 5. Homing orbs ───────────────────
        for orb in self.homing_orbs:
            draw_homing_orb(surf, orb['x'] + sx, orb['y'] + sy, self.t)

        # ── 6. Mini-eyes ─────────────────────
        for eye in self.mini_eyes:
            draw_mini_eye(surf, eye['x'] + sx, eye['y'] + sy, eye['frame'])

        # ── 7. Meteors ───────────────────────
        for m in self.meteors:
            draw_asteroid(surf, int(m['x']) + sx, int(m['y']) + sy, m['size'], m['seed'])

        # ── 8. Laser beam ────────────────────
        if self.laser:
            ls = self.laser
            if ls['telegraph_timer'] > 0:
                progress = 1.0 - ls['telegraph_timer'] / 60.0
                draw_laser_telegraph(surf, 0 + sx, ls['y'] + sy, SCREEN_W, progress)
            else:
                # Active beam — thick red sweep
                beam_y = ls['y'] + sy
                sweep = ls['sweep_x']
                # Glow
                gs = pygame.Surface((sweep, 20), pygame.SRCALPHA)
                gs.fill((255, 40, 60, 100))
                surf.blit(gs, (sx, beam_y - 10))
                # Core
                pygame.draw.line(surf, LASER_RED, (sx, beam_y), (sweep + sx, beam_y), 6)
                pygame.draw.line(surf, WHITE, (sx, beam_y), (sweep + sx, beam_y), 2)

        # ── 9. Power-ups ─────────────────────
        for pu in self.powerups:
            draw_powerup(surf, int(pu['x']) + sx, int(pu['y']) + sy, pu['kind'], self.t)

        # ── 10. Player bullets ───────────────
        for b in self.bullets:
            draw_bullet(surf, b['x'] + sx, b['y'] + sy, YELLOW)

        # ── 11. Player ship ──────────────────
        if self.immune_timer <= 0 or self.immune_timer % 6 < 3:
            draw_ship(surf, int(self.player_x) + sx, int(self.player_y) + sy,
                      self.player_frame, False)
            # Shield indicator ring
            if self.shield_hits > 0:
                shield_r = 22
                ss = pygame.Surface((shield_r * 2, shield_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(ss, (*SHIELD_BLU, 80), (shield_r, shield_r), shield_r, 2)
                surf.blit(ss, (int(self.player_x) + sx - shield_r,
                               int(self.player_y) + sy - shield_r))

        # ── 12. Particles ────────────────────
        update_particles(surf)

        # ── 13. Damage numbers ───────────────
        for dn in self.damage_nums:
            alpha = clamp(int(255 * dn['timer'] / 40), 0, 255)
            draw_text(surf, dn['text'], font_small, dn['color'],
                      int(dn['x']) + sx, int(dn['y']) + sy, alpha)

        # ── 14. Death flash ──────────────────
        if self.boss_dead and self.death_timer > 0:
            flash_alpha = int(120 * abs(math.sin(self.death_timer * 0.15)))
            fs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fs.fill((255, 255, 255, flash_alpha))
            surf.blit(fs, (0, 0))

        # ══════════════════════════════════════
        #  HUD  (drawn on top, NOT affected by shake)
        # ══════════════════════════════════════
        self._draw_hud(surf)

    # ─────────────────────────────────────────
    #  HUD
    # ─────────────────────────────────────────
    def _draw_hud(self, surf):
        # Dark top bar
        hud_bar = pygame.Surface((SCREEN_W, 55), pygame.SRCALPHA)
        hud_bar.fill((10, 10, 20, 220))
        surf.blit(hud_bar, (0, 0))

        # Level title
        draw_text(surf, 'LEVEL 3 \u2014 DEFEAT THE MOON EATER!', font_small,
                  MOON_GREY, SCREEN_W // 2, 14)

        # HP bars
        draw_hp_bar(surf, 20, 22, 160, 20, self.player_hp, self.player_max, 'SHIP')
        draw_hp_bar(surf, SCREEN_W - 180, 22, 160, 20,
                    max(0, self.boss_hp), self.boss_max, 'BOSS')

        # Phase indicator
        phase_cols  = {1: CYAN, 2: RED, 3: VORTEX_PUR}
        phase_names = {1: 'PHASE 1 — AWAKENING', 2: 'PHASE 2 — RAGE',
                       3: 'PHASE 3 — DESPERATION'}
        draw_text(surf, phase_names[self.phase], font_tiny,
                  phase_cols[self.phase], SCREEN_W // 2, 42)

        # Shield indicator
        if self.shield_hits > 0:
            draw_text(surf, f'SHIELD x{self.shield_hits}', font_tiny,
                      SHIELD_BLU, 100, 48)

        # Damage boost indicator
        if self.damage_boost_timer > 0:
            secs_left = self.damage_boost_timer // 60
            draw_text(surf, f'DMG BOOST {secs_left}s', font_tiny,
                      GOLD, SCREEN_W - 100, 48)

        # Controls hint
        draw_text(surf, '\u2190 \u2192 \u2191 \u2193 MOVE  |  Z / SPACE TO SHOOT',
                  font_tiny, (100, 100, 130), SCREEN_W // 2, SCREEN_H - 12)

        # Skip button
        pygame.draw.rect(surf, (60, 20, 20), (SCREEN_W - 110, 4, 100, 18), border_radius=3)
        pygame.draw.rect(surf, (180, 60, 60), (SCREEN_W - 110, 4, 100, 18), 1, border_radius=3)
        draw_text(surf, '[F1] SKIP', font_tiny, (220, 120, 120), SCREEN_W - 60, 13)

        # Flash message
        if self.flash_timer > 0:
            alpha = min(255, self.flash_timer * 4)
            draw_text(surf, self.flash_msg, font_med, WHITE,
                      SCREEN_W // 2, SCREEN_H // 2 - 40, alpha)
