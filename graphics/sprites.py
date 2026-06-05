"""Code-drawn pixel sprites and background drawing helpers."""

import pygame
import math
import random
from settings import *
from utils import *
from core.particles import spawn_particles

# ─────────────────────────────────────────────
#  PIXEL-ART SPRITE DRAWERS
# ─────────────────────────────────────────────
def draw_astronaut(surf, x, y, frame=0, facing=1):
    """Draw a tiny pixel astronaut."""
    # Helmet
    pygame.draw.ellipse(surf, LIGHT_GREY, (x - 8, y - 20, 16, 16))
    pygame.draw.ellipse(surf, CYAN,       (x - 5, y - 17, 10, 10))
    pygame.draw.ellipse(surf, LIGHT_GREY, (x - 8, y - 20, 16, 16), 2)
    # Body
    pygame.draw.rect(surf, WHITE, (x - 7, y - 4, 14, 12))
    # Legs
    leg_off = 2 * math.sin(frame * 0.3) if facing != 0 else 0
    pygame.draw.rect(surf, LIGHT_GREY, (x - 6, y + 8,  5, 8))
    pygame.draw.rect(surf, LIGHT_GREY, (x + 1,  y + 8 + int(leg_off), 5, 8))
    # Boots
    pygame.draw.rect(surf, MOON_DARK, (x - 7, y + 14, 6, 4))
    pygame.draw.rect(surf, MOON_DARK, (x + 1,  y + 14 + int(leg_off), 6, 4))
    # Arms
    arm_off = 2 * math.sin(frame * 0.3 + math.pi)
    pygame.draw.rect(surf, WHITE, (x - 12, y - 3 + int(arm_off), 6, 4))
    pygame.draw.rect(surf, WHITE, (x + 6,  y - 3 - int(arm_off), 6, 4))
    # Backpack
    pygame.draw.rect(surf, MOON_GREY, (x + 6, y - 4, 5, 10))

def draw_watcher(surf, x, y, frame=0, hp_ratio=1.0):
    """Level 1 boss: floating eyeball with wings."""
    t = frame * 0.05
    bob = int(4 * math.sin(t))
    # Glow aura
    for r in range(22, 10, -4):
        alpha = int(60 * (r - 10) / 12 * hp_ratio)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*PURPLE, alpha), (r, r), r)
        surf.blit(s, (x - r, y - r + bob))
    # Eyeball body
    pygame.draw.circle(surf, WHITE, (x, y + bob), 14)
    # Iris
    iris_x = x + int(3 * math.cos(t * 0.5))
    iris_y = y + bob + int(3 * math.sin(t * 0.7))
    pygame.draw.circle(surf, PURPLE, (iris_x, iris_y), 8)
    pygame.draw.circle(surf, BLACK,  (iris_x, iris_y), 4)
    pygame.draw.circle(surf, WHITE,  (iris_x - 2, iris_y - 2), 2)
    # Veins
    for i in range(4):
        angle = i * math.pi / 2 + t * 0.2
        ex = int(x + 10 * math.cos(angle))
        ey = int(y + bob + 10 * math.sin(angle))
        pygame.draw.line(surf, BLOOD_RED, (x, y + bob), (ex, ey), 1)
    # Wings
    wing_flap = int(5 * math.sin(t * 3))
    # Left wing
    pts_l = [(x - 14, y + bob), (x - 30, y + bob - 12 + wing_flap),
             (x - 28, y + bob + 6)]
    pygame.draw.polygon(surf, DEEP_PURP, pts_l)
    pygame.draw.polygon(surf, PURPLE, pts_l, 1)
    # Right wing
    pts_r = [(x + 14, y + bob), (x + 30, y + bob - 12 + wing_flap),
             (x + 28, y + bob + 6)]
    pygame.draw.polygon(surf, DEEP_PURP, pts_r)
    pygame.draw.polygon(surf, PURPLE, pts_r, 1)
    # Tentacles
    for i in range(6):
        base_angle = math.pi / 2 + (i - 2.5) * 0.3
        tx1 = x + int(10 * math.cos(base_angle))
        ty1 = y + bob + int(10 * math.sin(base_angle))
        tx2 = tx1 + int(15 * math.cos(base_angle + math.sin(t + i)))
        ty2 = ty1 + int(15 * math.sin(base_angle + math.sin(t + i)))
        pygame.draw.line(surf, DEEP_PURP, (tx1, ty1), (tx2, ty2), 2)

def draw_failed_experiment(surf, x, y, frame=0, hp_ratio=1.0):
    """Level 2 boss: hulking biomechanical abomination — layered pixel art."""
    t = frame * 0.06

    # ── 1. Outer toxic aura glow ──────────────────────────────────────────
    for r in range(38, 14, -6):
        alpha = int(35 * (r - 14) / 24)
        gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (40, 180, 40, alpha), (r, r), r)
        surf.blit(gs, (x - r, y - 14 - r))

    # ── 2. Legs (drawn first so body overlaps them) ───────────────────────
    leg_cycle = math.sin(t * 2.2)
    l_raise = int(6 * leg_cycle)
    r_raise = int(6 * -leg_cycle)
    # Upper leg segments
    pygame.draw.polygon(surf, (30, 100, 30), [
        (x - 18, y + 12), (x - 8,  y + 12),
        (x - 10, y + 28 + l_raise), (x - 22, y + 28 + l_raise)])
    pygame.draw.polygon(surf, (30, 100, 30), [
        (x + 8,  y + 12), (x + 18, y + 12),
        (x + 22, y + 28 + r_raise), (x + 10, y + 28 + r_raise)])
    # Knee bolts
    pygame.draw.circle(surf, MOON_GREY, (x - 16, y + 28 + l_raise), 4)
    pygame.draw.circle(surf, MOON_GREY, (x + 16, y + 28 + r_raise), 4)
    pygame.draw.circle(surf, WHITE,     (x - 16, y + 28 + l_raise), 4, 1)
    pygame.draw.circle(surf, WHITE,     (x + 16, y + 28 + r_raise), 4, 1)
    # Lower leg / shin
    pygame.draw.polygon(surf, (25, 80, 25), [
        (x - 22, y + 28 + l_raise), (x - 12, y + 28 + l_raise),
        (x - 10, y + 44),           (x - 20, y + 44)])
    pygame.draw.polygon(surf, (25, 80, 25), [
        (x + 12, y + 28 + r_raise), (x + 22, y + 28 + r_raise),
        (x + 20, y + 44),           (x + 10, y + 44)])
    # Metal boots with toe claws
    for bx, by, flip in [(x - 18, y + 44, -1), (x + 12, y + 44, 1)]:
        pygame.draw.rect(surf, MOON_DARK, (bx - 4, by, 16, 7))
        pygame.draw.rect(surf, MOON_GREY, (bx - 4, by, 16, 7), 1)
        for ci in range(3):
            pygame.draw.line(surf, MOON_GREY,
                             (bx + ci * 4, by + 7),
                             (bx + ci * 4 + flip * 3, by + 12), 2)

    # ── 3. Torso ──────────────────────────────────────────────────────────
    # Main body shape (wider at chest, tapers to waist)
    torso_pts = [
        (x - 24, y - 22), (x + 24, y - 22),
        (x + 20, y + 14), (x - 20, y + 14)]
    pygame.draw.polygon(surf, (45, 130, 45), torso_pts)
    # Chest highlight stripe
    pygame.draw.polygon(surf, (60, 160, 60), [
        (x - 10, y - 22), (x + 10, y - 22),
        (x + 8,  y - 6),  (x - 8,  y - 6)])
    # Body outline
    pygame.draw.polygon(surf, (20, 80, 20), torso_pts, 2)

    # Metal plate grafted on left pec
    pygame.draw.rect(surf, (80, 85, 90), (x - 22, y - 18, 14, 16))
    pygame.draw.rect(surf, MOON_GREY,    (x - 22, y - 18, 14, 16), 1)
    # Rivet row on plate
    for ri in range(3):
        pygame.draw.circle(surf, WHITE, (x - 18 + ri * 5, y - 20), 1)

    # Scar lines cut across torso
    pygame.draw.line(surf, BLOOD_RED, (x - 4,  y - 20), (x + 14, y - 4),  2)
    pygame.draw.line(surf, BLOOD_RED, (x - 16, y - 8),  (x - 6,  y + 8),  2)
    pygame.draw.line(surf, (140, 10, 10), (x - 4, y - 20), (x + 14, y - 4), 1)

    # Pulsing bio-tube along right side (dripping fluid)
    for seg in range(5):
        sy2 = y - 16 + seg * 6
        tube_alpha = int(120 + 60 * math.sin(t * 3 + seg * 0.8))
        ts = pygame.Surface((8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(ts, (0, 200, 80, tube_alpha), (0, 0, 8, 6))
        surf.blit(ts, (x + 18, sy2))
    pygame.draw.line(surf, (0, 160, 60), (x + 22, y - 16), (x + 22, y + 14), 2)

    # ── 4. Left arm (organic — swings forward/back) ───────────────────────
    larm_angle = t * 1.8
    lshoulder  = (x - 24, y - 16)
    lelbow     = (x - 38 + int(5 * math.cos(larm_angle)),
                  y - 2  + int(6 * math.sin(larm_angle)))
    lhand      = (x - 46 + int(4 * math.cos(larm_angle + 0.5)),
                  y + 14 + int(8 * math.sin(larm_angle + 0.5)))
    pygame.draw.line(surf, (35, 110, 35), lshoulder, lelbow, 9)
    pygame.draw.line(surf, (35, 110, 35), lelbow,    lhand,  7)
    pygame.draw.circle(surf, (55, 140, 55), lelbow, 5)       # elbow joint
    # Fist / hand with claws
    pygame.draw.circle(surf, (30, 100, 30), lhand, 7)
    pygame.draw.circle(surf, (20,  80, 20), lhand, 7, 1)
    for ci in range(3):
        cang = math.pi * 0.8 + ci * 0.35 + math.sin(larm_angle) * 0.3
        cx2  = lhand[0] + int(9 * math.cos(cang))
        cy2  = lhand[1] + int(9 * math.sin(cang))
        pygame.draw.line(surf, MOON_GREY, lhand, (cx2, cy2), 2)

    # ── 5. Right arm (mechanical claw) ───────────────────────────────────
    rarm_angle = t * 1.8 + math.pi        # opposite phase
    rshoulder  = (x + 24, y - 16)
    relbow     = (x + 38 + int(5 * math.cos(rarm_angle)),
                  y - 2  + int(6 * math.sin(rarm_angle)))
    # Upper arm
    pygame.draw.line(surf, MOON_GREY, rshoulder, relbow, 9)
    pygame.draw.circle(surf, (120, 120, 130), relbow, 5)
    # Forearm (metal)
    rclaw_base = (relbow[0] + int(8 * math.cos(rarm_angle + 0.4)),
                  relbow[1] + int(14 * math.sin(rarm_angle + 0.4)))
    pygame.draw.line(surf, (100, 105, 115), relbow, rclaw_base, 7)
    # Hydraulic piston detail on forearm
    piston_mid = ((relbow[0] + rclaw_base[0]) // 2,
                  (relbow[1] + rclaw_base[1]) // 2)
    pygame.draw.circle(surf, (150, 155, 165), piston_mid, 3)
    # Claw fingers
    claw_open = abs(math.sin(t * 1.5)) * 0.5
    for ci in range(3):
        base_ang = -0.4 + ci * 0.4
        tip_ang  = base_ang + claw_open * (1 if ci != 1 else -1)
        c1x = rclaw_base[0] + int(10 * math.cos(base_ang))
        c1y = rclaw_base[1] + int(10 * math.sin(base_ang))
        c2x = rclaw_base[0] + int(18 * math.cos(tip_ang))
        c2y = rclaw_base[1] + int(18 * math.sin(tip_ang))
        pygame.draw.line(surf, (160, 165, 175), rclaw_base, (c1x, c1y), 3)
        pygame.draw.line(surf, (200, 200, 210), (c1x, c1y),  (c2x, c2y), 2)

    # ── 6. Neck ───────────────────────────────────────────────────────────
    pygame.draw.rect(surf, (40, 118, 40), (x - 10, y - 34, 20, 14))
    # Neck bolts
    pygame.draw.circle(surf, MOON_GREY, (x - 10, y - 28), 3)
    pygame.draw.circle(surf, MOON_GREY, (x + 10, y - 28), 3)

    # ── 7. Head ───────────────────────────────────────────────────────────
    # Skull shape
    pygame.draw.ellipse(surf, (50, 140, 50), (x - 18, y - 62, 36, 30))
    # Jaw (separate, animates open)
    jaw_open = int(5 * abs(math.sin(t * 1.6)))
    pygame.draw.rect(surf, (40, 115, 40), (x - 14, y - 36 + jaw_open, 28, 10))

    # Head outline
    pygame.draw.ellipse(surf, (20, 90, 20), (x - 18, y - 62, 36, 30), 2)

    # Forehead metal plate
    pygame.draw.rect(surf, (75, 80, 88), (x - 10, y - 62, 20, 8))
    pygame.draw.rect(surf, MOON_GREY,    (x - 10, y - 62, 20, 8), 1)

    # Back-spines (drawn as overlapping triangles behind head)
    spine_cols = [(60, 80, 60), (50, 70, 50), (40, 60, 40)]
    for i in range(4):
        sx2 = x - 14 + i * 9
        sh  = 16 + i * 3
        pygame.draw.polygon(surf, spine_cols[i % 3], [
            (sx2,      y - 58),
            (sx2 - 4,  y - 58 - sh),
            (sx2 + 4,  y - 58)])
        pygame.draw.polygon(surf, MOON_DARK, [
            (sx2,      y - 58),
            (sx2 - 4,  y - 58 - sh),
            (sx2 + 4,  y - 58)], 1)

    # ── 8. Eyes (the key to life — same layered technique as The Watcher) ─
    # Eye whites with slight off-white tint
    eye_bob  = int(2 * math.sin(t * 0.9))
    for ex2, ey2 in [(x - 7, y - 52 + eye_bob), (x + 7, y - 52 + eye_bob)]:
        # sclera (white of eye)
        pygame.draw.circle(surf, (230, 220, 210), (ex2, ey2), 6)
        # iris — tracks a slow figure-8 path
        iris_dx = int(2 * math.cos(t * 0.55))
        iris_dy = int(2 * math.sin(t * 0.9))
        iris_x  = ex2 + iris_dx
        iris_y  = ey2 + iris_dy
        # layered iris: outer ring, mid ring, pupil
        pygame.draw.circle(surf, (180, 30, 30), (iris_x, iris_y), 4)
        pygame.draw.circle(surf, (220, 60, 60), (iris_x, iris_y), 2)
        pygame.draw.circle(surf, BLACK,         (iris_x, iris_y), 1)
        # corner reflection dot
        pygame.draw.circle(surf, WHITE, (iris_x - 1, iris_y - 2), 1)
        # eye outline
        pygame.draw.circle(surf, (20, 80, 20),  (ex2, ey2), 6, 1)
        # pulsing red glow behind each eye
        glow_r = int(4 + 3 * abs(math.sin(t * 2.5)))
        gs2 = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs2, (220, 30, 30, 80), (glow_r, glow_r), glow_r)
        surf.blit(gs2, (ex2 - glow_r, ey2 - glow_r))

    # ── 9. Teeth ──────────────────────────────────────────────────────────
    for i in range(6):
        tx2 = x - 12 + i * 4
        # upper teeth
        pygame.draw.polygon(surf, (230, 230, 220), [
            (tx2, y - 36), (tx2 + 2, y - 36), (tx2 + 1, y - 30)])
        # lower teeth (move with jaw)
        pygame.draw.polygon(surf, (210, 210, 200), [
            (tx2, y - 36 + jaw_open + 8), (tx2 + 2, y - 36 + jaw_open + 8),
            (tx2 + 1, y - 36 + jaw_open + 14)])
    # Drool string when mouth open
    if jaw_open > 2:
        drool_x = x + random.randint(-4, 4)
        drool_alpha = int(jaw_open * 40)
        ds = pygame.Surface((4, jaw_open * 3), pygame.SRCALPHA)
        ds.fill((180, 220, 100, drool_alpha))
        surf.blit(ds, (drool_x, y - 36 + 8))

def draw_moon_eater(surf, x, y, frame=0, hp_ratio=1.0):
    """Level 3 boss: colossal cosmic dragon — layered pixel art."""
    t = frame * 0.045

    # ── 1. Deep cosmic aura (outermost, drawn first) ──────────────────────
    for r in range(90, 30, -12):
        alpha = int(28 * (r - 30) / 60)
        gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (10, 20, 100, alpha), (r, r), r)
        surf.blit(gs, (x - r, y - 30 - r))

    # ── 2. Tail (sinuous chain of scaled segments) ────────────────────────
    tail_segs = 9
    for i in range(tail_segs, 0, -1):
        frac    = i / tail_segs
        seg_r   = max(3, int(14 * frac))
        wave    = math.sin(t * 1.2 + i * 0.55) * (18 + i * 4)
        seg_x   = x + int(12 + i * 14 * math.cos(0.5 + i * 0.18))
        seg_y   = y + 30 + int(i * 9 + wave * 0.4)
        # Scale colour — darker towards tip
        shade   = int(20 + 35 * frac)
        pygame.draw.circle(surf, (shade, shade * 2, 100 + shade), (seg_x, seg_y), seg_r)
        pygame.draw.circle(surf, (30, 60, 180), (seg_x, seg_y), seg_r, 1)
        # Scale ridge line
        if i < tail_segs:
            prev_frac = (i + 1) / tail_segs
            prev_x    = x + int(12 + (i + 1) * 14 * math.cos(0.5 + (i + 1) * 0.18))
            prev_y    = y + 30 + int((i + 1) * 9 + math.sin(t * 1.2 + (i + 1) * 0.55) * (18 + (i + 1) * 4) * 0.4)
            pygame.draw.line(surf, (40, 80, 200), (prev_x, prev_y), (seg_x, seg_y), max(1, seg_r - 2))

    # ── 3. Wings ──────────────────────────────────────────────────────────
    wing_beat  = math.sin(t * 2.0)
    wing_raise = int(28 * wing_beat)
    wing_curl  = int(12 * abs(wing_beat))

    # Wing base colour layers (dark → bright edge)
    for wing_side, flip in [(-1, True), (1, False)]:
        sign = wing_side
        # Primary membrane (large)
        w_tip_x = x + sign * (88 + wing_curl)
        w_tip_y = y - 55 - wing_raise
        w_mid_x = x + sign * 60
        w_mid_y = y - 20 + int(wing_raise * 0.3)
        w_bot_x = x + sign * 55
        w_bot_y = y + 22

        membrane = [
            (x + sign * 20, y - 18),
            (w_tip_x,        w_tip_y),
            (w_mid_x,        w_mid_y),
            (w_bot_x,        w_bot_y),
            (x + sign * 22, y + 18),
        ]
        pygame.draw.polygon(surf, (12, 18, 80),  membrane)
        pygame.draw.polygon(surf, (30, 50, 160), membrane, 2)

        # Inner secondary wing lobe
        lobe = [
            (x + sign * 20, y - 18),
            (x + sign * (60 + wing_curl // 2), y - 35 - wing_raise // 2),
            (x + sign * 45, y + 5),
        ]
        pygame.draw.polygon(surf, (18, 28, 110), lobe)

        # Wing membrane veins (3 ribs fanning out)
        rib_origins = [(x + sign * 20, y - 18),
                       (x + sign * 22, y + 2),
                       (x + sign * 22, y + 18)]
        rib_tips    = [(w_tip_x, w_tip_y),
                       (w_mid_x, w_mid_y),
                       (w_bot_x, w_bot_y)]
        for ro, rt in zip(rib_origins, rib_tips):
            pygame.draw.line(surf, (50, 90, 200), ro, rt, 2)
            # Sub-veins along each rib
            for frac in [0.4, 0.7]:
                mid  = (int(ro[0] + (rt[0]-ro[0])*frac), int(ro[1] + (rt[1]-ro[1])*frac))
                perp = (mid[0] + sign * int(10*(1-frac)), mid[1] + int(-8*(1-frac)))
                pygame.draw.line(surf, (40, 70, 160), mid, perp, 1)

        # Glowing leading edge
        edge_glow = int(160 + 80 * abs(wing_beat))
        pygame.draw.line(surf, (edge_glow, edge_glow, 255),
                         (x + sign * 20, y - 18), (w_tip_x, w_tip_y), 2)

    # ── 4. Hind legs / claws (gripping the moon orb) ─────────────────────
    moon_y = y + 58
    for side, angle_base in [(-1, 2.2), (1, 0.9)]:
        leg_swing = int(4 * math.sin(t * 1.5 + side))
        lx = x + side * 22 + leg_swing
        ly = y + 24
        # Thigh
        pygame.draw.line(surf, (25, 45, 140), (lx, ly),
                         (x + side * 18, moon_y - 12), 8)
        # Shin
        pygame.draw.line(surf, (20, 35, 120), (x + side * 18, moon_y - 12),
                         (x + side * 14, moon_y + 6), 6)
        # Toe claws
        for ci in range(3):
            cang = angle_base + ci * 0.35
            c1x  = x + side * 14 + int(8 * math.cos(cang))
            c1y  = moon_y + 6 + int(8 * math.sin(cang))
            c2x  = x + side * 14 + int(16 * math.cos(cang + 0.15 * side))
            c2y  = moon_y + 6 + int(16 * math.sin(cang + 0.15 * side))
            pygame.draw.line(surf, (80, 100, 200), (x + side * 14, moon_y + 6), (c1x, c1y), 3)
            pygame.draw.line(surf, (160, 180, 255), (c1x, c1y), (c2x, c2y), 2)

    # ── 5. Moon orb (devoured) ────────────────────────────────────────────
    moon_pulse = int(200 + 55 * math.sin(t * 0.8))
    # Outer glow
    for mr in range(28, 20, -4):
        ma = int(40 * (mr - 20) / 8)
        ms = pygame.Surface((mr * 2, mr * 2), pygame.SRCALPHA)
        pygame.draw.circle(ms, (moon_pulse, moon_pulse, 255, ma), (mr, mr), mr)
        surf.blit(ms, (x - mr, moon_y - mr))
    pygame.draw.circle(surf, (moon_pulse, moon_pulse, 255), (x, moon_y), 20)
    pygame.draw.circle(surf, WHITE, (x, moon_y), 20, 2)
    # Craters
    for cx2, cy2, cr in [(-8, 5, 4), (5, -6, 3), (-2, 10, 2), (7, 8, 2)]:
        pygame.draw.circle(surf, (160, 160, 200), (x + cx2, moon_y + cy2), cr)
        pygame.draw.circle(surf, (120, 120, 180), (x + cx2, moon_y + cy2), cr, 1)
    # Moon cracks (dark bite marks)
    pygame.draw.line(surf, (40, 40, 120), (x - 6, moon_y - 18), (x + 2, moon_y - 8), 2)
    pygame.draw.line(surf, (40, 40, 120), (x + 8,  moon_y - 18), (x + 4, moon_y - 6), 2)

    # ── 6. Body / torso ───────────────────────────────────────────────────
    torso_pts = [
        (x - 22, y - 22), (x + 22, y - 22),
        (x + 26, y + 20), (x - 26, y + 20)]
    pygame.draw.polygon(surf, (22, 38, 130), torso_pts)
    # Chest scale rows
    for row in range(3):
        for col in range(4):
            sx2 = x - 14 + col * 10
            sy2 = y - 16 + row * 12
            pygame.draw.ellipse(surf, (30, 55, 160), (sx2, sy2, 10, 8))
            pygame.draw.ellipse(surf, (50, 80, 200), (sx2, sy2, 10, 8), 1)
    # Torso outline
    pygame.draw.polygon(surf, (40, 70, 200), torso_pts, 2)
    # Glowing chest gem
    gem_glow = int(180 + 75 * abs(math.sin(t * 1.5)))
    pygame.draw.circle(surf, (gem_glow, gem_glow, 255), (x, y + 2), 7)
    pygame.draw.circle(surf, WHITE, (x, y + 2), 4)
    pygame.draw.circle(surf, (200, 220, 255), (x - 2, y), 2)

    # ── 7. Neck ───────────────────────────────────────────────────────────
    neck_sway = int(4 * math.sin(t * 0.7))
    pygame.draw.polygon(surf, (28, 46, 150), [
        (x - 12, y - 22), (x + 12, y - 22),
        (x + 10 + neck_sway, y - 46), (x - 10 + neck_sway, y - 46)])
    # Neck scales
    for ni in range(3):
        nx2 = x + neck_sway + int(ni * 4 - 4)
        ny2 = y - 40 + ni * 8
        pygame.draw.circle(surf, (40, 70, 180), (nx2, ny2), 4)

    # ── 8. Head ───────────────────────────────────────────────────────────
    hx = x + neck_sway
    hy = y - 46
    # Skull shape — elongated dragon snout
    pygame.draw.ellipse(surf, (30, 52, 168), (hx - 22, hy - 20, 44, 28))
    # Snout extension
    snout_pts = [
        (hx - 16, hy + 5), (hx + 16, hy + 5),
        (hx + 22, hy + 18), (hx - 22, hy + 18)]
    pygame.draw.polygon(surf, (28, 48, 158), snout_pts)
    pygame.draw.polygon(surf, (45, 75, 200), snout_pts, 1)

    # Horns (two main, two secondary)
    horn_pairs = [
        [(hx - 14, hy - 14), (hx - 22, hy - 42), (hx - 8, hy - 14)],
        [(hx + 8,  hy - 14), (hx + 22, hy - 42), (hx + 14, hy - 14)],
    ]
    for pts in horn_pairs:
        pygame.draw.polygon(surf, (20, 35, 130), pts)
        pygame.draw.polygon(surf, (60, 100, 220), pts, 2)
    # Small secondary horns
    pygame.draw.polygon(surf, (25, 42, 145),
                        [(hx - 8, hy - 12), (hx - 14, hy - 26), (hx - 4, hy - 12)])
    pygame.draw.polygon(surf, (25, 42, 145),
                        [(hx + 4, hy - 12), (hx + 14, hy - 26), (hx + 8,  hy - 12)])
    # Head crest spines along top
    for i in range(5):
        sx2 = hx - 16 + i * 8
        sh  = int(6 + 4 * math.sin(i * 0.8 + t * 0.5))
        pygame.draw.line(surf, (50, 90, 210), (sx2, hy - 18), (sx2, hy - 18 - sh), 2)

    # Head outline
    pygame.draw.ellipse(surf, (50, 85, 210), (hx - 22, hy - 20, 44, 28), 2)

    # ── 9. Eyes (layered — matching The Watcher quality) ──────────────────
    for side, ex_off in [(-1, -9), (1, 9)]:
        ex2 = hx + ex_off
        ey2 = hy - 8

        # Sclera (not pure white — slightly blue-tinted for cosmic feel)
        pygame.draw.circle(surf, (200, 210, 255), (ex2, ey2), 7)

        # Iris drifts on a slow ellipse path
        iris_t   = t * 0.5 + side * math.pi
        iris_dx  = int(2 * math.cos(iris_t))
        iris_dy  = int(2 * math.sin(iris_t * 0.7))
        iris_x   = ex2 + iris_dx
        iris_y   = ey2 + iris_dy

        # Iris layers: outer, mid, slit pupil
        eye_glow = int(160 + 80 * abs(math.sin(t * 2.2)))
        pygame.draw.circle(surf, (0, eye_glow // 3, eye_glow),  (iris_x, iris_y), 5)
        pygame.draw.circle(surf, (0, eye_glow // 2, 255),       (iris_x, iris_y), 3)
        # Vertical slit pupil (dragon-style)
        pygame.draw.ellipse(surf, BLACK, (iris_x - 1, iris_y - 3, 2, 6))
        # Highlight dot
        pygame.draw.circle(surf, WHITE, (iris_x - 1, iris_y - 2), 1)
        # Eye outline
        pygame.draw.circle(surf, (60, 100, 220), (ex2, ey2), 7, 1)

        # Pulsing cosmic glow around each eye
        glow_r = int(6 + 4 * abs(math.sin(t * 2.5)))
        gs2    = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        glow_a = int(80 + 40 * abs(math.sin(t * 2.5)))
        pygame.draw.circle(gs2, (eye_glow // 2, eye_glow // 2, 255, glow_a),
                           (glow_r, glow_r), glow_r)
        surf.blit(gs2, (ex2 - glow_r, ey2 - glow_r))

    # ── 10. Jaw / mouth ───────────────────────────────────────────────────
    jaw_open = int(7 * abs(math.sin(t * 1.8)))
    jaw_pts  = [
        (hx - 16, hy + 6 + jaw_open),
        (hx + 16, hy + 6 + jaw_open),
        (hx + 22, hy + 18 + jaw_open),
        (hx - 22, hy + 18 + jaw_open)]
    pygame.draw.polygon(surf, (28, 46, 155), jaw_pts)
    # Inner mouth glow when open
    if jaw_open > 2:
        mouth_r = jaw_open * 3
        ms2     = pygame.Surface((mouth_r * 2, mouth_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ms2, (100, 50, 255, jaw_open * 15), (mouth_r, mouth_r), mouth_r)
        surf.blit(ms2, (hx - mouth_r, hy + 10))
    # Teeth — two rows of sharp triangles
    for i in range(7):
        tx2 = hx - 18 + i * 6
        # Upper fangs
        pygame.draw.polygon(surf, (220, 225, 245), [
            (tx2,     hy + 5), (tx2 + 3, hy + 5),
            (tx2 + 1, hy + 5 + 4 + (3 if i in [2,4] else 0))])
        # Lower fangs (move with jaw)
        pygame.draw.polygon(surf, (200, 205, 230), [
            (tx2,     hy + 8 + jaw_open),
            (tx2 + 3, hy + 8 + jaw_open),
            (tx2 + 1, hy + 8 + jaw_open - 4 - (3 if i in [1,3,5] else 0))])

    # ── 11. Star specks on body (static cosmic texture) ───────────────────
    rng = random.Random(42)
    for _ in range(10):
        sx2 = x + rng.randint(-18, 18)
        sy2 = y + rng.randint(-18, 18)
        pygame.draw.circle(surf, WHITE, (sx2, sy2), 1)

def draw_ship(surf, x, y, frame=0, broken=True):
    """Draw the crashed/repaired ship."""
    # Main hull
    hull_col = MOON_DARK if broken else LIGHT_GREY
    pygame.draw.polygon(surf, hull_col,
                        [(x, y - 30), (x - 20, y + 10), (x + 20, y + 10)])
    # Window
    pygame.draw.circle(surf, CYAN if not broken else MOON_DARK, (x, y - 10), 7)
    # Legs
    pygame.draw.line(surf, MOON_GREY, (x - 15, y + 10), (x - 22, y + 24), 3)
    pygame.draw.line(surf, MOON_GREY, (x + 15, y + 10), (x + 22, y + 24), 3)
    pygame.draw.line(surf, MOON_GREY, (x,      y + 10), (x,       y + 24), 3)
    # Damage cracks if broken
    if broken:
        pygame.draw.line(surf, BLOOD_RED, (x - 5, y - 20), (x + 8, y), 2)
        pygame.draw.line(surf, BLOOD_RED, (x - 10, y),     (x,     y + 8), 2)
    # Engine glow if repaired
    if not broken:
        glow = int(200 + 55 * math.sin(frame * 0.1))
        pygame.draw.circle(surf, (glow, glow // 2, 0), (x, y + 12), 6)
        spawn_particles(x, y + 14, ORANGE, 1, 1, 15, 2)

def _part_glow(surf, x, y, colour, part_type):
    """Draw a pulsing glow halo behind a ship part."""
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.004 + part_type * 1.3)
    r = int(18 + 6 * pulse)
    alpha = int(60 + 40 * pulse)
    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*colour, alpha), (r, r), r)
    surf.blit(s, (x - r, y - r))

def draw_part_engine(surf, x, y):
    """Part 0 – Engine Core: a chunky rocket nozzle with heat glow."""
    t = pygame.time.get_ticks() * 0.004
    _part_glow(surf, x, y, ORANGE, 0)
    # Main nozzle body (bell shape via polygon)
    pygame.draw.polygon(surf, (160, 100, 40),
                        [(x - 8, y - 14), (x + 8, y - 14),
                         (x + 13, y + 6),  (x - 13, y + 6)])
    pygame.draw.polygon(surf, (200, 130, 60),
                        [(x - 8, y - 14), (x + 8, y - 14),
                         (x + 13, y + 6),  (x - 13, y + 6)], 2)
    # Nozzle throat (inner dark ring)
    pygame.draw.ellipse(surf, (80, 50, 20),  (x - 7, y - 16, 14, 6))
    pygame.draw.ellipse(surf, ORANGE,         (x - 7, y - 16, 14, 6), 1)
    # Nozzle flare opening
    pygame.draw.ellipse(surf, (50, 30, 10),  (x - 13, y + 3, 26, 8))
    pygame.draw.ellipse(surf, (220, 140, 60),(x - 13, y + 3, 26, 8), 1)
    # Engine glow fire (animated)
    flame_h = int(8 + 5 * abs(math.sin(t)))
    flame_col_inner = (255, 220, 80)
    flame_col_outer = (255, 120, 20)
    pygame.draw.polygon(surf, flame_col_outer,
                        [(x - 10, y + 7), (x + 10, y + 7),
                         (x + 5,  y + 7 + flame_h), (x - 5, y + 7 + flame_h)])
    pygame.draw.polygon(surf, flame_col_inner,
                        [(x - 5, y + 7), (x + 5, y + 7),
                         (x + 2, y + 7 + flame_h - 3), (x - 2, y + 7 + flame_h - 3)])
    # Mounting bolts
    for bx in [x - 8, x + 8]:
        pygame.draw.circle(surf, MOON_GREY, (bx, y - 10), 2)
        pygame.draw.circle(surf, WHITE,     (bx, y - 10), 2, 1)
    # Label
    draw_text(surf, "ENGINE", font_tiny, ORANGE, x, y + 22)

def draw_part_fuel_cell(surf, x, y):
    """Part 1 – Fuel Cell: cylindrical canister with pressure gauges."""
    t = pygame.time.get_ticks() * 0.003
    _part_glow(surf, x, y, CYAN, 1)
    # Cylinder body
    pygame.draw.rect(surf, (40, 120, 160),  (x - 10, y - 14, 20, 24))
    pygame.draw.rect(surf, CYAN,             (x - 10, y - 14, 20, 24), 2)
    # Top cap
    pygame.draw.ellipse(surf, (60, 160, 200),(x - 10, y - 18, 20, 8))
    pygame.draw.ellipse(surf, CYAN,          (x - 10, y - 18, 20, 8), 1)
    # Bottom cap
    pygame.draw.ellipse(surf, (30, 90, 130), (x - 10, y + 8,  20, 8))
    pygame.draw.ellipse(surf, CYAN,          (x - 10, y + 8,  20, 8), 1)
    # Pressure gauge circle
    pygame.draw.circle(surf, (10, 30, 50),  (x, y - 4), 6)
    pygame.draw.circle(surf, CYAN,          (x, y - 4), 6, 1)
    # Gauge needle (animated)
    needle_angle = math.pi * 1.1 + 0.8 * math.sin(t)
    nx = int(x + 4 * math.cos(needle_angle))
    ny = int(y - 4 + 4 * math.sin(needle_angle))
    pygame.draw.line(surf, (255, 80, 80), (x, y - 4), (nx, ny), 1)
    # Horizontal band markings
    for by in [y - 2, y + 4]:
        pygame.draw.line(surf, (0, 180, 220), (x - 9, by), (x + 9, by), 1)
    # Valve pipe on side
    pygame.draw.rect(surf, MOON_GREY, (x + 10, y - 2, 6, 4))
    pygame.draw.circle(surf, MOON_DARK, (x + 16, y), 3)
    pygame.draw.circle(surf, MOON_GREY, (x + 16, y), 3, 1)
    draw_text(surf, "FUEL", font_tiny, CYAN, x, y + 22)

def draw_part_nav_module(surf, x, y):
    """Part 2 – Nav Module: circuit board with blinking LEDs and antenna."""
    t = pygame.time.get_ticks()
    _part_glow(surf, x, y, GOLD, 2)
    # PCB board (green rectangle)
    pygame.draw.rect(surf, (20, 80, 30),  (x - 14, y - 12, 28, 22))
    pygame.draw.rect(surf, (40, 160, 50), (x - 14, y - 12, 28, 22), 2)
    # Circuit traces (horizontal + vertical lines)
    for lx in [x - 8, x, x + 8]:
        pygame.draw.line(surf, (30, 120, 40), (lx, y - 12), (lx, y + 10), 1)
    for ly in [y - 6, y, y + 6]:
        pygame.draw.line(surf, (30, 120, 40), (x - 14, ly), (x + 14, ly), 1)
    # Chip (dark square with pins)
    pygame.draw.rect(surf, (15, 15, 20),  (x - 6, y - 5, 12, 10))
    pygame.draw.rect(surf, (80, 80, 100), (x - 6, y - 5, 12, 10), 1)
    for py2 in [y - 3, y, y + 3]:
        pygame.draw.line(surf, (150, 150, 160), (x - 8, py2), (x - 6, py2), 1)
        pygame.draw.line(surf, (150, 150, 160), (x + 6, py2), (x + 8, py2), 1)
    # Blinking LEDs
    for i, (ldx, ldy, lcol) in enumerate([(-10, -9, RED), (10, -9, (0,200,0)), (0, -9, GOLD)]):
        blink = (t // (200 + i * 80)) % 2 == 0
        col = lcol if blink else (20, 20, 20)
        pygame.draw.circle(surf, col, (x + ldx, y + ldy), 2)
    # Antenna sticking up
    pygame.draw.line(surf, MOON_GREY, (x + 8, y - 12), (x + 8, y - 24), 2)
    pygame.draw.circle(surf, GOLD, (x + 8, y - 24), 3)
    pygame.draw.circle(surf, YELLOW, (x + 8, y - 24), 3, 1)
    draw_text(surf, "NAV", font_tiny, GOLD, x, y + 22)

def draw_part_comm_array(surf, x, y):
    """Part 3 – Comm Array: satellite dish with signal rings."""
    t = pygame.time.get_ticks() * 0.003
    _part_glow(surf, x, y, LIGHT_GREY, 3)
    # Dish bowl (arc / polygon)
    dish_pts = [(x - 16, y + 4), (x - 14, y - 8),
                (x,      y - 14), (x + 14, y - 8), (x + 16, y + 4)]
    pygame.draw.polygon(surf, (100, 100, 120), dish_pts)
    pygame.draw.polygon(surf, LIGHT_GREY,      dish_pts, 2)
    # Dish inner shading
    inner = [(x - 10, y + 2), (x - 9, y - 5),
             (x,      y - 10), (x + 9, y - 5), (x + 10, y + 2)]
    pygame.draw.polygon(surf, (130, 130, 155), inner)
    # Central focal point
    pygame.draw.line(surf, MOON_GREY, (x, y + 4), (x + 8, y - 10), 2)
    pygame.draw.circle(surf, WHITE, (x + 8, y - 10), 3)
    # Mount pole
    pygame.draw.rect(surf, MOON_DARK, (x - 2, y + 4, 4, 10))
    pygame.draw.rect(surf, MOON_GREY, (x - 6, y + 12, 12, 3))
    # Animated signal rings (emanating from focal point)
    sig_phase = (t % (math.pi * 2))
    for i in range(3):
        ring_r = int(6 + i * 6 + (sig_phase / (math.pi * 2)) * 6)
        ring_alpha = max(0, int(180 - ring_r * 8))
        rs = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(rs, (200, 200, 255, ring_alpha), (ring_r, ring_r), ring_r, 1)
        surf.blit(rs, (x + 8 - ring_r, y - 10 - ring_r))
    draw_text(surf, "COMMS", font_tiny, LIGHT_GREY, x, y + 22)

def draw_part_life_support(surf, x, y):
    """Part 4 – Life Support: oxygen tank with tubes and pressure readout."""
    t = pygame.time.get_ticks() * 0.003
    _part_glow(surf, x, y, (100, 220, 100), 4)
    # Main tank (rounded rect via ellipse + rect)
    pygame.draw.rect(surf, (30, 130, 60),   (x - 9, y - 10, 18, 20))
    pygame.draw.ellipse(surf, (30, 130, 60), (x - 9, y - 16, 18, 12))
    pygame.draw.ellipse(surf, (30, 130, 60), (x - 9, y + 8,  18, 12))
    # Outline
    pygame.draw.rect(surf, (60, 200, 80),   (x - 9, y - 10, 18, 20), 2)
    pygame.draw.ellipse(surf, (60, 200, 80), (x - 9, y - 16, 18, 12), 2)
    pygame.draw.ellipse(surf, (60, 200, 80), (x - 9, y + 8,  18, 12), 2)
    # O2 label on tank
    draw_text(surf, "O2", font_tiny, (180, 255, 180), x, y - 2)
    # Valve on top
    pygame.draw.rect(surf, MOON_DARK, (x - 3, y - 20, 6, 5))
    pygame.draw.rect(surf, MOON_GREY, (x - 3, y - 20, 6, 5), 1)
    # Tube coming out of valve, curling to the right
    tube_pts = [(x, y - 20), (x, y - 26), (x + 8, y - 26), (x + 8, y - 18)]
    pygame.draw.lines(surf, (160, 160, 160), False, tube_pts, 2)
    # Tube connector
    pygame.draw.circle(surf, MOON_GREY, (x + 8, y - 18), 3)
    pygame.draw.circle(surf, WHITE, (x + 8, y - 18), 3, 1)
    # Pressure bar on side
    bar_fill = int(10 + 6 * abs(math.sin(t)))
    pygame.draw.rect(surf, (20, 60, 30),    (x + 10, y - 8, 5, 16))
    pygame.draw.rect(surf, (60, 200, 80),   (x + 10, y - 8 + (16 - bar_fill), 5, bar_fill))
    pygame.draw.rect(surf, MOON_GREY,       (x + 10, y - 8, 5, 16), 1)
    draw_text(surf, "LIFE SUP", font_tiny, (100, 220, 100), x, y + 22)

# Part name labels aligned to part index used in Level1._place_parts
PART_NAMES = ["ENGINE", "FUEL CELL", "NAV MOD", "COMMS", "LIFE SUP"]
PART_DRAWERS = [draw_part_engine, draw_part_fuel_cell,
                draw_part_nav_module, draw_part_comm_array, draw_part_life_support]

def draw_ship_part(surf, x, y, part_type=0):
    """Dispatch to the correct detailed pixel-art part drawing."""
    idx = part_type % len(PART_DRAWERS)
    PART_DRAWERS[idx](surf, x, y)

def draw_moon_surface(surf, y_base):
    """Draw the moon ground."""
    pygame.draw.rect(surf, MOON_DARK, (0, y_base, SCREEN_W, SCREEN_H - y_base))
    pygame.draw.line(surf, MOON_GREY, (0, y_base), (SCREEN_W, y_base), 2)
    # Craters
    for cx2, cr, cy2 in [(100, 18, y_base + 8), (300, 12, y_base + 5),
                          (500, 25, y_base + 10), (650, 15, y_base + 6),
                          (200, 8,  y_base + 4)]:
        pygame.draw.ellipse(surf, CRATER, (cx2 - cr, cy2, cr * 2, cr // 2))
        pygame.draw.ellipse(surf, MOON_GREY, (cx2 - cr, cy2, cr * 2, cr // 2), 1)

def draw_bullet(surf, x, y, col=YELLOW):
    pygame.draw.circle(surf, col, (int(x), int(y)), 4)
    pygame.draw.circle(surf, WHITE, (int(x), int(y)), 2)

# ─────────────────────────────────────────────
#  ADDITIONAL SPRITE DRAWERS
# ─────────────────────────────────────────────

def draw_homing_orb(surf, x, y, frame=0):
    """Glowing purple tracking projectile with pulsing halo and trailing sparks."""
    t = frame * 0.05
    pulse = 0.8 + 0.2 * math.sin(t * 4)
    ix, iy = int(x), int(y)
    # Outer glow halo (layered SRCALPHA circles)
    for r in range(18, 6, -3):
        alpha = int(35 * pulse * (r - 6) / 12)
        gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*VORTEX_PUR, alpha), (r, r), r)
        surf.blit(gs, (ix - r, iy - r))
    # Core orb — violet gradient
    core_r = int(6 * pulse)
    pygame.draw.circle(surf, DEEP_PURP, (ix, iy), core_r + 4)
    pygame.draw.circle(surf, PURPLE, (ix, iy), core_r + 2)
    pygame.draw.circle(surf, VORTEX_PUR, (ix, iy), core_r)
    # Bright hot-spot
    pygame.draw.circle(surf, WHITE, (ix - 2, iy - 2), max(1, core_r // 2))
    # Trailing sparks (3 small dots behind the orb)
    for i in range(3):
        angle = math.pi + (i - 1) * 0.5 + math.sin(t * 3 + i) * 0.4
        dist = 10 + 4 * i + int(3 * math.sin(t * 5 + i * 2))
        sx = ix + int(dist * math.cos(angle))
        sy = iy + int(dist * math.sin(angle))
        spark_r = max(1, 3 - i)
        spark_alpha = int(180 - i * 50)
        ss = pygame.Surface((spark_r * 2, spark_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ss, (*PURPLE, spark_alpha), (spark_r, spark_r), spark_r)
        surf.blit(ss, (sx - spark_r, sy - spark_r))
    # Rim highlight
    pygame.draw.circle(surf, VORTEX_PUR, (ix, iy), core_r + 4, 1)


def draw_mini_eye(surf, x, y, frame=0):
    """Smaller Watcher minion (~60% scale). Floating eyeball with tiny wings."""
    t = frame * 0.05
    bob = int(3 * math.sin(t * 1.3))
    cy = y + bob
    # Soft glow aura
    for r in range(14, 6, -3):
        alpha = int(45 * (r - 6) / 8)
        gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*PURPLE, alpha), (r, r), r)
        surf.blit(gs, (x - r, cy - r))
    # Eyeball body
    pygame.draw.circle(surf, WHITE, (x, cy), 9)
    pygame.draw.circle(surf, LIGHT_GREY, (x, cy), 9, 1)
    # Iris — tracks slightly with time
    iris_x = x + int(2 * math.cos(t * 0.6))
    iris_y = cy + int(2 * math.sin(t * 0.8))
    pygame.draw.circle(surf, PURPLE, (iris_x, iris_y), 5)
    pygame.draw.circle(surf, BLACK, (iris_x, iris_y), 3)
    pygame.draw.circle(surf, WHITE, (iris_x - 1, iris_y - 1), 1)
    # Veins (3 thin red lines)
    for i in range(3):
        angle = i * math.pi * 2 / 3 + t * 0.15
        vx = int(x + 7 * math.cos(angle))
        vy = int(cy + 7 * math.sin(angle))
        pygame.draw.line(surf, BLOOD_RED, (x, cy), (vx, vy), 1)
    # Tiny wings
    wing_flap = int(3 * math.sin(t * 4))
    # Left wing
    pts_l = [(x - 9, cy), (x - 18, cy - 7 + wing_flap), (x - 16, cy + 4)]
    pygame.draw.polygon(surf, DEEP_PURP, pts_l)
    pygame.draw.polygon(surf, PURPLE, pts_l, 1)
    # Right wing
    pts_r = [(x + 9, cy), (x + 18, cy - 7 + wing_flap), (x + 16, cy + 4)]
    pygame.draw.polygon(surf, DEEP_PURP, pts_r)
    pygame.draw.polygon(surf, PURPLE, pts_r, 1)


def draw_laser_telegraph(surf, x1, y1, x2, y2, progress=0.0):
    """Laser telegraph line. Thin flickering dots at low progress, thick beam at high."""
    progress = max(0.0, min(1.0, progress))
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1:
        return
    nx, ny = dx / length, dy / length
    if progress <= 0.7:
        # Thin flickering dotted line
        dot_spacing = 8
        num_dots = max(1, int(length / dot_spacing))
        flicker = 0.5 + 0.5 * math.sin(progress * 40 + x1 * 0.1)
        alpha = int(80 + 120 * progress / 0.7 * flicker)
        for i in range(num_dots):
            frac = i / max(1, num_dots - 1)
            px = int(x1 + dx * frac)
            py = int(y1 + dy * frac)
            ds = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(ds, (*LASER_RED, alpha), (3, 3), 2)
            surf.blit(ds, (px - 3, py - 3))
    else:
        # Thick bright beam — glow, beam, white core
        beam_prog = (progress - 0.7) / 0.3  # 0..1 within beam phase
        # Outer glow
        glow_w = int(6 + 10 * beam_prog)
        gs = pygame.Surface((int(length) + glow_w * 2, glow_w * 2), pygame.SRCALPHA)
        for r in range(glow_w, 2, -2):
            alpha = int(40 * beam_prog * (glow_w - r) / glow_w)
            pygame.draw.line(gs, (*LASER_RED, alpha), (glow_w, glow_w), (int(length) + glow_w, glow_w), r * 2)
        # Rotate and blit the glow surface
        angle_deg = math.degrees(math.atan2(-dy, dx))
        gs_rot = pygame.transform.rotate(gs, angle_deg)
        gr = gs_rot.get_rect(center=((x1 + x2) // 2, (y1 + y2) // 2))
        surf.blit(gs_rot, gr)
        # Main beam line
        beam_thick = int(2 + 4 * beam_prog)
        pygame.draw.line(surf, LASER_RED, (int(x1), int(y1)), (int(x2), int(y2)), beam_thick)
        # White hot core
        core_thick = max(1, int(beam_thick * 0.4))
        pygame.draw.line(surf, WHITE, (int(x1), int(y1)), (int(x2), int(y2)), core_thick)


def draw_asteroid(surf, x, y, size=20, seed=0):
    """Floating rock/asteroid with deterministic random shape, craters, and highlight."""
    rng = random.Random(seed)
    num_verts = rng.randint(6, 8)
    # Generate polygon vertices
    verts = []
    for i in range(num_verts):
        angle = (2 * math.pi * i) / num_verts + rng.uniform(-0.3, 0.3)
        r = size * rng.uniform(0.65, 1.0)
        verts.append((int(x + r * math.cos(angle)), int(y + r * math.sin(angle))))
    # Base rock — dark grey fill
    base_col = (rng.randint(70, 90), rng.randint(65, 80), rng.randint(55, 70))
    pygame.draw.polygon(surf, base_col, verts)
    # Lighter edge outline
    edge_col = (base_col[0] + 40, base_col[1] + 40, base_col[2] + 30)
    pygame.draw.polygon(surf, edge_col, verts, 2)
    # Highlight edge on upper-left portion
    hl_col = (min(255, base_col[0] + 70), min(255, base_col[1] + 60), min(255, base_col[2] + 50))
    for i in range(len(verts)):
        v1 = verts[i]
        v2 = verts[(i + 1) % len(verts)]
        # Only highlight edges mostly above or to the left of center
        mid_y = (v1[1] + v2[1]) / 2
        if mid_y < y:
            pygame.draw.line(surf, hl_col, v1, v2, 2)
    # Crater dots (3-5 small dark circles)
    num_craters = rng.randint(3, 5)
    for _ in range(num_craters):
        ca = rng.uniform(0, 2 * math.pi)
        cd = rng.uniform(0, size * 0.5)
        cx = int(x + cd * math.cos(ca))
        cy_c = int(y + cd * math.sin(ca))
        cr = rng.randint(1, max(2, size // 8))
        crater_col = (max(0, base_col[0] - 25), max(0, base_col[1] - 25), max(0, base_col[2] - 20))
        pygame.draw.circle(surf, crater_col, (cx, cy_c), cr)
        pygame.draw.circle(surf, edge_col, (cx, cy_c), cr, 1)


def draw_powerup(surf, x, y, kind='health', frame=0):
    """Glowing pickup icon with pulsing halo and gentle bob animation."""
    t = frame * 0.05
    bob = int(3 * math.sin(t * 1.5))
    pulse = 0.7 + 0.3 * math.sin(t * 3)
    iy = y + bob
    # Pick colour and glow based on kind
    if kind == 'health':
        glow_col = HP_GREEN
        icon_col = POWER_GRN
    elif kind == 'damage':
        glow_col = ORANGE
        icon_col = RED
    else:  # shield
        glow_col = SHIELD_BLU
        icon_col = SHIELD_BLU
    # Outer glow halo
    for r in range(16, 6, -3):
        alpha = int(50 * pulse * (r - 6) / 10)
        gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*glow_col, alpha), (r, r), r)
        surf.blit(gs, (x - r, iy - r))
    # Background circle
    pygame.draw.circle(surf, DARK_GREY, (x, iy), 10)
    pygame.draw.circle(surf, icon_col, (x, iy), 10, 2)
    # Icon inside
    if kind == 'health':
        # Green cross
        pygame.draw.rect(surf, icon_col, (x - 2, iy - 6, 4, 12))
        pygame.draw.rect(surf, icon_col, (x - 6, iy - 2, 12, 4))
        pygame.draw.rect(surf, WHITE, (x - 1, iy - 5, 2, 10))
        pygame.draw.rect(surf, WHITE, (x - 5, iy - 1, 10, 2))
    elif kind == 'damage':
        # Arrow / sword pointing up
        pygame.draw.line(surf, icon_col, (x, iy + 6), (x, iy - 5), 2)
        pygame.draw.polygon(surf, icon_col, [(x, iy - 7), (x - 4, iy - 2), (x + 4, iy - 2)])
        pygame.draw.line(surf, WHITE, (x, iy + 5), (x, iy - 4), 1)
    else:
        # Shield — small circle with highlight
        pygame.draw.circle(surf, icon_col, (x, iy), 6, 2)
        pygame.draw.arc(surf, WHITE, (x - 5, iy - 5, 10, 10), 0.5, 2.0, 2)
    # Sparkle at top
    spark_y = iy - 12 - int(2 * math.sin(t * 5))
    spark_alpha = int(180 * pulse)
    ss = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.circle(ss, (*WHITE, spark_alpha), (3, 3), 2)
    surf.blit(ss, (x - 3, spark_y - 3))


def draw_gravity_well(surf, x, y, radius=60, frame=0):
    """Swirling vortex with concentric rings, spiral arms, and dark center."""
    t = frame * 0.05
    ix, iy = int(x), int(y)
    # Concentric semi-transparent rings (outer to inner, getting darker)
    num_rings = 6
    for i in range(num_rings):
        frac = i / num_rings
        r = int(radius * (1 - frac * 0.8))
        alpha = int(25 + 50 * frac)
        dark = int(140 * (1 - frac * 0.7))
        ring_s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring_s, (dark, 10 + int(30 * (1 - frac)), dark + 40, alpha), (r, r), r)
        pygame.draw.circle(ring_s, (*VORTEX_PUR, int(alpha * 0.6)), (r, r), r, 2)
        surf.blit(ring_s, (ix - r, iy - r))
    # Spiral arms (4 arms that rotate with time)
    num_arms = 4
    for arm in range(num_arms):
        base_angle = (2 * math.pi * arm) / num_arms + t * 0.8
        pts = []
        for step in range(12):
            frac = step / 11
            a = base_angle + frac * math.pi * 1.5
            r = radius * (1 - frac * 0.85)
            px = ix + int(r * math.cos(a))
            py = iy + int(r * math.sin(a))
            pts.append((px, py))
        if len(pts) >= 2:
            arm_alpha = int(60 + 40 * math.sin(t * 2 + arm))
            arm_s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            offset_pts = [(p[0] - ix + radius + 2, p[1] - iy + radius + 2) for p in pts]
            pygame.draw.lines(arm_s, (*VORTEX_PUR, arm_alpha), False, offset_pts, 2)
            surf.blit(arm_s, (ix - radius - 2, iy - radius - 2))
    # Dark center core
    core_r = max(4, int(radius * 0.15))
    core_s = pygame.Surface((core_r * 2, core_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(core_s, (*DEEP_PURP, 220), (core_r, core_r), core_r)
    pygame.draw.circle(core_s, (*BLACK, 200), (core_r, core_r), core_r // 2)
    surf.blit(core_s, (ix - core_r, iy - core_r))
    # Bright ring at event horizon
    horizon_r = core_r + 3
    hs = pygame.Surface((horizon_r * 2, horizon_r * 2), pygame.SRCALPHA)
    pulse = int(140 + 60 * math.sin(t * 4))
    pygame.draw.circle(hs, (*PURPLE, pulse), (horizon_r, horizon_r), horizon_r, 2)
    surf.blit(hs, (ix - horizon_r, iy - horizon_r))
    # Orbiting particle dots
    for i in range(5):
        orbit_a = t * (1.2 + i * 0.3) + i * math.pi * 2 / 5
        orbit_r = int(radius * (0.3 + 0.15 * i))
        ox = ix + int(orbit_r * math.cos(orbit_a))
        oy = iy + int(orbit_r * math.sin(orbit_a))
        dot_alpha = int(120 + 80 * math.sin(t * 3 + i))
        ds = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(ds, (*VORTEX_PUR, dot_alpha), (3, 3), 2)
        surf.blit(ds, (ox - 3, oy - 3))


