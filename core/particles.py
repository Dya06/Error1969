"""Simple particle system used by all scenes."""

import pygame
import random
import math

class Particle:
    def __init__(self, x, y, vx, vy, colour, life, size=3):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.colour = colour
        self.life = self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        r = max(1, int(self.size * self.life / self.max_life))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        c = (*self.colour, alpha)
        pygame.draw.circle(s, c, (r, r), r)
        surf.blit(s, (int(self.x) - r, int(self.y) - r))

particles = []

def spawn_particles(x, y, colour, count=8, speed=3, life=30, size=3):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(0.5, speed)
        particles.append(Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd - 1,
                                  colour, life + random.randint(-10, 10), size))

def update_particles(surf):
    for p in particles[:]:
        p.update()
        p.draw(surf)
        if p.life <= 0:
            particles.remove(p)