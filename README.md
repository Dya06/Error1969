# ERROR 1969 - Clean Folder Version

This is the refactored folder version of the original one-file Pygame project.

## Run

```bash
python main.py
```

## Main structure

- `main.py` - starts pygame and launches the game
- `game.py` - main state machine and scene switching
- `settings.py` - screen size, FPS, colours, fonts
- `utils.py` - helper functions for text, HP bars, clamping, stars
- `core/particles.py` - shared particle system
- `graphics/sprites.py` - code-drawn pixel sprites and backgrounds
- `levels/level1_maze.py` - moon maze level
- `levels/level2_ship.py` - ship repair level
- `levels/level3_boss.py` - final boss level
- `scenes/screens.py` - title, text/cutscene, game over, transition screens
- `scenes/cutscene_visuals.py` - cutscene drawing callbacks
- `data/dialogue.py` - all dialogue text
- `assets/` - place future image, sound, and font files here
