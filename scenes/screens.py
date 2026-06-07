"""Title, dialogue, win/game-over, and transition screens."""

import pygame
import random
import math

from settings import *
from utils import *
from graphics.sprites import draw_ship
from core.particles import spawn_particles, update_particles

_gameover_sfx_channel = None

class TextScene:

    def __init__(self, lines, next_state=None, title="MISSION LOG", speaker="APOLLO ARCHIVE",
                 music_path=None, music_volume=0.5, stop_music_on_finish=None,
                 line_sounds=None, line_sound_range=None):
        # Clean old cutscene data so functions like intro_draw do not appear as text
        cleaned_lines = []

        if isinstance(lines, (list, tuple)):
            for item in lines:
                if callable(item):
                    continue
                cleaned_lines.append(str(item))
        else:
            if callable(lines):
                cleaned_lines = []
            else:
                cleaned_lines = [str(lines)]

        self.lines = cleaned_lines

        # If old code passed a draw/background function as the second argument, ignore it
        if callable(next_state):
            self.next_state = None
        else:
            self.next_state = next_state

        self.title = str(title) if title is not None and not callable(title) else "MISSION LOG"
        self.speaker = str(speaker) if speaker is not None and not callable(speaker) else "APOLLO ARCHIVE"

        self.done = False
        self.t = 0

        self.line_index = 0
        self.char_index = 0
        self.type_speed = 2
        self.pause_timer = 0

        self.full_line_visible = False
        self.fade_in = 0
        self.glitch_timer = 0
        self.glitch_offset = 0

        self.music_path = music_path
        self.music_volume = music_volume
        self._music_started = False
        self.stop_music_on_finish = (music_path is not None) if stop_music_on_finish is None else stop_music_on_finish

        self.line_sounds = {}
        if line_sounds:
            for idx, path in line_sounds.items():
                snd = load_sound(path)
                if snd:
                    self.line_sounds[idx] = snd
        self._played_line_sounds = set()

        self.range_sound = None
        self.range_start = self.range_end = -1
        self._range_channel = None
        if line_sound_range:
            start_idx, end_idx, path = line_sound_range
            self.range_sound = load_sound(path)
            self.range_start = start_idx
            self.range_end = end_idx

        self.star_seed = random.randint(1000, 9999)
        self.warning_pulse = 0
        self.skip_rect = pygame.Rect(SCREEN_W - 125, SCREEN_H - 47, 100, 30)

        # Fonts local to cutscene
        self.font_title = pygame.font.Font(None, 48)
        self.font_speaker = pygame.font.Font(None, 24)
        self.font_body = pygame.font.Font(None, 30)
        self.font_hint = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 18)

    def handle_event(self, event):
        # Mouse click skip button
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.skip_rect.collidepoint(event.pos):
                self._finish()
                return

        if event.type != pygame.KEYDOWN:
            return

        # SPACE / ENTER = continue dialogue
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            current_line = self._current_line()

            if not self.full_line_visible:
                self.char_index = len(current_line)
                self.full_line_visible = True
                return

            self._next_line()

        # S = skip cutscene
        elif event.key == pygame.K_s:
            self._finish()

    def _finish(self):
        self.done = True

        if self.stop_music_on_finish:
            stop_music(fade_ms=400)

        if self._range_channel is not None:
            self._range_channel.stop()
            self._range_channel = None


    def update(self):
        self.t += 1
        self.fade_in = min(255, self.fade_in + 7)

        if self.music_path and not self._music_started:
            self._music_started = True
            play_music(self.music_path, loops=-1, volume=self.music_volume)

        if self.line_index in self.line_sounds and self.line_index not in self._played_line_sounds:
            self._played_line_sounds.add(self.line_index)
            self.line_sounds[self.line_index].play()

        if self.range_sound:
            if self.line_index == self.range_start and self._range_channel is None:
                self._range_channel = self.range_sound.play(loops=-1)
            elif self.line_index >= self.range_end and self._range_channel is not None:
                self._range_channel.stop()
                self._range_channel = None

        # Random glitch hit
        if random.random() < 0.035:
            self.glitch_timer = random.randint(3, 8)
            self.glitch_offset = random.randint(-5, 5)

        if self.glitch_timer > 0:
            self.glitch_timer -= 1
        else:
            self.glitch_offset = 0

        if self.pause_timer > 0:
            self.pause_timer -= 1
            return

        current_line = self._current_line()

        if not self.full_line_visible:
            if self.t % self.type_speed == 0:
                self.char_index += 1

            if self.char_index >= len(current_line):
                self.char_index = len(current_line)
                self.full_line_visible = True
                self.pause_timer = 10


    def _current_line(self):
        if not self.lines:
            return ""

        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]

            if callable(line):
                self.line_index += 1
                continue

            return str(line)

        return ""

    def _next_line(self):
        self.line_index += 1
        self.char_index = 0
        self.full_line_visible = False
        self.pause_timer = 6

        if self.line_index >= len(self.lines):
            self._finish()

    def _wrap_text(self, text, font, max_width):
        text = str(text)
        words = text.split(" ")
        lines = []
        current = ""

        for word in words:
            test = word if current == "" else current + " " + word

            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def _render_text(self, surf, text, font, colour, x, y, alpha=255, center=False):
        text = str(text)  # prevents pygame text crash

        img = font.render(text, True, colour)
        img.set_alpha(alpha)
        rect = img.get_rect()

        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)

        surf.blit(img, rect)

    # ─────────────────────────────────────────────
    #  DRAW
    # ─────────────────────────────────────────────

    def draw(self, surf):
        self._draw_background(surf)
        self._draw_scanlines(surf)
        self._draw_main_panel(surf)
        self._draw_header(surf)
        self._draw_story_text(surf)
        self._draw_footer_prompt(surf)

    # Removed full-screen glitch overlay.
    # Title glitch remains inside _draw_header().
    
        self._draw_fade(surf)

    def _draw_background(self, surf):
        # Deep space background
        surf.fill((1, 2, 10))

        rng = random.Random(self.star_seed)

        for i in range(160):
            x = rng.randint(0, SCREEN_W)
            y = rng.randint(0, SCREEN_H)
            size = rng.choice([1, 1, 1, 2])
            pulse = 40 + int(35 * math.sin(self.t * 0.02 + i))
            shade = rng.randint(90, 180) + pulse
            shade = max(60, min(230, shade))
            pygame.draw.circle(surf, (shade, shade, shade), (x, y), size)

        # Slow moving red nebula glow
        glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        gx = SCREEN_W // 2 + int(80 * math.sin(self.t * 0.006))
        gy = SCREEN_H // 2 + int(50 * math.cos(self.t * 0.004))
        pygame.draw.circle(glow, (110, 0, 30, 45), (gx, gy), 260)
        pygame.draw.circle(glow, (50, 0, 100, 25), (SCREEN_W - gx, gy + 80), 220)
        surf.blit(glow, (0, 0))

        # Horror vignette
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for r in range(500, 120, -40):
            alpha = int((500 - r) * 0.26)
            pygame.draw.circle(vignette, (0, 0, 0, alpha), (SCREEN_W // 2, SCREEN_H // 2), r, 22)
        surf.blit(vignette, (0, 0))

    def _draw_scanlines(self, surf):
        # Old monitor / archive feed effect
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(scan, (255, 255, 255, 10), (0, y), (SCREEN_W, y))

        # Occasional red corrupted line
        if self.glitch_timer > 0:
            for _ in range(5):
                y = random.randint(0, SCREEN_H)
                pygame.draw.rect(scan, (180, 0, 40, 35), (0, y, SCREEN_W, random.randint(2, 5)))

        surf.blit(scan, (0, 0))

    def _draw_main_panel(self, surf):
        # Main glass panel
        panel = pygame.Surface((SCREEN_W - 120, 330), pygame.SRCALPHA)
        panel.fill((5, 10, 22, 220))

        px = 60
        py = 165

        surf.blit(panel, (px, py))

        pygame.draw.rect(surf, (75, 95, 130), (px, py, SCREEN_W - 120, 330), 2, border_radius=8)
        pygame.draw.rect(surf, (20, 30, 48), (px + 8, py + 8, SCREEN_W - 136, 314), 1, border_radius=6)

        # Left red warning strip
        strip_col = (150, 20, 35) if self.t % 40 < 25 else (80, 10, 20)
        pygame.draw.rect(surf, strip_col, (px, py, 6, 330), border_radius=3)

        # Tiny corner screws
        for sx, sy in [
            (px + 16, py + 16),
            (px + SCREEN_W - 136, py + 16),
            (px + 16, py + 314),
            (px + SCREEN_W - 136, py + 314),
        ]:
            pygame.draw.circle(surf, (90, 105, 130), (sx, sy), 3)

    def _draw_header(self, surf):
        # Top archive bar
        pygame.draw.rect(surf, (4, 8, 18), (0, 0, SCREEN_W, 82))
        pygame.draw.line(surf, (70, 90, 120), (0, 82), (SCREEN_W, 82), 2)

        # Glitched title layers
        title = self.title
        tx = SCREEN_W // 2 + self.glitch_offset

        if self.glitch_timer > 0:
            self._render_text(surf, title, self.font_title, (220, 0, 60), tx - 4, 36, 160, center=True)
            self._render_text(surf, title, self.font_title, (0, 210, 255), tx + 4, 36, 160, center=True)

        self._render_text(surf, title, self.font_title, (230, 235, 230), tx, 36, 255, center=True)

        # Archive metadata
        left = "ERROR 1969 // BLACKBOX PLAYBACK"
        right = f"LOG {self.line_index + 1:02d}/{max(1, len(self.lines)):02d}"

        self._render_text(surf, left, self.font_small, (95, 120, 145), 18, 58)
        self._render_text(surf, right, self.font_small, (95, 120, 145), SCREEN_W - 150, 58)

    def _draw_story_text(self, surf):
        current_line = self._current_line()
        visible_text = current_line[:self.char_index]

        x = 105
        y = 220
        max_width = SCREEN_W - 210

        # Speaker tag
        tag_rect = pygame.Rect(x, y - 38, 245, 28)
        pygame.draw.rect(surf, (20, 28, 45), tag_rect, border_radius=6)
        pygame.draw.rect(surf, (90, 115, 145), tag_rect, 1, border_radius=6)
        self._render_text(surf, self.speaker, self.font_speaker, (180, 200, 215), x + 12, y - 32)

        # Small warning icon / red blinking square
        if self.t % 50 < 30:
            pygame.draw.rect(surf, (180, 30, 45), (x + 222, y - 30, 9, 9))

        wrapped = self._wrap_text(visible_text, self.font_body, max_width)

        line_y = y + 18
        for line in wrapped:
            # soft shadow
            self._render_text(surf, line, self.font_body, (0, 0, 0), x + 2, line_y + 2, 180)
            self._render_text(surf, line, self.font_body, (225, 230, 220), x, line_y, 255)
            line_y += 38

        # Typewriter cursor
        if not self.full_line_visible or self.t % 40 < 20:
            cursor_x = x + self.font_body.size(wrapped[-1] if wrapped else "")[0] + 4
            cursor_y = line_y - 32
            pygame.draw.rect(surf, (220, 40, 60), (cursor_x, cursor_y, 10, 24))

    def _draw_footer_prompt(self, surf):
        # Bottom controls panel
        pygame.draw.rect(surf, (4, 8, 18), (0, SCREEN_H - 58, SCREEN_W, 58))
        pygame.draw.line(surf, (70, 90, 120), (0, SCREEN_H - 58), (SCREEN_W, SCREEN_H - 58), 2)

        if self.full_line_visible:
            if self.t % 60 < 40:
                prompt = "PRESS SPACE TO CONTINUE"
                colour = (220, 220, 180)
            else:
                prompt = ""
                colour = (220, 220, 180)
        else:
            prompt = "TRANSMISSION DECODING..."
            colour = (100, 140, 160)

        self._render_text(surf, prompt, self.font_hint, colour, SCREEN_W // 2, SCREEN_H - 30, 255, center=True)
        self._render_text(surf, "ARCHIVE SIGNAL UNSTABLE", self.font_small, (85, 95, 115), 18, SCREEN_H - 32)

        # Skip button
        mouse_pos = pygame.mouse.get_pos()
        hover = self.skip_rect.collidepoint(mouse_pos)

        btn_col = (45, 15, 25) if not hover else (85, 25, 40)
        border_col = (140, 45, 65) if not hover else (220, 70, 90)
        text_col = (170, 110, 120) if not hover else (255, 190, 200)

        pygame.draw.rect(surf, btn_col, self.skip_rect, border_radius=8)
        pygame.draw.rect(surf, border_col, self.skip_rect, 1, border_radius=8)

        self._render_text(
            surf,
            "SKIP",
            self.font_hint,
            text_col,
            self.skip_rect.centerx,
            self.skip_rect.centery + 1,
            255,
            center=True
        )

    def _draw_glitch_overlay(self, surf):
        if self.glitch_timer <= 0:
            return

        # Horizontal glitch bars
        for _ in range(6):
            y = random.randint(90, SCREEN_H - 90)
            h = random.randint(2, 8)
            x = random.randint(-30, 80)
            w = random.randint(200, SCREEN_W)
            col = random.choice([
                (180, 0, 50, 45),
                (0, 180, 220, 35),
                (255, 255, 255, 25),
            ])
            pygame.draw.rect(surf, col, (x, y, w, h))

        # Corrupted text fragments
        fragments = ["SIGNAL LOST", "DO NOT LOOK", "LUNAR ENTITY", "DATA CORRUPTED", "1969"]
        for _ in range(2):
            frag = random.choice(fragments)
            x = random.randint(40, SCREEN_W - 180)
            y = random.randint(95, SCREEN_H - 100)
            self._render_text(surf, frag, self.font_small, (180, 30, 45), x, y, 90)

    def _draw_fade(self, surf):
        if self.fade_in >= 255:
            return

        fade = pygame.Surface((SCREEN_W, SCREEN_H))
        fade.fill(BLACK)
        fade.set_alpha(255 - self.fade_in)
        surf.blit(fade, (0, 0))

# ─────────────────────────────────────────────
#  TITLE SCREEN
# ─────────────────────────────────────────────
class TitleScreen:
    def __init__(self):
        self.t = 0
        self.done = False
        self.glitch_timer = 0
        self.glitch_offset = 0

        self.starting = False
        self.start_timer = 0

        self.bg = pygame.image.load("assets/images/MENU.png").convert()
        self.bg = pygame.transform.scale(self.bg, (SCREEN_W, SCREEN_H))

        play_music("assets/audio/TITLEMUSIC.mp3", loops=-1, volume=0.5)

    def handle_event(self, event):
        if self.starting:
            return

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.starting = True
            self.start_timer = 40
            stop_music(fade_ms=600)

    def update(self):
        self.t += 1

        if self.starting:
            self.start_timer -= 1
            if self.start_timer <= 0:
                self.done = True

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
        blink = int(self.t * 0.045)
        if blink:
            start_text = "▶ PRESS SPACE TO START ◀"

            # Text position
            text_x = SCREEN_W // 2
            text_y = 430

            # Render text first so we can size the panel properly
            text_surface = font_med.render(start_text, True, (245, 240, 220))
            text_rect = text_surface.get_rect(center=(text_x, text_y))

            # Background panel behind text
            panel_rect = text_rect.inflate(44, 24)

            panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 165))  # dark transparent overlay
            surf.blit(panel, panel_rect.topleft)

            # Border glow
            pygame.draw.rect(
                surf,
                (160, 40, 55),
                panel_rect,
                2,
                border_radius=10
            )

            # Thick shadow / outline effect
            shadow_colour = (0, 0, 0)

            for ox, oy in [
                (-3, 0), (3, 0), (0, -3), (0, 3),
                (-2, -2), (2, -2), (-2, 2), (2, 2)
            ]:
                shadow = font_med.render(start_text, True, shadow_colour)
                shadow_rect = shadow.get_rect(center=(text_x + ox, text_y + oy))
                surf.blit(shadow, shadow_rect)

            # Main text
            surf.blit(text_surface, text_rect)

        draw_text(
            surf,
            "GROUP 26 // APD2F2509CSAI",
            font_tiny,
            (80, 80, 95),
            SCREEN_W // 2,
            SCREEN_H - 14
        )

# ─────────────────────────────────────────────
#  GAME OVER / WIN SCREENS / DEATH CUT SCENE
# ─────────────────────────────────────────────

class DeathCutscene:
    def __init__(self):
        self.t = 0
        self.done = False

        self.font_death = pygame.font.Font(None, 54)
        self.font_small = pygame.font.Font(None, 22)

        global _gameover_sfx_channel

        play_music("assets/audio/gameovermusic.wav", loops=-1, volume=0.5)
        snd_effect = load_sound("assets/audio/gameoversoundeffect.mp3", volume=0.6)
        if snd_effect:
            _gameover_sfx_channel = snd_effect.play()

    def handle_event(self, event):
        # Optional: allow skipping after the text appears
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.t > 90:
                    self.done = True

    def update(self):
        self.t += 1

        # Auto-finish after around 4 seconds
        if self.t > 240:
            self.done = True

    def _render_text(self, surf, text, font, colour, x, y, alpha=255):
        img = font.render(str(text), True, colour)
        img.set_alpha(alpha)
        rect = img.get_rect(center=(x, y))
        surf.blit(img, rect)

    def draw(self, surf):
        surf.fill((0, 0, 0))

        # Fade text in
        if self.t < 60:
            alpha = int(255 * (self.t / 60))
        elif self.t < 180:
            alpha = 255
        else:
            alpha = int(255 * max(0, 1 - ((self.t - 180) / 60)))

        # Slight unsettling flicker
        flicker = 0
        if self.t % 17 < 2:
            flicker = random.randint(-2, 2)

        self._render_text(
            surf,
            "YOUR SUIT IS NOW YOUR COFFIN",
            self.font_death,
            (210, 210, 210),
            SCREEN_W // 2 + flicker,
            SCREEN_H // 2,
            alpha
        )

        # Small hint after a while
        if self.t > 100 and self.t % 80 < 50:
            self._render_text(
                surf,
                "PRESS SPACE TO CONTINUE",
                self.font_small,
                (90, 90, 90),
                SCREEN_W // 2,
                SCREEN_H // 2 + 58,
                min(180, alpha)
            )

class GameOverScreen:
    def __init__(self, win=False):
        self.win = win
        self.t = 0
        self.done = False

        # Used by game.py to know what the player selected
        self.choice = None  # "retry" or "menu"

        self.glitch_timer = 0
        self.fade_in = 0

        self.font_big = pygame.font.Font(None, 86)
        self.font_title2 = pygame.font.Font(None, 52)
        self.font_med2 = pygame.font.Font(None, 32)
        self.font_small2 = pygame.font.Font(None, 22)
        self.font_tiny2 = pygame.font.Font(None, 16)

        self._winning_channel = None

        if self.win:
            snd = load_sound("assets/audio/WinningScreen.ogg", volume=0.5)
            if snd:
                self._winning_channel = snd.play(loops=-1)

    def _stop_winning_music(self):
        if self._winning_channel is not None:
            self._winning_channel.stop()
            self._winning_channel = None

    def _stop_gameover_sfx(self):
        global _gameover_sfx_channel
        if _gameover_sfx_channel is not None:
            _gameover_sfx_channel.stop()
            _gameover_sfx_channel = None

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        # Retry
        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
            self.choice = "retry"
            self.done = True
            self._stop_winning_music()
            if not self.win:
                stop_music(fade_ms=300)
                self._stop_gameover_sfx()

        # Back to menu
        elif event.key == pygame.K_m:
            self.choice = "menu"
            self.done = True
            self._stop_winning_music()
            if not self.win:
                stop_music(fade_ms=300)
                self._stop_gameover_sfx()

    def update(self):
        self.t += 1
        self.fade_in = min(255, self.fade_in + 5)

        if random.random() < 0.04:
            self.glitch_timer = random.randint(3, 8)

        if self.glitch_timer > 0:
            self.glitch_timer -= 1

    def _render_text(self, surf, text, font, colour, x, y, alpha=255, center=True):
        img = font.render(str(text), True, colour)
        img.set_alpha(alpha)
        rect = img.get_rect()

        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)

        surf.blit(img, rect)

    def draw(self, surf):
        if self.win:
            self._draw_win_screen(surf)
        else:
            self._draw_lose_screen(surf)

        self._draw_fade(surf)

    def _draw_lose_screen(self, surf):
        # Background
        surf.fill((2, 2, 8))

        # Dead-space stars
        rng = random.Random(1969)
        for i in range(130):
            x = rng.randint(0, SCREEN_W)
            y = rng.randint(0, SCREEN_H)
            flicker = int(40 + 30 * math.sin(self.t * 0.03 + i))
            shade = clamp(rng.randint(45, 120) + flicker, 25, 160)
            pygame.draw.circle(surf, (shade, shade, shade), (x, y), rng.choice([1, 1, 2]))

        # Gloomy red/purple glow
        glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.circle(glow, (110, 0, 25, 55), (SCREEN_W // 2, SCREEN_H // 2), 280)
        pygame.draw.circle(glow, (55, 0, 90, 38), (SCREEN_W // 2, SCREEN_H // 2 + 80), 220)
        surf.blit(glow, (0, 0))

        # Dark vignette
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for r in range(560, 120, -40):
            alpha = int((560 - r) * 0.30)
            pygame.draw.circle(vignette, (0, 0, 0, alpha), (SCREEN_W // 2, SCREEN_H // 2), r, 24)
        surf.blit(vignette, (0, 0))

        # Huge faded eye/signal shape in background
        eye_alpha = 70 + int(20 * math.sin(self.t * 0.04))
        eye = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.ellipse(
            eye,
            (100, 0, 30, eye_alpha),
            (SCREEN_W // 2 - 190, 115, 380, 150),
            3
        )
        pygame.draw.circle(eye, (35, 0, 10, eye_alpha), (SCREEN_W // 2, 190), 42)
        pygame.draw.circle(eye, (160, 20, 40, eye_alpha), (SCREEN_W // 2, 190), 18)
        surf.blit(eye, (0, 0))

        # Main panel
        panel = pygame.Surface((SCREEN_W - 130, 310), pygame.SRCALPHA)
        panel.fill((5, 8, 18, 220))
        px = 65
        py = 180
        surf.blit(panel, (px, py))

        pygame.draw.rect(surf, (80, 40, 55), (px, py, SCREEN_W - 130, 310), 2, border_radius=10)
        pygame.draw.rect(surf, (25, 15, 25), (px + 8, py + 8, SCREEN_W - 146, 294), 1, border_radius=8)

        # Glitch title only, not full-screen chaos
        title_x = SCREEN_W // 2
        title_y = 145

        if self.glitch_timer > 0:
            self._render_text(surf, "SIGNAL LOST", self.font_big, (255, 0, 60), title_x - 5, title_y, 150)
            self._render_text(surf, "SIGNAL LOST", self.font_big, (0, 210, 255), title_x + 5, title_y, 130)

        pulse = int(190 + 45 * math.sin(self.t * 0.06))
        self._render_text(surf, "SIGNAL LOST", self.font_big, (pulse, 25, 35), title_x, title_y)

        # Horror message
        self._render_text(
            surf,
            "YOUR SUIT STOPPED RESPONDING",
            self.font_med2,
            (210, 210, 210),
            SCREEN_W // 2,
            235
        )

        self._render_text(
            surf,
            "The archive recovered only fragments of your final transmission.",
            self.font_small2,
            (135, 145, 160),
            SCREEN_W // 2,
            278
        )

        # Broken transmission lines
        broken_lines = [
            "OXYGEN STATUS  : UNKNOWN",
            "HEARTBEAT      : LOST",
            "ENTITY SIGNAL  : STILL NEAR",
            "MISSION RESULT : FAILED"
        ]

        start_y = 325
        for i, line in enumerate(broken_lines):
            col = (120, 135, 150)
            if i == 2 and self.t % 60 < 35:
                col = (190, 40, 60)

            self._render_text(
                surf,
                line,
                self.font_small2,
                col,
                SCREEN_W // 2,
                start_y + i * 28
            )

        # Bottom action buttons
        self._draw_action_buttons(surf)

        # Scanlines
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(scan, (255, 255, 255, 8), (0, y), (SCREEN_W, y))
        surf.blit(scan, (0, 0))

    def _draw_action_buttons(self, surf):
        blink = self.t % 70 < 50

        # Retry button
        retry_rect = pygame.Rect(SCREEN_W // 2 - 230, 515, 205, 42)
        menu_rect = pygame.Rect(SCREEN_W // 2 + 25, 515, 205, 42)

        pygame.draw.rect(surf, (35, 12, 18), retry_rect, border_radius=9)
        pygame.draw.rect(surf, (165, 50, 65), retry_rect, 2, border_radius=9)

        pygame.draw.rect(surf, (12, 18, 32), menu_rect, border_radius=9)
        pygame.draw.rect(surf, (75, 100, 135), menu_rect, 2, border_radius=9)

        if blink:
            self._render_text(
                surf,
                "SPACE TO RETRY",
                self.font_small2,
                (255, 210, 210),
                retry_rect.centerx,
                retry_rect.centery
            )

            self._render_text(
                surf,
                "M FOR MAIN MENU",
                self.font_small2,
                (205, 220, 240),
                menu_rect.centerx,
                menu_rect.centery
            )

        self._render_text(
            surf,
            "ERROR 1969 // BLACKBOX TERMINATED",
            self.font_tiny2,
            (85, 90, 105),
            SCREEN_W // 2,
            SCREEN_H - 18
        )

    def _draw_win_screen(self, surf):
        # ─────────────────────────────────────────────
        # CORRUPTED VICTORY SCREEN
        # ─────────────────────────────────────────────

        surf.fill((1, 2, 8))

        # Star field
        rng = random.Random(1969)
        for i in range(160):
            x = rng.randint(0, SCREEN_W)
            y = rng.randint(0, SCREEN_H)
            flicker = int(40 + 25 * math.sin(self.t * 0.025 + i))
            shade = clamp(rng.randint(90, 180) + flicker, 60, 230)
            size = rng.choice([1, 1, 1, 2])
            pygame.draw.rect(surf, (shade, shade, shade), (x, y, size, size))

        # Slow red infection vignette
        red_alpha = clamp(int(self.t * 0.35), 0, 115)
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        for r in range(620, 80, -35):
            alpha = int((620 - r) * 0.22)
            pygame.draw.circle(
                vignette,
                (70, 0, 8, min(red_alpha, alpha)),
                (SCREEN_W // 2, SCREEN_H // 2),
                r,
                30
            )

        surf.blit(vignette, (0, 0))

        # Occasional full-screen glitch strips
        if self.t % 95 < 7:
            for _ in range(8):
                y = random.randint(40, SCREEN_H - 90)
                h = random.randint(2, 8)
                x_off = random.randint(-25, 25)

                strip = pygame.Surface((SCREEN_W, h), pygame.SRCALPHA)
                strip.fill(random.choice([
                    (255, 40, 40, 45),
                    (0, 220, 220, 35),
                    (255, 255, 255, 25),
                ]))
                surf.blit(strip, (x_off, y))

        # Small warning top corner
        warn_col = (255, 40, 35) if self.t % 40 < 22 else (90, 10, 10)
        self._render_text(
            surf,
            "[ SYSTEMS CORRUPTED ]",
            self.font_tiny2,
            warn_col,
            20,
            22,
            center=False
        )

        # Corrupted rocket icon top-right
        self._draw_corrupted_rocket_icon(surf, SCREEN_W - 70, 58)

        # Main title bait-and-switch
        glitching = self.t > 120 and self.t % 110 < 24

        if glitching:
            title = "MIS SION  C OMPROMISED"
            title_col = (255, 45, 35)

            # Chromatic glitch shadows
            self._render_text(
                surf,
                title,
                self.font_big,
                (0, 210, 220),
                SCREEN_W // 2 - 4,
                170,
                alpha=120
            )
            self._render_text(
                surf,
                title,
                self.font_big,
                (255, 0, 50),
                SCREEN_W // 2 + 5,
                170,
                alpha=160
            )

        else:
            title = "MISSION COMPLETE"
            title_col = (190, 195, 105)

        self._render_text(
            surf,
            title,
            self.font_big,
            title_col,
            SCREEN_W // 2,
            170
        )

        # Subtitle changes after a short delay
        if self.t < 150:
            subtitle = "YOU MADE IT HOME"
            subtitle_col = (255, 220, 0)
        else:
            subtitle = "YOU THINK YOU MADE IT HOME"
            subtitle_col = (230, 70, 55)

        self._render_text(
            surf,
            subtitle,
            self.font_title2,
            subtitle_col,
            SCREEN_W // 2,
            250
        )

        # Horror flavor text
        flavor_lines = [
            "The moon is quiet again.",
            "It followed you.",
        ]

        if self.t > 220:
            flavor_lines = [
                "Vitals normal.",
                "Unknown organism detected in hull.",
            ]

        self._render_text(
            surf,
            flavor_lines[0],
            self.font_med2,
            (150, 50, 45),
            SCREEN_W // 2,
            320
        )

        self._render_text(
            surf,
            flavor_lines[1],
            self.font_med2,
            (210, 45, 40) if self.t % 50 < 30 else (90, 20, 20),
            SCREEN_W // 2,
            350
        )

        # Buttons
        self._draw_corrupted_action_buttons(surf)

        # Bottom ticker
        self._draw_blackbox_ticker(surf)

        # CRT scanlines
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(scan, (255, 255, 255, 9), (0, y), (SCREEN_W, y))
        surf.blit(scan, (0, 0))

    def _draw_blackbox_ticker(self, surf):
        ticker_h = 26
        y = SCREEN_H - ticker_h

        pygame.draw.rect(surf, (5, 0, 3), (0, y, SCREEN_W, ticker_h))
        pygame.draw.line(surf, (120, 20, 18), (0, y), (SCREEN_W, y), 1)

        ticker_text = (
            "ERROR 1969 // BLACK BOX TERMINATED // INFESTATION DETECTED // "
            "BIOMASS OVERRIDE // RETURN VECTOR COMPROMISED // "
        )

        text_img = self.font_tiny2.render(ticker_text, True, (220, 55, 35))
        text_w = text_img.get_width()

        scroll_x = -((self.t * 2) % text_w)

        for i in range(-1, SCREEN_W // text_w + 3):
            surf.blit(text_img, (scroll_x + i * text_w, y + 7))


    def _draw_corrupted_action_buttons(self, surf):
        retry_rect = pygame.Rect(SCREEN_W // 2 - 235, 485, 205, 42)
        menu_rect = pygame.Rect(SCREEN_W // 2 + 30, 485, 205, 42)

        mouse_pos = pygame.mouse.get_pos()

        for rect, label, base_col, border_col in [
            (retry_rect, "SPACE TO RETRY", (25, 8, 10), (180, 45, 55)),
            (menu_rect, "M FOR MAIN MENU", (8, 14, 25), (85, 120, 160)),
        ]:
            hover = rect.collidepoint(mouse_pos)

            fill = (
                min(base_col[0] + 25, 255),
                min(base_col[1] + 12, 255),
                min(base_col[2] + 12, 255),
            ) if hover else base_col

            # Sharp pixel rectangle, no rounded corners
            pygame.draw.rect(surf, fill, rect)
            pygame.draw.rect(surf, border_col, rect, 2)

            # Inner pixel border
            pygame.draw.rect(surf, (0, 0, 0), rect.inflate(-8, -8), 1)

            # Tiny glitch line on hover
            if hover and self.t % 16 < 8:
                pygame.draw.line(
                    surf,
                    (255, 80, 80),
                    (rect.x + 8, rect.y + random.randint(8, rect.h - 8)),
                    (rect.right - 8, rect.y + random.randint(8, rect.h - 8)),
                    1
                )

            self._render_text(
                surf,
                label,
                self.font_small2,
                (235, 210, 210),
                rect.centerx,
                rect.centery
            )


    def _draw_corrupted_rocket_icon(self, surf, x, y):
        # Pixel-style small rocket
        body_col = (220, 220, 210)
        flame_col = (255, 90, 25)
        corrupt_col = (120, 0, 80)

        # Rocket body
        points = [
            (x, y - 34),
            (x - 16, y + 20),
            (x, y + 10),
            (x + 16, y + 20),
        ]
        pygame.draw.polygon(surf, body_col, points)
        pygame.draw.polygon(surf, (40, 40, 45), points, 2)

        # Window
        pygame.draw.circle(surf, (0, 220, 220), (x, y - 8), 7)

        # Flame
        pygame.draw.polygon(
            surf,
            flame_col,
            [(x - 7, y + 18), (x, y + 34), (x + 7, y + 18)]
        )

        # Corruption pixels / tendrils
        for i in range(7):
            ox = random.randint(-22, 20)
            oy = random.randint(-28, 18)
            pygame.draw.rect(
                surf,
                corrupt_col,
                (x + ox, y + oy, random.randint(2, 4), random.randint(2, 4))
            )

        # Small tendril lines
        if self.t % 20 < 12:
            pygame.draw.line(surf, corrupt_col, (x - 10, y + 4), (x - 28, y + 18), 2)
            pygame.draw.line(surf, corrupt_col, (x + 8, y - 2), (x + 25, y - 14), 2)

    def _draw_fade(self, surf):
        if self.fade_in >= 255:
            return

        fade = pygame.Surface((SCREEN_W, SCREEN_H))
        fade.fill(BLACK)
        fade.set_alpha(255 - self.fade_in)
        surf.blit(fade, (0, 0))

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
