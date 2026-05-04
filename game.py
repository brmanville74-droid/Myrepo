"""
Crystal Quest - 2D Adventure Game Final Project
Author: Brady Manville

How to run:
    pip install pygame
    python adventure_game_upgraded.py

Controls:
    W/A/S/D or Arrow Keys = move
    SPACE = attack
    E = interact with chests, signs, portals
    P = pause
    R = restart after win/lose
    ESC = quit

Game goal:
    Clear three levels. Collect enough coins, grab power-up coins, open the
    chest to get the crystal key, then enter the portal. Every coin and power-up
    is placed on walkable tiles and the game validates reachable placement at
    the start of each level.
"""

import math
import random
import sys
from array import array
from dataclasses import dataclass
from collections import deque
from typing import Dict, List, Optional, Tuple

import pygame

WIDTH = 960
HEIGHT = 640
FPS = 60
TILE = 40
HUD_HEIGHT = 52
PLAYER_BASE_SPEED = 4.0
ENEMY_BASE_SPEED = 1.45
SWORD_RANGE = 48
MAX_HEALTH = 6
NIGHT_MODE_TIME = 30 * FPS
NIGHT_MODE_DURATION = 15 * FPS

WHITE = (245, 245, 245)
BLACK = (12, 12, 18)
GRAY = (115, 118, 130)
LIGHT_GRAY = (185, 188, 198)
DARK_GRAY = (32, 34, 44)
GREEN = (74, 176, 87)
DARK_GREEN = (24, 96, 48)
GRASS_1 = (55, 142, 68)
GRASS_2 = (63, 156, 75)
BLUE = (70, 145, 235)
DEEP_BLUE = (30, 67, 138)
WATER = (35, 94, 177)
RED = (225, 72, 72)
DARK_RED = (135, 30, 35)
GOLD = (255, 195, 45)
YELLOW = (255, 228, 89)
BROWN = (132, 86, 48)
DARK_BROWN = (76, 48, 27)
PURPLE = (155, 88, 220)
PINK = (246, 110, 190)
ORANGE = (250, 142, 48)
CYAN = (80, 230, 240)
LIME = (145, 255, 105)
MAGENTA = (255, 90, 240)

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "enemy_speed": 0.9,
        "enemy_damage_bonus": 0,
        "coin_delta": -1,
        "color": CYAN,
        "description": "Softer enemy pressure and a lower coin goal.",
    },
    "medium": {
        "label": "Medium",
        "enemy_speed": 1.0,
        "enemy_damage_bonus": 0,
        "coin_delta": 0,
        "color": GOLD,
        "description": "Balanced survival with the default coin goal.",
    },
    "hard": {
        "label": "Hard",
        "enemy_speed": 1.18,
        "enemy_damage_bonus": 1,
        "coin_delta": 1,
        "color": RED,
        "description": "Faster monsters, harder hits, and more coins required.",
    },
}
DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font, color: Tuple[int, int, int],
              x: int, y: int, center: bool = False) -> None:
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(image, rect)


def tile_center(col: int, row: int, size: int = 24) -> Tuple[int, int]:
    return col * TILE + (TILE - size) // 2, row * TILE + (TILE - size) // 2


def blend(color_a: Tuple[int, int, int], color_b: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
    amount = clamp(amount, 0.0, 1.0)
    return tuple(int(a + (b - a) * amount) for a, b in zip(color_a, color_b))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, fill: Tuple[int, int, int],
               border: Tuple[int, int, int], alpha: int = 220, radius: int = 16) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*fill, alpha), panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, (*border, min(255, alpha + 20)), panel.get_rect(), 2, border_radius=radius)
    surface.blit(panel, rect.topleft)


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    color: Tuple[int, int, int]
    timer: int = 58

    def update(self) -> None:
        self.y -= 0.75
        self.timer -= 1

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.timer > 0:
            draw_text(surface, self.text, font, self.color, int(self.x), int(self.y), True)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    size: int
    timer: int

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.timer -= 1

    def draw(self, surface: pygame.Surface) -> None:
        if self.timer > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), max(1, self.size))


@dataclass
class RingEffect:
    x: float
    y: float
    color: Tuple[int, int, int]
    radius: float = 10.0
    growth: float = 2.8
    timer: int = 16
    width: int = 3

    def update(self) -> None:
        self.radius += self.growth
        self.timer -= 1

    def draw(self, surface: pygame.Surface) -> None:
        if self.timer <= 0:
            return
        alpha = max(0, min(255, self.timer * 14))
        size = int(self.radius * 2 + 10)
        ring = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self.color, alpha), (size // 2, size // 2), int(self.radius), self.width)
        surface.blit(ring, (self.x - size // 2, self.y - size // 2))


class SoundBank:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.enabled = True
            self.sounds = {
                "menu_move": self._tone(420, 70, 0.16, "triangle"),
                "menu_select": self._tone(640, 120, 0.18, "triangle"),
                "attack": self._tone(250, 90, 0.28, "square"),
                "enemy_hit": self._tone(180, 80, 0.25, "square"),
                "coin": self._tone(760, 110, 0.16, "sine"),
                "powerup": self._tone(920, 160, 0.18, "triangle"),
                "hurt": self._tone(140, 180, 0.28, "saw"),
                "chest": self._tone(510, 170, 0.22, "triangle"),
                "key": self._tone(1080, 160, 0.14, "sine"),
                "portal": self._tone(300, 260, 0.20, "sine"),
                "night": self._tone(110, 340, 0.24, "saw"),
                "win": self._tone(880, 280, 0.18, "triangle"),
                "lose": self._tone(100, 360, 0.20, "square"),
                "hazard": self._tone(220, 120, 0.25, "saw"),
                "seismic": self._tone(72, 420, 0.35, "saw"),
            }
        except pygame.error:
            self.enabled = False

    def _wave_value(self, wave_type: str, phase: float) -> float:
        if wave_type == "square":
            return 1.0 if math.sin(phase) >= 0 else -1.0
        if wave_type == "triangle":
            cycle = (phase / math.tau) % 1.0
            return 2.0 * abs(2.0 * cycle - 1.0) - 1.0
        if wave_type == "saw":
            cycle = (phase / math.tau) % 1.0
            return 2.0 * cycle - 1.0
        return math.sin(phase)

    def _tone(self, frequency: int, duration_ms: int, volume: float, wave_type: str = "sine") -> pygame.mixer.Sound:
        sample_rate = 22050
        total_samples = int(sample_rate * duration_ms / 1000)
        buffer = array("h")
        peak = int(32767 * volume)
        for sample in range(total_samples):
            t = sample / sample_rate
            phase = math.tau * frequency * t
            envelope = (1.0 - sample / max(1, total_samples)) ** 1.6
            value = int(self._wave_value(wave_type, phase) * peak * envelope)
            buffer.append(value)
        return pygame.mixer.Sound(buffer=buffer.tobytes())

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()


@dataclass
class HazardProjectile:
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    glow: Tuple[int, int, int]
    radius: int
    timer: int
    label: str
    damage: int

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.timer -= 1

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    def draw(self, surface: pygame.Surface) -> None:
        if self.timer <= 0:
            return
        glow_size = self.radius * 6
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        alpha = max(40, min(160, self.timer * 5))
        pygame.draw.circle(glow_surface, (*self.glow, alpha), (glow_size // 2, glow_size // 2), self.radius * 2)
        surface.blit(glow_surface, (self.x - glow_size // 2, self.y - glow_size // 2))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), max(2, self.radius // 2))


LEVELS = [
    {
        "name": "Level 1 - Whispering Wilds",
        "need": 7,
        "player": (1, 1),
        "chest": (5, 10),
        "portal": (22, 13),
        "theme": {
            "style": "forest",
            "ground1": (58, 135, 76),
            "ground2": (74, 156, 88),
            "sky_day": (42, 88, 110),
            "sky_night": (12, 18, 42),
            "night_overlay": (16, 20, 46),
        },
        "map": [
            "WWWWWWWWWWWWWWWWWWWWWWWW",
            "W......................W",
            "W..TT....M.....TT......W",
            "W.......MM.............W",
            "W..MMMM......TT....MM..W",
            "W..M..M...........M....W",
            "W..M..M....WW.....M....W",
            "W..M......W..W.........W",
            "W......TT.W..W....TT...W",
            "W....TT..W.............W",
            "W..........MMM.........W",
            "W....T.....M..M...TT...W",
            "W......M...............W",
            "W..TT..M....MMMM.......W",
            "W......................W",
            "WWWWWWWWWWWWWWWWWWWWWWWW",
        ],
        "coins": [(3, 3), (7, 2), (14, 2), (20, 2), (2, 6), (8, 9), (15, 9), (20, 10), (2, 13), (11, 14)],
        "powerups": [(18, 4, "speed"), (6, 13, "heal")],
        "enemies": [(13, 5, "goblin"), (19, 7, "slime"), (8, 12, "goblin"), (16, 10, "bat"), (4, 8, "slime")],
        "signs": [(2, 4, "The wilds are gentle, but the paths twist around roots and ponds."),
                  (18, 13, "Grab the key from the mossy chest, then sprint for the portal.")],
    },
    {
        "name": "Level 2 - Sunstone Maze",
        "need": 9,
        "player": (1, 14),
        "chest": (16, 2),
        "portal": (22, 1),
        "theme": {
            "style": "desert",
            "ground1": (191, 164, 108),
            "ground2": (214, 189, 132),
            "sky_day": (138, 103, 58),
            "sky_night": (26, 18, 42),
            "night_overlay": (34, 22, 38),
        },
        "map": [
            "WWWWWWWWWWWWWWWWWWWWWWWW",
            "W......................W",
            "W..MM....TT......MM....W",
            "W..M.....TT......M.....W",
            "W..M..WW.........M.....W",
            "W.....W..W....TT.......W",
            "W...TTW..W........MM...W",
            "W.....W...........M....W",
            "W..MM.W....MMMM...M....W",
            "W.....W......M.........W",
            "W.....WWW....M....TT...W",
            "W.............M........W",
            "W..TT......WWWM........W",
            "W..MM..............TT..W",
            "W......................W",
            "WWWWWWWWWWWWWWWWWWWWWWWW",
        ],
        "coins": [(2, 13), (5, 11), (8, 9), (14, 10), (20, 11), (21, 6), (16, 4), (11, 2), (2, 2), (22, 4), (7, 14)],
        "powerups": [(12, 14, "shield"), (19, 2, "speed"), (4, 4, "heal")],
        "enemies": [(8, 6, "goblin"), (16, 7, "slime"), (20, 9, "goblin"), (12, 3, "bat"), (8, 12, "slime"), (18, 11, "bat")],
        "signs": [(2, 11, "Sunstone paths are wider, but the ruins funnel you into ambushes."),
                  (16, 1, "Use the open lanes to dodge, then dive back in for powerups.")],
    },
    {
        "name": "Level 3 - Ember Citadel",
        "need": 11,
        "player": (1, 1),
        "chest": (4, 13),
        "portal": (22, 13),
        "theme": {
            "style": "volcano",
            "ground1": (104, 62, 48),
            "ground2": (81, 39, 31),
            "sky_day": (92, 48, 32),
            "sky_night": (28, 8, 20),
            "night_overlay": (54, 12, 18),
        },
        "map": [
            "WWWWWWWWWWWWWWWWWWWWWWWW",
            "W......................W",
            "W..MMMM....TT....WW....W",
            "W..M..M...........W....W",
            "W..M..M..MMMM.....W....W",
            "W......T.M..M..TT.W....W",
            "W..WWWW..M..M.....W....W",
            "W..W.....M..M..........W",
            "W..W..TT........MMMM...W",
            "W..W......TT.....M..M..W",
            "W..W..MMMM.......M..M..W",
            "W......M..............TW",
            "W..TT..M....WWWW.......W",
            "W..M...M...........TT..W",
            "W......................W",
            "WWWWWWWWWWWWWWWWWWWWWWWW",
        ],
        "coins": [(3, 1), (8, 1), (14, 1), (20, 1), (6, 5), (11, 5), (17, 5), (2, 9), (9, 11), (15, 11), (21, 11), (7, 14), (13, 14), (19, 14)],
        "powerups": [(10, 13, "shield"), (5, 7, "speed"), (18, 9, "damage"), (2, 6, "heal")],
        "enemies": [(10, 3, "bat"), (15, 6, "goblin"), (20, 6, "slime"), (8, 12, "goblin"), (17, 13, "bat"), (5, 9, "slime"), (12, 13, "goblin")],
        "signs": [(2, 12, "This citadel burns bright. Powerups matter more than ever here."),
                  (19, 3, "Lava channels split the arena, so clear a lane before rushing.")],
    },
]


class TileMap:
    def __init__(self, map_data: List[str], theme: Optional[Dict[str, Tuple[int, int, int] | str]] = None) -> None:
        self.map_data = map_data
        self.rows = len(map_data)
        self.cols = len(map_data[0])
        self.blocked = {"W", "M", "T"}
        self.theme = theme or {}

    def is_blocked_tile(self, row: int, col: int) -> bool:
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return True
        return self.map_data[row][col] in self.blocked

    def is_walkable_tile(self, row: int, col: int) -> bool:
        return not self.is_blocked_tile(row, col)

    def rect_collides(self, rect: pygame.Rect) -> bool:
        left = rect.left // TILE
        right = (rect.right - 1) // TILE
        top = rect.top // TILE
        bottom = (rect.bottom - 1) // TILE
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                if self.is_blocked_tile(row, col):
                    return True
        return False

    def reachable_tiles(self, start_col: int, start_row: int) -> set:
        seen = set()
        queue = deque([(start_col, start_row)])
        seen.add((start_col, start_row))
        while queue:
            col, row = queue.popleft()
            for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                ncol = col + dc
                nrow = row + dr
                if (ncol, nrow) not in seen and self.is_walkable_tile(nrow, ncol):
                    seen.add((ncol, nrow))
                    queue.append((ncol, nrow))
        return seen

    def draw(self, surface: pygame.Surface) -> None:
        style = self.theme.get("style", "forest")
        ground1 = self.theme.get("ground1", GRASS_1)
        ground2 = self.theme.get("ground2", GRASS_2)
        for row_index, row in enumerate(self.map_data):
            for col_index, tile in enumerate(row):
                x = col_index * TILE
                y = row_index * TILE
                rect = pygame.Rect(x, y, TILE, TILE)
                if tile == "W" and style == "desert":
                    pygame.draw.rect(surface, (125, 92, 54), rect)
                    pygame.draw.rect(surface, (166, 128, 74), rect.inflate(-6, -6), border_radius=8)
                    pygame.draw.arc(surface, (219, 181, 111), rect.inflate(-10, -10), 0, math.pi * 1.6, 2)
                elif tile == "W" and style == "volcano":
                    pygame.draw.rect(surface, (130, 22, 8), rect)
                    pygame.draw.rect(surface, (255, 110, 26), rect.inflate(-6, -6), border_radius=9)
                    pygame.draw.line(surface, YELLOW, (x + 7, y + 12), (x + 32, y + 28), 3)
                    pygame.draw.line(surface, ORANGE, (x + 9, y + 30), (x + 30, y + 10), 2)
                elif tile == "W":
                    pygame.draw.rect(surface, WATER, rect)
                    pygame.draw.rect(surface, DEEP_BLUE, rect, 2)
                    pygame.draw.arc(surface, BLUE, rect.inflate(-8, -8), 0, math.pi, 2)
                elif tile == "M" and style == "desert":
                    pygame.draw.rect(surface, (141, 99, 58), rect)
                    pygame.draw.rect(surface, (206, 170, 111), rect.inflate(-6, -6), border_radius=6)
                    pygame.draw.line(surface, (108, 78, 44), (x + 6, y + 20), (x + 33, y + 20), 2)
                elif tile == "M" and style == "volcano":
                    pygame.draw.rect(surface, (26, 24, 36), rect)
                    pygame.draw.rect(surface, (58, 52, 74), rect.inflate(-8, -5), border_radius=8)
                    pygame.draw.line(surface, (100, 82, 118), (x + 14, y + 5), (x + 24, y + 33), 2)
                elif tile == "M":
                    pygame.draw.rect(surface, DARK_BROWN, rect)
                    pygame.draw.rect(surface, BROWN, rect.inflate(-7, -7), border_radius=8)
                    pygame.draw.line(surface, (95, 61, 35), (x + 8, y + 10), (x + 31, y + 30), 2)
                elif tile == "T" and style == "desert":
                    pygame.draw.rect(surface, ground1, rect)
                    pygame.draw.rect(surface, (46, 120, 62), (x + 18, y + 8, 5, 25), border_radius=3)
                    pygame.draw.line(surface, (61, 166, 85), (x + 20, y + 10), (x + 10, y + 16), 3)
                    pygame.draw.line(surface, (61, 166, 85), (x + 20, y + 18), (x + 31, y + 23), 3)
                elif tile == "T" and style == "volcano":
                    pygame.draw.rect(surface, ground1, rect)
                    pygame.draw.polygon(surface, (198, 80, 255), [(x + 20, y + 6), (x + 11, y + 32), (x + 18, y + 28)])
                    pygame.draw.polygon(surface, (126, 218, 255), [(x + 25, y + 10), (x + 18, y + 30), (x + 30, y + 27)])
                    pygame.draw.polygon(surface, WHITE, [(x + 20, y + 6), (x + 18, y + 13), (x + 21, y + 12)])
                elif tile == "T":
                    pygame.draw.rect(surface, ground1, rect)
                    pygame.draw.rect(surface, DARK_BROWN, (x + 16, y + 22, 8, 17), border_radius=3)
                    pygame.draw.circle(surface, DARK_GREEN, (x + 20, y + 19), 18)
                    pygame.draw.circle(surface, GREEN, (x + 14, y + 15), 10)
                    pygame.draw.circle(surface, GREEN, (x + 26, y + 15), 10)
                else:
                    base = ground1 if (row_index + col_index) % 2 == 0 else ground2
                    pygame.draw.rect(surface, base, rect)
                    if style == "desert" and (row_index * 3 + col_index) % 4 == 0:
                        pygame.draw.circle(surface, (166, 132, 86), (x + 10, y + 29), 2)
                        pygame.draw.circle(surface, (233, 213, 164), (x + 25, y + 14), 2)
                    elif style == "volcano" and (row_index * 5 + col_index) % 4 == 0:
                        pygame.draw.circle(surface, (164, 84, 44), (x + 10, y + 30), 2)
                        pygame.draw.circle(surface, (255, 132, 56), (x + 26, y + 12), 2)
                    elif (row_index * 3 + col_index) % 5 == 0:
                        pygame.draw.circle(surface, (80, 176, 86), (x + 10, y + 30), 2)
                        pygame.draw.circle(surface, (80, 176, 86), (x + 25, y + 11), 2)


class Entity:
    def __init__(self, x: int, y: int, w: int, h: int, color: Tuple[int, int, int]) -> None:
        self.rect = pygame.Rect(x, y, w, h)
        self.pos = pygame.Vector2(float(x), float(y))
        self.color = color
        self.vx = 0.0
        self.vy = 0.0
        self.health = 1
        self.alive = True

    def move_and_collide(self, tile_map: TileMap) -> None:
        self.pos.x += self.vx
        self.rect.x = int(round(self.pos.x))
        if tile_map.rect_collides(self.rect):
            if self.vx > 0:
                self.rect.right = (self.rect.right // TILE) * TILE
            elif self.vx < 0:
                self.rect.left = ((self.rect.left // TILE) + 1) * TILE
            self.pos.x = float(self.rect.x)
        self.pos.y += self.vy
        self.rect.y = int(round(self.pos.y))
        if tile_map.rect_collides(self.rect):
            if self.vy > 0:
                self.rect.bottom = (self.rect.bottom // TILE) * TILE
            elif self.vy < 0:
                self.rect.top = ((self.rect.top // TILE) + 1) * TILE
            self.pos.y = float(self.rect.y)


class Player(Entity):
    def __init__(self, col: int, row: int) -> None:
        x, y = tile_center(col, row, 30)
        super().__init__(x, y, 30, 34, BLUE)
        self.health = MAX_HEALTH
        self.coins = 0
        self.total_coins = 0
        self.has_key = False
        self.direction = pygame.Vector2(0, 1)
        self.attack_timer = 0
        self.invincible_timer = 0
        self.speed_timer = 0
        self.shield_timer = 0
        self.damage_timer = 0
        self.walk_timer = 0
        self.enemies_defeated = 0
        self.trail_timer = 0
        self.spin_angle = 0.0

    def current_speed(self) -> float:
        return PLAYER_BASE_SPEED + (1.7 if self.speed_timer > 0 else 0)

    def attack_damage(self) -> int:
        return 2 if self.damage_timer > 0 else 1

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        self.vx = 0
        self.vy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx -= self.current_speed()
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx += self.current_speed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.vy -= self.current_speed()
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.vy += self.current_speed()
        if self.vx or self.vy:
            movement = pygame.Vector2(self.vx, self.vy)
            if movement.length() > 0:
                movement = movement.normalize()
                self.vx = movement.x * self.current_speed()
                self.vy = movement.y * self.current_speed()
                self.direction = movement
                self.walk_timer += 1

    def update(self, tile_map: TileMap) -> None:
        self.move_and_collide(tile_map)
        if self.attack_timer > 0:
            self.attack_timer -= 1
            self.spin_angle += 0.55
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.speed_timer > 0:
            self.speed_timer -= 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
        if self.damage_timer > 0:
            self.damage_timer -= 1

    def attack_rect(self) -> pygame.Rect:
        cx, cy = self.rect.center
        dx = int(self.direction.x * SWORD_RANGE)
        dy = int(self.direction.y * SWORD_RANGE)
        return pygame.Rect(cx + dx - 22, cy + dy - 22, 44, 44)

    def attack_radius(self) -> int:
        return 62 if self.damage_timer > 0 else 54

    def start_attack(self) -> bool:
        if self.attack_timer == 0:
            self.attack_timer = 19 if self.damage_timer > 0 else 24
            self.spin_angle = math.atan2(self.direction.y, self.direction.x)
            return True
        return False

    def take_damage(self, amount: int) -> bool:
        if self.invincible_timer > 0:
            return False
        if self.shield_timer > 0:
            self.shield_timer = max(0, self.shield_timer - 90)
            self.invincible_timer = 45
            return True
        self.health -= amount
        self.invincible_timer = 72
        if self.health <= 0:
            self.alive = False
        return True

    def apply_powerup(self, kind: str) -> str:
        if kind == "speed":
            self.speed_timer = 520
            return "Speed boost!"
        if kind == "shield":
            self.shield_timer = 560
            return "Shield activated!"
        if kind == "damage":
            self.damage_timer = 500
            return "Sword powered up!"
        if kind == "heal":
            self.health = min(MAX_HEALTH, self.health + 2)
            return "+2 health!"
        return "Power up!"

    def draw(self, surface: pygame.Surface) -> None:
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            return
        x, y = self.rect.x, self.rect.y
        cape_offset = int(math.sin(self.walk_timer * 0.2) * 2)
        pygame.draw.ellipse(surface, (0, 0, 0), (x + 3, y + 28, 24, 10))
        pygame.draw.polygon(surface, PURPLE, [(x + 6, y + 13), (x - 6, y + 31 + cape_offset), (x + 13, y + 29)])
        pygame.draw.polygon(surface, DEEP_BLUE, [(x + 24, y + 13), (x + 36, y + 31 - cape_offset), (x + 17, y + 29)])
        pygame.draw.rect(surface, (42, 88, 210), (x + 5, y + 10, 20, 22), border_radius=8)
        pygame.draw.rect(surface, BLUE, (x + 7, y + 12, 16, 18), border_radius=6)
        pygame.draw.circle(surface, (232, 188, 138), (x + 15, y + 8), 10)
        pygame.draw.rect(surface, DARK_BROWN, (x + 5, y - 1, 20, 8), border_radius=6)
        pygame.draw.circle(surface, WHITE, (x + 11, y + 8), 2)
        pygame.draw.circle(surface, WHITE, (x + 19, y + 8), 2)
        pygame.draw.rect(surface, GOLD, (x + 10, y + 31, 4, 6), border_radius=2)
        pygame.draw.rect(surface, GOLD, (x + 17, y + 31, 4, 6), border_radius=2)
        if self.shield_timer > 0:
            pygame.draw.circle(surface, CYAN, self.rect.center, 26, 2)
        if self.attack_timer > 0:
            color = MAGENTA if self.damage_timer > 0 else YELLOW
            radius = self.attack_radius()
            for i in range(3):
                angle = self.spin_angle + i * (math.tau / 3)
                tip_x = self.rect.centerx + int(math.cos(angle) * radius)
                tip_y = self.rect.centery + int(math.sin(angle) * radius)
                pygame.draw.line(surface, color, self.rect.center, (tip_x, tip_y), 4)
                pygame.draw.circle(surface, color, (tip_x, tip_y), 7, 2)
            pygame.draw.circle(surface, color, self.rect.center, radius, 2)


class Enemy(Entity):
    def __init__(self, col: int, row: int, kind: str) -> None:
        x, y = tile_center(col, row, 30)
        color = RED if kind == "goblin" else PURPLE if kind == "bat" else LIME
        super().__init__(x, y, 30, 30, color)
        self.kind = kind
        self.health = 3 if kind == "goblin" else 2 if kind == "bat" else 1
        self.wander_timer = random.randint(20, 90)
        self.wander_dir = pygame.Vector2(random.choice([-1, 1]), random.choice([-1, 0, 1])).normalize()
        self.hit_flash = 0
        self.flap = random.randint(0, 60)
        self.powerup = random.choices(
            ["swift", "guard", "fury", "drain", None],
            weights=[2, 2, 2, 1, 5],
            k=1,
        )[0]
        self.power_timer = random.randint(150, 260)
        self.damage = 2 if self.powerup == "fury" else 1
        self.base_damage = self.damage
        if self.powerup == "guard":
            self.health += 1
        self.demon_mode = False

    def update(self, tile_map: TileMap, player: Player, level_number: int, night_mode: bool = False,
               speed_multiplier: float = 1.0) -> None:
        if not self.alive:
            return
        self.flap += 1
        speed = ENEMY_BASE_SPEED + level_number * 0.12
        if self.kind == "slime":
            speed -= 0.25
        if self.kind == "bat":
            speed += 0.45
        if self.powerup == "swift":
            speed += 0.6
        if night_mode:
            speed += 2.25
        speed *= speed_multiplier
        player_dist = distance(self.rect.center, player.rect.center)
        if night_mode or player_dist < 235:
            vec = pygame.Vector2(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            if vec.length() > 0:
                vec = vec.normalize()
                self.vx = vec.x * speed
                self.vy = vec.y * speed
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.wander_timer = random.randint(35, 120)
                self.wander_dir = pygame.Vector2(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
                if self.wander_dir.length() == 0:
                    self.wander_dir = pygame.Vector2(1, 0)
                self.wander_dir = self.wander_dir.normalize()
            self.vx = self.wander_dir.x * speed
            self.vy = self.wander_dir.y * speed
        old = self.rect.topleft
        self.move_and_collide(tile_map)
        if old == self.rect.topleft and random.random() < 0.05:
            self.wander_timer = 0
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.power_timer > 0:
            self.power_timer -= 1

    def take_damage(self, amount: int) -> bool:
        if self.powerup == "guard" and self.power_timer > 0:
            amount = max(1, amount - 1)
        self.health -= amount
        self.hit_flash = 12
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def activate_demon_mode(self) -> None:
        if self.demon_mode:
            return
        self.demon_mode = True
        self.damage = self.base_damage + 1

    def deactivate_demon_mode(self) -> None:
        self.demon_mode = False
        self.damage = self.base_damage

    def power_color(self) -> Tuple[int, int, int]:
        return {
            "swift": CYAN,
            "guard": BLUE,
            "fury": ORANGE,
            "drain": MAGENTA,
        }.get(self.powerup, LIGHT_GRAY)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        x, y = self.rect.x, self.rect.y
        base_color = blend(self.color, RED, 0.7) if self.demon_mode else self.color
        color = WHITE if self.hit_flash > 0 else base_color
        pygame.draw.ellipse(surface, (0, 0, 0), (x + 4, y + 22, 22, 9))
        if self.powerup and self.power_timer > 0:
            aura = self.power_color()
            pulse = 20 + int(math.sin(self.flap * 0.22) * 3)
            pygame.draw.circle(surface, aura, self.rect.center, pulse, 2)
            angle = self.flap * 0.08
            px = self.rect.centerx + int(math.cos(angle) * 18)
            py = self.rect.centery + int(math.sin(angle) * 14)
            pygame.draw.circle(surface, aura, (px, py), 4)
        if self.demon_mode:
            pulse = 22 + int(math.sin(self.flap * 0.28) * 4)
            for extra in (0, 8, 16):
                pygame.draw.circle(surface, (255, 45, 30), self.rect.center, pulse + extra, 2)
            ember = pygame.Surface((76, 76), pygame.SRCALPHA)
            pygame.draw.circle(ember, (255, 30, 20, 70), (38, 38), 24)
            surface.blit(ember, (self.rect.centerx - 38, self.rect.centery - 38))
        if self.kind == "bat":
            wing = int(math.sin(self.flap * 0.35) * 6)
            pygame.draw.polygon(surface, color, [(x + 15, y + 12), (x - 8, y + 6 + wing), (x + 2, y + 24)])
            pygame.draw.polygon(surface, color, [(x + 15, y + 12), (x + 38, y + 6 - wing), (x + 28, y + 24)])
            pygame.draw.circle(surface, DARK_GRAY, (x + 15, y + 15), 11)
            pygame.draw.circle(surface, RED, (x + 11, y + 13), 2)
            pygame.draw.circle(surface, RED, (x + 19, y + 13), 2)
        elif self.kind == "slime":
            pygame.draw.ellipse(surface, color, self.rect.inflate(4, 0))
            pygame.draw.circle(surface, BLACK, (x + 10, y + 12), 2)
            pygame.draw.circle(surface, BLACK, (x + 20, y + 12), 2)
            pygame.draw.arc(surface, BLACK, self.rect.inflate(-10, -11), 0, math.pi, 2)
        else:
            pygame.draw.rect(surface, color, self.rect, border_radius=9)
            pygame.draw.polygon(surface, DARK_RED, [(x + 4, y + 3), (x - 3, y - 7), (x + 12, y + 2)])
            pygame.draw.polygon(surface, DARK_RED, [(x + 26, y + 3), (x + 33, y - 7), (x + 18, y + 2)])
            pygame.draw.circle(surface, BLACK, (x + 9, y + 11), 3)
            pygame.draw.circle(surface, BLACK, (x + 21, y + 11), 3)
            pygame.draw.line(surface, BLACK, (x + 8, y + 22), (x + 22, y + 22), 2)


class Coin:
    def __init__(self, col: int, row: int, kind: str = "normal") -> None:
        x, y = tile_center(col, row, 22)
        self.rect = pygame.Rect(x, y, 22, 22)
        self.collected = False
        self.bob = random.randint(0, 120)
        self.kind = kind

    def update(self) -> None:
        self.bob += 1

    def color(self) -> Tuple[int, int, int]:
        if self.kind == "speed":
            return CYAN
        if self.kind == "shield":
            return BLUE
        if self.kind == "damage":
            return MAGENTA
        if self.kind == "heal":
            return RED
        return GOLD

    def draw(self, surface: pygame.Surface) -> None:
        if self.collected:
            return
        offset = int(math.sin(self.bob * 0.12) * 4)
        center = (self.rect.centerx, self.rect.centery + offset)
        color = self.color()
        pygame.draw.circle(surface, (60, 45, 20), (center[0] + 2, center[1] + 3), 11)
        pygame.draw.circle(surface, color, center, 11)
        pygame.draw.circle(surface, YELLOW if self.kind == "normal" else WHITE, center, 6)
        if self.kind != "normal":
            mark = {"speed": "S", "shield": "B", "damage": "X", "heal": "+"}.get(self.kind, "?")
            small_font = pygame.font.SysFont("arial", 13, bold=True)
            draw_text(surface, mark, small_font, BLACK, center[0], center[1], True)


class Chest:
    def __init__(self, col: int, row: int) -> None:
        x, y = tile_center(col, row, 34)
        self.rect = pygame.Rect(x, y + 4, 34, 28)
        self.opened = False

    def interact(self) -> bool:
        if not self.opened:
            self.opened = True
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, DARK_BROWN, self.rect, border_radius=5)
        pygame.draw.rect(surface, BROWN, (self.rect.x, self.rect.y, self.rect.w, 13), border_radius=5)
        pygame.draw.line(surface, GOLD, (self.rect.x + 3, self.rect.y + 13), (self.rect.right - 3, self.rect.y + 13), 2)
        pygame.draw.rect(surface, LIGHT_GRAY if self.opened else GOLD, (self.rect.centerx - 5, self.rect.y + 12, 10, 9), border_radius=2)
        if self.opened:
            pygame.draw.line(surface, BLACK, (self.rect.x + 5, self.rect.y + 7), (self.rect.right - 5, self.rect.y + 2), 3)


class KeyItem:
    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x, y, 28, 20)
        self.collected = False
        self.timer = 0

    def update(self) -> None:
        self.timer += 1

    def draw(self, surface: pygame.Surface) -> None:
        if self.collected:
            return
        y = self.rect.y + int(math.sin(self.timer * 0.11) * 5)
        pygame.draw.circle(surface, YELLOW, (self.rect.x + 8, y + 10), 8, 3)
        pygame.draw.rect(surface, YELLOW, (self.rect.x + 14, y + 8, 18, 5), border_radius=2)
        pygame.draw.rect(surface, YELLOW, (self.rect.x + 25, y + 12, 4, 6))


class Portal:
    def __init__(self, col: int, row: int) -> None:
        x, y = tile_center(col, row, 46)
        self.rect = pygame.Rect(x - 4, y - 10, 54, 64)
        self.timer = 0

    def update(self) -> None:
        self.timer += 1

    def draw(self, surface: pygame.Surface, active: bool) -> None:
        color = PURPLE if active else GRAY
        glow = MAGENTA if active else DARK_GRAY
        radius = 7 + int(math.sin(self.timer * 0.15) * 3)
        pygame.draw.ellipse(surface, color, self.rect, 5)
        pygame.draw.ellipse(surface, (30, 16, 62) if active else (30, 30, 36), self.rect.inflate(-16, -16))
        pygame.draw.circle(surface, glow, self.rect.center, radius)
        if active:
            for i in range(4):
                angle = self.timer * 0.05 + i * math.pi / 2
                px = self.rect.centerx + int(math.cos(angle) * 22)
                py = self.rect.centery + int(math.sin(angle) * 28)
                pygame.draw.circle(surface, PINK, (px, py), 3)


class Sign:
    def __init__(self, col: int, row: int, message: str) -> None:
        x, y = tile_center(col, row, 30)
        self.rect = pygame.Rect(x, y, 30, 30)
        self.message = message

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, DARK_BROWN, (self.rect.centerx - 3, self.rect.y + 12, 6, 22), border_radius=2)
        pygame.draw.rect(surface, BROWN, self.rect.inflate(8, -8), border_radius=5)
        pygame.draw.rect(surface, DARK_BROWN, self.rect.inflate(8, -8), 2, border_radius=5)
        pygame.draw.circle(surface, GOLD, self.rect.center, 3)


class Game:
    def __init__(self) -> None:
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Crystal Quest - 2D Adventure Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.big_font = pygame.font.SysFont("arial", 42, bold=True)
        self.title_font = pygame.font.SysFont("arial", 52, bold=True)
        self.sound = SoundBank()
        self.state = "menu"
        self.menu_index = 1
        self.difficulty_key = DIFFICULTY_ORDER[self.menu_index]
        self.level_index = 0
        self.message = ""
        self.message_timer = 0
        self.floating_texts: List[FloatingText] = []
        self.particles: List[Particle] = []
        self.rings: List[RingEffect] = []
        self.hazards: List[HazardProjectile] = []
        self.screen_flash = 0
        self.level_timer = 0
        self.night_mode = False
        self.night_mode_triggered = False
        self.hazard_spawn_timer = 0
        self.seismic_ready = False
        self.seismic_used = False
        self.load_level(0, keep_stats=False)

    def difficulty_settings(self) -> Dict[str, object]:
        return DIFFICULTIES[self.difficulty_key]

    def play_sound(self, name: str) -> None:
        self.sound.play(name)

    def start_new_run(self) -> None:
        self.total_score = 0
        self.total_defeated = 0
        self.load_level(0, keep_stats=False)
        self.state = "playing"

    def load_level(self, index: int, keep_stats: bool = True) -> None:
        self.level_index = index
        data = LEVELS[index]
        self.level_theme = data.get("theme", {})
        self.tile_map = TileMap(data["map"], self.level_theme)
        old_total = getattr(self, "total_score", 0) if keep_stats else 0
        old_defeated = getattr(self, "total_defeated", 0) if keep_stats else 0
        self.player = Player(*data["player"])
        self.player.total_coins = old_total
        self.total_score = old_total
        self.total_defeated = old_defeated
        self.coins: List[Coin] = [Coin(c, r) for c, r in data["coins"]]
        self.coins += [Coin(c, r, kind) for c, r, kind in data["powerups"]]
        self.enemies: List[Enemy] = [Enemy(c, r, kind) for c, r, kind in data["enemies"]]
        self.chest = Chest(*data["chest"])
        self.key_item: Optional[KeyItem] = None
        self.portal = Portal(*data["portal"])
        self.signs = [Sign(c, r, msg) for c, r, msg in data["signs"]]
        self.need_coins = max(1, data["need"] + int(self.difficulty_settings()["coin_delta"]))
        self.level_name = data["name"]
        self.message = ""
        self.message_timer = 0
        self.floating_texts.clear()
        self.particles.clear()
        self.rings.clear()
        self.hazards.clear()
        self.level_timer = 0
        self.night_mode = False
        self.night_mode_triggered = False
        self.hazard_spawn_timer = random.randint(90, 160)
        self.seismic_ready = False
        self.seismic_used = False
        self.validate_reachable_items(data)
        self.show_message(f"{self.level_name}: collect {self.need_coins} coins and find the key.", 180)

    def validate_reachable_items(self, data: Dict) -> None:
        start_col, start_row = data["player"]
        reachable = self.tile_map.reachable_tiles(start_col, start_row)
        required = list(data["coins"]) + [(c, r) for c, r, _ in data["powerups"]] + [data["chest"], data["portal"]]
        for col, row in required:
            if (col, row) not in reachable:
                raise ValueError(f"Unreachable item in {data['name']} at tile {(col, row)}")

    def show_message(self, text: str, duration: int = 130) -> None:
        self.message = text
        self.message_timer = duration

    def spawn_particles(self, x: int, y: int, color: Tuple[int, int, int], count: int = 12) -> None:
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.8, 3.6)
            self.particles.append(Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                                           color, random.randint(2, 4), random.randint(22, 48)))

    def spawn_ring(self, x: int, y: int, color: Tuple[int, int, int], growth: float = 2.8,
                   timer: int = 16, width: int = 3) -> None:
        self.rings.append(RingEffect(x, y, color, 10.0, growth, timer, width))

    def run(self) -> None:
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_game()
                if self.state == "menu":
                    if event.key in (pygame.K_w, pygame.K_UP, pygame.K_a, pygame.K_LEFT):
                        self.menu_index = (self.menu_index - 1) % len(DIFFICULTY_ORDER)
                        self.difficulty_key = DIFFICULTY_ORDER[self.menu_index]
                        self.play_sound("menu_move")
                    elif event.key in (pygame.K_s, pygame.K_DOWN, pygame.K_d, pygame.K_RIGHT):
                        self.menu_index = (self.menu_index + 1) % len(DIFFICULTY_ORDER)
                        self.difficulty_key = DIFFICULTY_ORDER[self.menu_index]
                        self.play_sound("menu_move")
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.difficulty_key = DIFFICULTY_ORDER[self.menu_index]
                        self.play_sound("menu_select")
                        self.start_new_run()
                elif self.state == "playing":
                    if event.key == pygame.K_p:
                        self.state = "paused"
                    elif event.key == pygame.K_SPACE:
                        self.perform_attack()
                    elif event.key == pygame.K_f:
                        self.use_seismic_charge()
                    elif event.key == pygame.K_e:
                        self.interact()
                elif self.state == "paused" and event.key == pygame.K_p:
                    self.state = "playing"
                elif self.state in ("win", "lose") and event.key == pygame.K_r:
                    self.start_new_run()

    def perform_attack(self) -> None:
        if not self.player.start_attack():
            return
        self.play_sound("attack")
        radius = self.player.attack_radius()
        hit = False
        attack_color = MAGENTA if self.player.damage_timer > 0 else WHITE
        self.spawn_ring(self.player.rect.centerx, self.player.rect.centery, attack_color, 4.1, 15, 3)
        for enemy in self.enemies:
            if enemy.alive and distance(self.player.rect.center, enemy.rect.center) <= radius:
                hit = True
                defeated = enemy.take_damage(self.player.attack_damage())
                self.play_sound("enemy_hit")
                hit_color = (255, 45, 30) if enemy.demon_mode else enemy.power_color()
                self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, hit_color, 22)
                self.spawn_ring(enemy.rect.centerx, enemy.rect.centery, hit_color, 3.8, 15, 3)
                self.floating_texts.append(FloatingText("Spin hit!", enemy.rect.centerx, enemy.rect.y, WHITE))
                if defeated:
                    self.player.coins += 1
                    self.total_score += 1
                    self.total_defeated += 1
                    self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, GOLD, 18)
                    self.spawn_ring(enemy.rect.centerx, enemy.rect.centery, GOLD, 4.0, 18, 4)
                    self.floating_texts.append(FloatingText("+1 coin", enemy.rect.centerx, enemy.rect.y - 18, GOLD))
        if not hit:
            self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, LIGHT_GRAY, 8)

    def interact(self) -> None:
        center = self.player.rect.center
        for sign in self.signs:
            if distance(center, sign.rect.center) < 62:
                self.show_message(sign.message, 230)
                return
        if distance(center, self.chest.rect.center) < 70:
            if self.chest.interact():
                self.key_item = KeyItem(self.chest.rect.x + 4, self.chest.rect.y - 24)
                self.play_sound("chest")
                self.spawn_particles(self.chest.rect.centerx, self.chest.rect.centery, GOLD, 22)
                self.show_message("Chest opened! Grab the crystal key.")
            else:
                self.show_message("The chest is already open.")
            return
        if self.portal.rect.colliderect(self.player.rect.inflate(20, 20)):
            if self.can_use_portal():
                self.play_sound("portal")
                if self.level_index < len(LEVELS) - 1:
                    self.load_level(self.level_index + 1, keep_stats=True)
                    self.show_message("Level complete! You entered the next area.", 180)
                else:
                    self.state = "win"
                    self.play_sound("win")
                    self.spawn_particles(self.portal.rect.centerx, self.portal.rect.centery, PURPLE, 52)
            else:
                self.show_message(f"Portal locked: need {self.need_coins} coins and the key.")
            return
        self.show_message("Nothing close enough to interact with.", 90)

    def can_use_portal(self) -> bool:
        return self.player.has_key and self.player.coins >= self.need_coins

    def hazard_profile(self) -> Dict[str, object]:
        style = self.level_theme.get("style", "forest")
        if style == "volcano":
            return {
                "name": "Fireball",
                "color": ORANGE,
                "glow": RED,
                "speed": 4.6,
                "radius": 10,
                "damage": 2,
                "source_tile": "W",
                "interval": (40, 82),
            }
        if style == "desert":
            return {
                "name": "Sun Shard",
                "color": GOLD,
                "glow": ORANGE,
                "speed": 4.1,
                "radius": 9,
                "damage": 1,
                "source_tile": "M",
                "interval": (58, 104),
            }
        return {
            "name": "Thorn Seed",
            "color": LIME,
            "glow": GREEN,
            "speed": 3.6,
            "radius": 8,
            "damage": 1,
            "source_tile": "T",
            "interval": (62, 112),
        }

    def level_hazard_sources(self, tile_type: str) -> List[Tuple[int, int]]:
        sources: List[Tuple[int, int]] = []
        for row_index, row in enumerate(self.tile_map.map_data):
            for col_index, tile in enumerate(row):
                if tile == tile_type:
                    sources.append((col_index * TILE + TILE // 2, row_index * TILE + TILE // 2))
        return sources

    def spawn_level_hazard(self) -> None:
        profile = self.hazard_profile()
        sources = self.level_hazard_sources(str(profile["source_tile"]))
        if not sources:
            return
        sx, sy = random.choice(sources)
        target = pygame.Vector2(
            self.player.rect.centerx + random.randint(-50, 50),
            self.player.rect.centery + random.randint(-50, 50),
        )
        origin = pygame.Vector2(sx, sy)
        direction = target - origin
        if direction.length() == 0:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize()
        speed = float(profile["speed"])
        origin += direction * (TILE * 0.35)
        self.hazards.append(
            HazardProjectile(
                origin.x,
                origin.y,
                direction.x * speed,
                direction.y * speed,
                profile["color"],
                profile["glow"],
                int(profile["radius"]),
                random.randint(80, 120),
                str(profile["name"]),
                int(profile["damage"]),
            )
        )

    def use_seismic_charge(self) -> None:
        if not self.seismic_ready or self.seismic_used:
            self.show_message("Seismic charge is locked. Collect every coin first.", 110)
            return
        self.seismic_used = True
        self.seismic_ready = False
        self.play_sound("seismic")
        self.spawn_ring(self.player.rect.centerx, self.player.rect.centery, CYAN, 8.0, 28, 5)
        self.spawn_ring(self.player.rect.centerx, self.player.rect.centery, WHITE, 11.0, 24, 3)
        self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, CYAN, 48)
        cleared = len(self.hazards)
        self.hazards.clear()
        defeated_count = 0
        for enemy in self.enemies:
            if enemy.alive:
                enemy.alive = False
                defeated_count += 1
                self.player.coins += 1
                self.total_score += 1
                self.total_defeated += 1
                self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, WHITE, 18)
                self.spawn_ring(enemy.rect.centerx, enemy.rect.centery, CYAN, 4.8, 20, 4)
        self.show_message(f"Seismic charge! {defeated_count} enemies crushed, {cleared} hazards cleared.", 170)

    def update(self) -> None:
        if self.state == "playing":
            difficulty = self.difficulty_settings()
            self.level_timer += 1
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
            self.player.update(self.tile_map)
            self.hazard_spawn_timer -= 1
            if not self.night_mode_triggered and self.level_timer >= NIGHT_MODE_TIME:
                self.night_mode_triggered = True
                self.night_mode = True
                self.play_sound("night")
                self.show_message("Night mode! 15 seconds of demon rush.", 180)
                self.screen_flash = 8
                for enemy in self.enemies:
                    enemy.activate_demon_mode()
                    self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, RED, 26)
                    self.spawn_ring(enemy.rect.centerx, enemy.rect.centery, RED, 4.4, 18, 4)
                    self.floating_texts.append(FloatingText("DEMON MODE", enemy.rect.centerx, enemy.rect.y - 16, RED))
            if self.night_mode and self.level_timer >= NIGHT_MODE_TIME + NIGHT_MODE_DURATION:
                self.night_mode = False
                self.show_message("Sunrise. Demon rush is over.", 140)
                for enemy in self.enemies:
                    enemy.deactivate_demon_mode()
            if self.hazard_spawn_timer <= 0:
                self.spawn_level_hazard()
                interval_low, interval_high = self.hazard_profile()["interval"]
                self.hazard_spawn_timer = random.randint(int(interval_low), int(interval_high))
            for enemy in self.enemies:
                enemy.update(
                    self.tile_map,
                    self.player,
                    self.level_index + 1,
                    self.night_mode,
                    float(difficulty["enemy_speed"]),
                )
                if enemy.alive and enemy.rect.colliderect(self.player.rect):
                    blocked = self.player.shield_timer > 0
                    incoming_damage = enemy.damage + int(difficulty["enemy_damage_bonus"])
                    if self.player.take_damage(incoming_damage):
                        self.play_sound("hurt")
                        color = CYAN if blocked else enemy.power_color() if enemy.powerup == "fury" else RED
                        self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, color, 16)
                        self.spawn_ring(self.player.rect.centerx, self.player.rect.centery, color, 3.1, 14, 3)
                        damage_text = f"-{incoming_damage} HP" if incoming_damage > 1 else "-1 HP"
                        text = "Blocked!" if blocked else damage_text
                        self.floating_texts.append(FloatingText(text, self.player.rect.centerx, self.player.rect.y, color))
                        if enemy.powerup == "drain" and not blocked and enemy.alive and enemy.health > 0:
                            enemy.health += 1
                            self.floating_texts.append(FloatingText("Drain!", enemy.rect.centerx, enemy.rect.y - 12, MAGENTA))
            for coin in self.coins:
                coin.update()
                if not coin.collected and coin.rect.colliderect(self.player.rect.inflate(6, 6)):
                    coin.collected = True
                    self.player.coins += 1
                    self.total_score += 1
                    self.play_sound("coin" if coin.kind == "normal" else "powerup")
                    self.spawn_particles(coin.rect.centerx, coin.rect.centery, coin.color(), 14)
                    self.spawn_ring(coin.rect.centerx, coin.rect.centery, coin.color(), 3.0, 15, 3)
                    if coin.kind == "normal":
                        self.floating_texts.append(FloatingText("+1 coin", coin.rect.centerx, coin.rect.y, GOLD))
                    else:
                        msg = self.player.apply_powerup(coin.kind)
                        self.floating_texts.append(FloatingText(msg, coin.rect.centerx, coin.rect.y, coin.color()))
                        self.show_message(msg, 110)
                    if not self.seismic_used and all(existing_coin.collected for existing_coin in self.coins):
                        self.seismic_ready = True
                        self.play_sound("seismic")
                        self.spawn_ring(self.player.rect.centerx, self.player.rect.centery, CYAN, 5.0, 20, 4)
                        self.show_message("All coins collected! Press F to unleash Seismic Charge.", 180)
            if self.key_item:
                self.key_item.update()
                if not self.key_item.collected and self.key_item.rect.colliderect(self.player.rect.inflate(10, 10)):
                    self.key_item.collected = True
                    self.player.has_key = True
                    self.play_sound("key")
                    self.spawn_particles(self.key_item.rect.centerx, self.key_item.rect.centery, YELLOW, 22)
                    self.spawn_ring(self.key_item.rect.centerx, self.key_item.rect.centery, YELLOW, 4.1, 18, 4)
                    self.show_message("Crystal key collected! The portal can open when you have enough coins.")
            remaining_hazards: List[HazardProjectile] = []
            for hazard in self.hazards:
                hazard.update()
                out_of_bounds = (
                    hazard.x < -40 or hazard.x > WIDTH + 40 or
                    hazard.y < HUD_HEIGHT - 40 or hazard.y > HEIGHT + 40
                )
                if hazard.timer <= 0 or out_of_bounds:
                    continue
                if hazard.rect().colliderect(self.player.rect.inflate(4, 4)):
                    if self.player.take_damage(hazard.damage):
                        self.play_sound("hazard")
                        self.spawn_particles(int(hazard.x), int(hazard.y), hazard.glow, 16)
                        self.spawn_ring(int(hazard.x), int(hazard.y), hazard.glow, 3.8, 16, 3)
                        self.floating_texts.append(FloatingText(f"{hazard.label}!", hazard.x, hazard.y - 16, hazard.color))
                    continue
                remaining_hazards.append(hazard)
            self.hazards = remaining_hazards
            self.portal.update()
            self.update_ambient_effects()
            if not self.player.alive:
                self.state = "lose"
                self.play_sound("lose")
                self.screen_flash = 10
            if self.message_timer > 0:
                self.message_timer -= 1
        self.update_effects()

    def update_ambient_effects(self) -> None:
        if (self.player.speed_timer > 0 or self.player.damage_timer > 0) and random.random() < 0.35:
            glow = CYAN if self.player.speed_timer > 0 else MAGENTA
            self.particles.append(
                Particle(
                    self.player.rect.centerx + random.randint(-8, 8),
                    self.player.rect.centery + random.randint(-12, 10),
                    random.uniform(-0.8, 0.8),
                    random.uniform(-1.4, 0.2),
                    glow,
                    random.randint(2, 3),
                    random.randint(10, 18),
                )
            )
        if self.can_use_portal() and random.random() < 0.18:
            angle = random.uniform(0, math.tau)
            radius_x = random.randint(12, 24)
            radius_y = random.randint(18, 30)
            px = self.portal.rect.centerx + int(math.cos(angle) * radius_x)
            py = self.portal.rect.centery + int(math.sin(angle) * radius_y)
            self.particles.append(Particle(px, py, 0, -0.7, PINK, 3, 18))
        if self.player.attack_timer > 0 and random.random() < 0.8:
            angle = random.uniform(0, math.tau)
            radius = random.randint(26, self.player.attack_radius())
            px = self.player.rect.centerx + int(math.cos(angle) * radius)
            py = self.player.rect.centery + int(math.sin(angle) * radius)
            color = MAGENTA if self.player.damage_timer > 0 else YELLOW
            self.particles.append(Particle(px, py, random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), color, 3, 14))
        if self.night_mode and random.random() < 0.25:
            self.particles.append(
                Particle(
                    random.randint(0, WIDTH),
                    random.randint(HUD_HEIGHT, HEIGHT),
                    random.uniform(-0.15, 0.15),
                    random.uniform(0.1, 0.45),
                    blend((80, 120, 255), WHITE, random.random() * 0.35),
                    random.randint(1, 2),
                    random.randint(24, 40),
                )
            )
        if self.night_mode:
            for enemy in self.enemies:
                if enemy.alive and enemy.demon_mode and random.random() < 0.28:
                    self.particles.append(
                        Particle(
                            enemy.rect.centerx + random.randint(-12, 12),
                            enemy.rect.centery + random.randint(-12, 12),
                            random.uniform(-0.5, 0.5),
                            random.uniform(-1.2, -0.2),
                            (255, random.randint(20, 60), 10),
                            random.randint(2, 4),
                            random.randint(10, 18),
                        )
                    )

    def update_effects(self) -> None:
        for text in self.floating_texts:
            text.update()
        self.floating_texts = [t for t in self.floating_texts if t.timer > 0]
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.timer > 0]
        for ring in self.rings:
            ring.update()
        self.rings = [r for r in self.rings if r.timer > 0]
        if self.screen_flash > 0:
            self.screen_flash -= 1

    def draw(self) -> None:
        self.screen.fill(BLACK)
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_world()
            if self.state == "paused":
                self.draw_overlay("Paused", "Press P to continue")
            elif self.state == "win":
                self.draw_overlay("You Win!", "Press R to restart or ESC to quit")
            elif self.state == "lose":
                self.draw_overlay("Game Over", "Press R to restart or ESC to quit")
        pygame.display.flip()

    def draw_menu(self) -> None:
        self.screen.fill((14, 20, 34))
        for i in range(10):
            radius = 90 + i * 16
            pygame.draw.circle(self.screen, blend((30, 70, 100), (5, 8, 14), i / 10), (WIDTH // 2, 110), radius, 2)
        draw_text(self.screen, "Crystal Quest", self.title_font, WHITE, WIDTH // 2, 92, True)
        draw_text(self.screen, "Choose your mode before stepping into the adventure.", self.font, LIGHT_GRAY, WIDTH // 2, 144, True)
        card_width = 250
        gap = 28
        start_x = WIDTH // 2 - (card_width * 3 + gap * 2) // 2
        for index, key in enumerate(DIFFICULTY_ORDER):
            settings = DIFFICULTIES[key]
            card = pygame.Rect(start_x + index * (card_width + gap), 215, card_width, 250)
            selected = index == self.menu_index
            fill = blend((18, 24, 38), settings["color"], 0.18 if selected else 0.06)
            border = settings["color"] if selected else LIGHT_GRAY
            draw_panel(self.screen, card, fill, border, 235, 22)
            draw_text(self.screen, settings["label"], self.big_font, settings["color"], card.centerx, card.y + 44, True)
            draw_text(self.screen, settings["description"], self.small_font, WHITE, card.centerx, card.y + 94, True)
            draw_text(self.screen, f"Enemy speed x{settings['enemy_speed']:.2f}", self.small_font, WHITE, card.centerx, card.y + 140, True)
            coin_adjust = int(settings["coin_delta"])
            coin_text = f"Coin goal {'+' if coin_adjust > 0 else ''}{coin_adjust}"
            draw_text(self.screen, coin_text, self.small_font, WHITE, card.centerx, card.y + 170, True)
            damage_text = f"Enemy damage +{int(settings['enemy_damage_bonus'])}"
            draw_text(self.screen, damage_text, self.small_font, WHITE, card.centerx, card.y + 200, True)
            if selected:
                draw_text(self.screen, "Selected", self.small_font, WHITE, card.centerx, card.y + 228, True)
        draw_text(self.screen, "Arrow keys or WASD to switch  |  ENTER or SPACE to begin", self.font, YELLOW, WIDTH // 2, 520, True)
        draw_text(self.screen, "Power coins: cyan speed, blue shield, red heal, purple damage.", self.small_font, LIGHT_GRAY, WIDTH // 2, 560, True)
        draw_text(self.screen, "Combat: move with WASD or arrows, spin attack with SPACE, interact with E, seismic with F.", self.small_font, LIGHT_GRAY, WIDTH // 2, 588, True)

    def draw_world(self) -> None:
        sky = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for band in range(6):
            base = self.level_theme.get("sky_night", (12, 18, 42)) if self.night_mode else self.level_theme.get("sky_day", (20, 44, 70))
            shade = blend(base, (0, 0, 0), band / 7)
            alpha = 40 if self.night_mode else 18
            pygame.draw.rect(sky, (*shade, alpha), (0, HUD_HEIGHT + band * 96, WIDTH, 96))
        self.screen.blit(sky, (0, 0))
        self.tile_map.draw(self.screen)
        self.chest.draw(self.screen)
        for sign in self.signs:
            sign.draw(self.screen)
        for coin in self.coins:
            coin.draw(self.screen)
        if self.key_item and not self.key_item.collected:
            self.key_item.draw(self.screen)
        self.portal.draw(self.screen, self.can_use_portal())
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for hazard in self.hazards:
            hazard.draw(self.screen)
        self.player.draw(self.screen)
        for particle in self.particles:
            particle.draw(self.screen)
        for ring in self.rings:
            ring.draw(self.screen)
        for text in self.floating_texts:
            text.draw(self.screen, self.small_font)
        self.draw_hud()
        if self.message_timer > 0 and self.message:
            self.draw_message_box(self.message)
        if self.night_mode:
            night_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay_color = self.level_theme.get("night_overlay", (16, 12, 44))
            night_overlay.fill((*overlay_color, 92))
            self.screen.blit(night_overlay, (0, 0))
        if self.screen_flash > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, self.screen_flash * 10))
            self.screen.blit(flash, (0, 0))

    def draw_hud(self) -> None:
        bar = pygame.Rect(8, 8, WIDTH - 16, HUD_HEIGHT - 10)
        draw_panel(self.screen, bar, (13, 16, 24), WHITE, 230, 18)
        for i in range(MAX_HEALTH):
            x = 18 + i * 27
            color = RED if i < self.player.health else DARK_GRAY
            pygame.draw.circle(self.screen, color, (x, 25), 9)
            pygame.draw.circle(self.screen, WHITE if i < self.player.health else GRAY, (x, 25), 9, 1)
        coin_text = f"Coins: {self.player.coins}/{self.need_coins}"
        draw_text(self.screen, coin_text, self.font, GOLD, 180, 14)
        key_text = "Key: YES" if self.player.has_key else "Key: NO"
        draw_text(self.screen, key_text, self.font, YELLOW if self.player.has_key else LIGHT_GRAY, 315, 14)
        draw_text(self.screen, f"{self.level_name}", self.small_font, WHITE, 430, 7)
        boosts = []
        if self.player.speed_timer > 0:
            boosts.append("Speed")
        if self.player.shield_timer > 0:
            boosts.append("Shield")
        if self.player.damage_timer > 0:
            boosts.append("Power Sword")
        if self.seismic_ready and not self.seismic_used:
            boosts.append("Seismic Ready")
        boost_text = "Boosts: " + (", ".join(boosts) if boosts else "None")
        draw_text(self.screen, boost_text, self.small_font, CYAN if boosts else LIGHT_GRAY, 430, 29)
        enemy_boosts = sum(1 for enemy in self.enemies if enemy.alive and enemy.powerup)
        if not self.night_mode_triggered:
            cycle_text = f"Night in {max(0, 30 - self.level_timer // FPS)}s"
            cycle_color = CYAN
        elif self.night_mode:
            cycle_text = f"Demon rush {max(0, 15 - max(0, self.level_timer - NIGHT_MODE_TIME) // FPS)}s"
            cycle_color = MAGENTA
        else:
            cycle_text = "Daylight returned"
            cycle_color = LIGHT_GRAY
        draw_text(self.screen, cycle_text, self.small_font, cycle_color, 690, 8)
        difficulty_label = self.difficulty_settings()["label"]
        draw_text(self.screen, str(difficulty_label), self.small_font, self.difficulty_settings()["color"], 610, 8)
        hazard_name = self.hazard_profile()["name"]
        draw_text(self.screen, f"Hazard: {hazard_name}", self.small_font, self.hazard_profile()["color"], 610, 28)
        draw_text(self.screen, f"Enemy buffs: {enemy_boosts}", self.small_font, ORANGE if enemy_boosts else LIGHT_GRAY, 835, 8)
        seismic_text = "F seismic" if self.seismic_ready and not self.seismic_used else "F locked"
        draw_text(self.screen, f"E interact | SPACE attack | {seismic_text} | P pause", self.small_font, WHITE, 730, 28)

    def draw_message_box(self, message: str) -> None:
        box = pygame.Rect(60, HEIGHT - 84, WIDTH - 120, 52)
        draw_panel(self.screen, box, (20, 20, 30), WHITE, 220, 15)
        draw_text(self.screen, message, self.font, WHITE, box.centerx, box.centery, True)

    def draw_overlay(self, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WIDTH // 2 - 260, HEIGHT // 2 - 130, 520, 260)
        draw_panel(self.screen, panel, (25, 25, 38), WHITE, 235, 22)
        draw_text(self.screen, title, self.big_font, WHITE, WIDTH // 2, HEIGHT // 2 - 60, True)
        draw_text(self.screen, subtitle, self.font, YELLOW, WIDTH // 2, HEIGHT // 2 + 3, True)
        stats = f"Total coins: {self.total_score} | Enemies defeated: {self.total_defeated} | Level: {self.level_index + 1}/3"
        draw_text(self.screen, stats, self.small_font, WHITE, WIDTH // 2, HEIGHT // 2 + 48, True)

    def quit_game(self) -> None:
        pygame.quit()
        sys.exit()


def main() -> None:
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
