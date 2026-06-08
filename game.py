"""Main game state machine for ERROR 1969."""

import pygame
import sys
import random

from settings import *
from scenes.screens import TextScene, TitleScreen, GameOverScreen, Transition, DeathCutscene
from scenes.cutscene_visuals import (
    intro_draw,
    cutscene1_draw,
    repair_intro_draw,
    boss_intro_draw,
    win_fly_draw,
)
from levels.level1_new import Level1
from levels.level2_ship import Level2
from levels.level3_boss import Level3
from data.dialogue import *

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()


STATE_TITLE = "title"
STATE_INTRO = "intro"
STATE_CUTSCENE1 = "cutscene1"
STATE_LEVEL1 = "level1"
STATE_CUTSCENE2 = "cutscene2"
STATE_LEVEL2 = "level2"
STATE_CUTSCENE3 = "cutscene3"
STATE_LEVEL3 = "level3"
STATE_WIN_SCENE = "win_scene"
STATE_WIN = "win"
STATE_DEATH_CUTSCENE = "death_cutscene"
STATE_GAMEOVER = "gameover"
STATE_TRANSITION = "transition"


DEBUG_START_STATE = STATE_LEVEL2




# CUTSCENE TEXT
INTRO_LINES = [
    "JULY 20, 1969.",
    "HUMANITY HAS REACHED THE MOON. BUT NOT ALL GOES AS PLANNED...",
    "MISSION LOG — ASTRONAUT CALLSIGN: ERROR.",
    "WE WERE SUPPOSED TO LAND IN THE SEA OF TRANQUILITY.",
    "SOMETHING INTERFERED WITH OUR GUIDANCE SYSTEMS.",
    "TRANSMISSION FROM MISSION CONTROL: '...UNABLE TO CONFIRM LANDING SITE...'",
    "THE LAST THING I REMEMBER IS THE SHIP SHAKING VIOLENTLY...",
    "THEN... SILENCE.",
]

CUTSCENE1_LINES = [
    "...",
    "I'M AWAKE. BUT WHERE AM I?",
    "THE VIEW IS WRONG. TOO DARK. TOO QUIET.",
    "*SUIT DIAGNOSTIC: OXYGEN — 94%  |  STRUCTURAL INTEGRITY — CRITICAL*",
    "THE SHIP... SHE'S COMPLETELY WRECKED.",
    "HULL BREACH IN SECTIONS 3, 5, AND 7.",
    "WAIT — I CAN SEE THE SHIP PARTS SCATTERED OUT THERE ON THE SURFACE!",
    "FUEL CELL... ENGINE COMPONENTS... THEY'RE ALL OUT THERE.",
    "IF I CAN COLLECT THEM ALL, I MIGHT BE ABLE TO MAKE REPAIRS.",
    "BUT WHAT IS THAT THING IN THE SHADOWS?",
    "SOMETHING IS WATCHING ME...",
    "I HAVE TO MOVE. NOW.",
    "TASK: COLLECT ALL 5 SHIP PARTS TO PROCEED —",
    "HOW TO PLAY - WASD TO MOVE",
]

CUTSCENE2_LINES = [
    "I FOUND ALL THE PARTS. SOMEHOW.",
    "THAT WATCHER — IT CHASED ME THE WHOLE TIME.",
    "BUT I MADE IT BACK TO THE SHIP.",
    "*SUIT DIAGNOSTIC: OXYGEN — 61%  |  STRUCTURAL INTEGRITY — CRITICAL*",
    "NOW COMES THE HARD PART. I NEED TO FIX ALL THE SYSTEMS.",
    "FUEL CELL, NAVIGATION, ENGINE, COMMUNICATIONS, LIFE SUPPORT.",
    "BUT THERE'S SOMETHING ELSE IN HERE. SOMETHING BIGGER.",
    "IT LOOKS LIKE... A FAILED EXPERIMENT? HALF MAN, HALF MACHINE.",
    "IT'S TRYING TO STOP ME FROM REPAIRING THE SHIP.",
    "I WON'T LET IT.",
    "MAY GOD BE WITH ME",
    "TASK: REPAIR ALL SHIP SYSTEMS TO PROCEED —",
    "HOW TO PLAY - WASD TO MOVE, PRESS E TO FIX",
]

CUTSCENE3_LINES = [
    "THE SHIP IS REPAIRED. SYSTEMS ONLINE.",
    "PREPARING FOR EMERGENCY LAUNCH...",
    "*LAUNCH SEQUENCE: INITIATED*",
    "WAIT.",
    "SOMETHING IS OUTSIDE.",
    "SOMETHING ENORMOUS.",
    "IT'S DEVOURING THE MOON ITSELF.",
    "THE MOON EATER.",
    "IT'S BLOCKING MY ESCAPE ROUTE.",
    "IF I CAN'T GET PAST IT, I'LL NEVER MAKE IT HOME.",
    "THIS ENDS HERE.",
    "TASK: DESTROY THE MOON EATER TO ESCAPE —",
    "HOW TO PLAY - WASD TO MOVE",
    "SPACE TO JUMP",
    "J TO SHOOT AND R TO BOOST SHOOT",
]

WIN_LINES = [
    "THE MOON EATER IS DEFEATED.",
    "THE MOON IS SILENT ONCE MORE.",
    "EMERGENCY LAUNCH — SUCCESSFUL.",
    "RISING THROUGH THE LUNAR ATMOSPHERE...",
    "MISSION CONTROL: '...WE'RE READING A SIGNAL! APOLLO 11 IS THAT YOU?!'",
    "ME: 'I'M COMING HOME.'",
    "MISSION CONTROL: '...WE NEVER STOPPED BELIEVING.'",
    "JULY 21, 1969 — ASTRONAUT NEIL, MISSION COMPLETE.",
    "APOLLO 11 — OVERCOME.",
]


# ─────────────────────────────────────────────
# MAIN GAME
# ─────────────────────────────────────────────

def main():
    state = None
    scene = None
    next_state = None
    transition = None

    last_level_state = STATE_LEVEL1
    death_started = False

    def start_state(s):
        nonlocal state, scene, death_started

        state = s
        death_started = False

        if s == STATE_TITLE:
            scene = TitleScreen()

        elif s == STATE_INTRO:
            scene = TextScene(
                INTRO_LINES,
                title="ERROR 1969",
                speaker="BLACKBOX PLAYBACK",
                music_path="assets/audio/1stDialogue.wav",
                stop_music_on_finish=False
            )

        elif s == STATE_CUTSCENE1:
            scene = TextScene(
                CUTSCENE1_LINES,
                title="CRASH LANDING",
                speaker="SUIT DIAGNOSTIC",
                stop_music_on_finish=True
            )

        elif s == STATE_LEVEL1:
            scene = Level1()

        elif s == STATE_CUTSCENE2:
            scene = TextScene(
                CUTSCENE2_LINES,
                title="THE SHIP",
                speaker="MISSION LOG",
                music_path="assets/audio/2ndDialogue.wav"
            )

        elif s == STATE_LEVEL2:
            scene = Level2()

        elif s == STATE_CUTSCENE3:
            scene = TextScene(
                CUTSCENE3_LINES,
                title="THE MOON EATER",
                speaker="WARNING SIGNAL",
                music_path="assets/audio/3rdDialoguemusic.wav",
                line_sounds={4: "assets/audio/BossNoises.mp3"},
                line_sound_range=(0, 2, "assets/audio/3rdDialoguefiirstbeeping.mp3")
            )

        elif s == STATE_LEVEL3:
            scene = Level3()

        elif s == STATE_WIN_SCENE:
            scene = TextScene(
                WIN_LINES,
                title="VICTORY",
                speaker="MISSION CONTROL"
            )

        elif s == STATE_WIN:
            scene = GameOverScreen(win=True)

        elif s == STATE_DEATH_CUTSCENE:
            scene = DeathCutscene()

        elif s == STATE_GAMEOVER:
            scene = GameOverScreen(win=False)

        else:
            print(f"[WARNING] Unknown state: {s}. Returning to title.")
            scene = TitleScreen()
            state = STATE_TITLE

    def go_to(s):
        nonlocal state, next_state, transition

        next_state = s
        transition = Transition(fade_in=False, duration=35)
        state = STATE_TRANSITION

    # Start game
    start_state(DEBUG_START_STATE)

    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif state != STATE_TRANSITION and scene is not None:
                scene.handle_event(event)

        if not running:
            break

        # ── UPDATE + DRAW ───────────────────────────
        if state == STATE_TRANSITION:
            # Draw previous scene behind the fade.
            if scene is not None:
                scene.draw(screen)
            else:
                screen.fill(BLACK)

            transition.update()
            transition.draw(screen)

            if transition.done:
                start_state(next_state)
                transition = None

        else:
            scene.update()
            scene.draw(screen)

            # ─────────────────────────────────────────
            # STATE TRANSITIONS
            # ─────────────────────────────────────────

            if state == STATE_TITLE and scene.done:
                go_to(STATE_INTRO)

            elif state == STATE_INTRO and scene.done:
                go_to(STATE_CUTSCENE1)

            elif state == STATE_CUTSCENE1 and scene.done:
                last_level_state = STATE_LEVEL1
                go_to(STATE_LEVEL1)

            elif state == STATE_LEVEL1:
                if scene.lose and not death_started:
                    death_started = True
                    go_to(STATE_DEATH_CUTSCENE)

                elif scene.done and getattr(scene, "flash_timer", 0) <= 0:
                    go_to(STATE_CUTSCENE2)

            elif state == STATE_CUTSCENE2 and scene.done:
                last_level_state = STATE_LEVEL2
                go_to(STATE_LEVEL2)

            elif state == STATE_LEVEL2:
                if scene.lose and not death_started:
                    death_started = True
                    go_to(STATE_DEATH_CUTSCENE)

                elif scene.done:
                    go_to(STATE_CUTSCENE3)

            elif state == STATE_CUTSCENE3 and scene.done:
                last_level_state = STATE_LEVEL3
                go_to(STATE_LEVEL3)

            elif state == STATE_LEVEL3:
                if scene.lose and not death_started:
                    death_started = True
                    go_to(STATE_DEATH_CUTSCENE)

                elif scene.done:
                    go_to(STATE_WIN)

            elif state == STATE_DEATH_CUTSCENE and scene.done:
                go_to(STATE_GAMEOVER)

            elif state == STATE_WIN_SCENE and scene.done:
                go_to(STATE_WIN)

            elif state == STATE_GAMEOVER and scene.done:
                if getattr(scene, "choice", None) == "retry":
                    go_to(last_level_state)
                else:
                    go_to(STATE_TITLE)

            elif state == STATE_WIN and scene.done:
                if getattr(scene, "choice", None) == "retry":
                    go_to(STATE_LEVEL1)
                else:
                    go_to(STATE_TITLE)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()