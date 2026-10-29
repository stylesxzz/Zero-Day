"""Pygame interface for the Zéro Day tower simulator."""

from __future__ import annotations

import math
import sys

import pygame

from .config import FLOORS, RISK_PROFILES
from .models import RobotStatus
from .simulation import SimulationEngine


BG = (5, 10, 15)
PANEL = (10, 19, 27)
ALT = (13, 27, 36)
BORDER = (27, 74, 82)
GREEN = (0, 244, 145)
CYAN = (45, 206, 238)
WHITE = (224, 241, 244)
MUTED = (119, 151, 161)
RED = (255, 82, 105)
AMBER = (255, 190, 85)


class GameApp:
    WIDTH, HEIGHT = 1460, 900

    def __init__(self, engine: SimulationEngine) -> None:
        pygame.init()
        pygame.display.set_caption("ZÉRO DAY: SWARM TRADING")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.engine = engine
        self.running = True
        self.selected_floor: int | None = None
        self.buttons: dict[str, pygame.Rect] = {}
        self.floor_buttons: dict[int, pygame.Rect] = {}
        self.risk_buttons: dict[str, pygame.Rect] = {}
        self.font = {
            "tiny": pygame.font.SysFont("consolas", 12),
            "small": pygame.font.SysFont("consolas", 14),
            "body": pygame.font.SysFont("consolas", 16),
            "medium": pygame.font.SysFont("consolas", 20, bold=True),
            "large": pygame.font.SysFont("consolas", 28, bold=True),
            "brand": pygame.font.SysFont("arial", 25, bold=True),
        }

    def text(self, value: str, x: int, y: int, color=WHITE, size="small") -> None:
        self.screen.blit(self.font[size].render(str(value), True, color), (x, y))

    def panel(self, rect: pygame.Rect, title: str) -> None:
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=12)
        self.text(title, rect.x + 15, rect.y + 12, CYAN, "body")
        pygame.draw.line(self.screen, BORDER, (rect.x + 14, rect.y + 40), (rect.right - 14, rect.y + 40))

    def button(self, key: str, rect: pygame.Rect, label: str, active=False, color=GREEN) -> None:
        pygame.draw.rect(self.screen, (12, 50, 43) if active else ALT, rect, border_radius=7)
        pygame.draw.rect(self.screen, color if active else BORDER, rect, 1, border_radius=7)
        label_surface = self.font["small"].render(label, True, color if active else WHITE)
        self.screen.blit(label_surface, label_surface.get_rect(center=rect.center))
        self.buttons[key] = rect

    def draw_header(self, width: int) -> None:
        pygame.draw.rect(self.screen, (7, 15, 21), pygame.Rect(0, 0, width, 72))
        pygame.draw.line(self.screen, BORDER, (0, 71), (width, 71))
        pygame.draw.polygon(self.screen, GREEN, [(24, 17), (47, 17), (31, 35), (51, 35), (19, 61), (28, 41), (11, 41)])
        self.text("ZÉRO DAY", 62, 12, WHITE, "brand")
        self.text("SWARM TRADING  /  SIMULADOR AUTÔNOMO", 64, 42, GREEN, "tiny")
        status = "PAUSADO" if self.engine.paused else f"SIMULAÇÃO ATIVA  ·  TICK {self.engine.tick_count:,}"
        self.text(status, max(650, width - 370), 27, AMBER if self.engine.paused else GREEN, "small")
        self.button("pause", pygame.Rect(width - 154, 18, 130, 36),
                    "RETOMAR" if self.engine.paused else "PAUSAR", self.engine.paused, AMBER)

    def draw_stats(self, rect: pygame.Rect) -> None:
        self.panel(rect, "PAINEL DA DIREÇÃO")
        values = [
            ("SALDO TOTAL", self.engine._money(self.engine.total_balance()), GREEN),
            ("ROBÔS VIVOS", f"{len(self.engine.alive_robots):03d}", CYAN),
            ("ROBÔS MORTOS", f"{len(self.engine.dead_robots):03d}", RED),
            ("LUCRO / PREJUÍZO DO DIA", self.engine._money(self.engine.daily_pnl), GREEN if self.engine.daily_pnl >= 0 else RED),
        ]
        y = rect.y + 55
        for label, value, color in values:
            self.text(label, rect.x + 15, y, MUTED, "tiny")
            self.text(value, rect.x + 15, y + 17, color, "medium")
            y += 65
        pygame.draw.line(self.screen, BORDER, (rect.x + 14, y), (rect.right - 14, y))
        self.text("POLÍTICA DE RISCO", rect.x + 15, y + 8, CYAN, "small")
        y += 31
        for index, risk in enumerate(("conservador", "moderado", "agressivo")):
            item = pygame.Rect(rect.x + 12 + index * 77, y, 72, 28)
            self.risk_buttons[risk] = item
            self.button("risk:" + risk, item, ("BAIXO", "MÉDIO", "ALTO")[index],
                        self.engine.risk_name == risk)
        y += 38
        self.button("spawn", pygame.Rect(rect.x + 12, y, rect.w - 24, 30), "+ CRIAR ROBÔ  (₡ 100)", False, CYAN)
        y += 45
        self.text("FEED DE EVENTOS", rect.x + 15, y, CYAN, "small")
        y += 25
        for event in list(self.engine.events)[:max(1, (rect.bottom - y - 8) // 42)]:
            color = {"danger": RED, "warning": AMBER, "success": GREEN, "trade": CYAN, "system": MUTED}.get(event.kind, WHITE)
            self.text(f"T{event.tick:04d}", rect.x + 14, y, color, "tiny")
            self.wrap(event.message, rect.x + 57, y, rect.w - 68, color)
            y += 42

    def wrap(self, value: str, x: int, y: int, max_width: int, color) -> None:
        words, lines, line = value.split(), [], ""
        for word in words:
            candidate = (line + " " + word).strip()
            if self.font["tiny"].size(candidate)[0] > max_width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        for index, part in enumerate(lines[:2]):
            self.text(part, x, y + index * 14, color, "tiny")

    def draw_floors(self, rect: pygame.Rect) -> None:
        self.panel(rect, "MAPA DE ANDARES")
        self.text("CLIQUE EM UM SETOR PARA ENTRAR", rect.x + 15, rect.y + 48, MUTED, "tiny")
        self.floor_buttons.clear()
        y = rect.y + 70
        for floor in (10, 9, 8, 7, 6, 5, 4, 3, 2, 1, -1, -2):
            name, _description = FLOORS[floor]
            row = pygame.Rect(rect.x + 10, y, rect.w - 20, 49)
            selected = self.selected_floor == floor
            pygame.draw.rect(self.screen, (12, 47, 42) if selected else ALT, row, border_radius=7)
            pygame.draw.rect(self.screen, GREEN if selected else BORDER, row, 1, border_radius=7)
            self.text(f"{floor:>2}", row.x + 9, row.y + 8, GREEN if selected else CYAN, "medium")
            self.text(name.upper()[:23], row.x + 50, row.y + 7, WHITE if selected else MUTED, "tiny")
            count = len(self.engine.dead_robots) if floor == -2 else sum(bot.floor == floor for bot in self.engine.alive_robots)
            self.text(f"{count:02d} AGENTES", row.x + 50, row.y + 24, GREEN if count else MUTED, "tiny")
            self.floor_buttons[floor] = row
            y += 53
        self.text(f"FILIAIS: {self.engine.building.branch_count}", rect.x + 14, rect.bottom - 32, GREEN, "small")
        state = "DESBLOQUEADA" if self.engine.building.expansion_unlocked else "EM CONSTRUÇÃO"
        self.text("EXPANSÃO: " + state, rect.x + 133, rect.bottom - 30, MUTED, "tiny")

    def draw_tower(self, rect: pygame.Rect) -> None:
        self.panel(rect, "VISÃO GERAL DO COMPLEXO")
        self.text("ESTRUTURA ISOMÉTRICA  /  ANDARES INTERATIVOS", rect.x + 15, rect.y + 48, MUTED, "tiny")
        center_x, base_y = rect.centerx, rect.bottom - 88
        for index, floor in enumerate((10, 9, 8, 7, 6, 5, 4, 3, 2, 1, -1)):
            y = base_y - index * 48
            width = 286 - index * 8
            left, right = center_x - width // 2, center_x + width // 2
            front = [(left, y - 34), (right, y - 34), (right - 18, y), (left - 18, y)]
            side = [(right, y - 34), (right + 18, y - 50), (right + 18, y - 16), (right - 18, y)]
            top = [(left, y - 34), (left + 18, y - 50), (right + 18, y - 50), (right, y - 34)]
            color = (18, 83, 69) if self.selected_floor == floor else (14, 39 + index * 2, 46 + index * 2)
            pygame.draw.polygon(self.screen, color, front)
            pygame.draw.polygon(self.screen, (15, 52, 68), side)
            pygame.draw.polygon(self.screen, (22, 75, 83), top)
            pygame.draw.polygon(self.screen, GREEN if self.selected_floor == floor else BORDER, front, 1)
            self.text(str(floor), left + 13, y - 27, GREEN if self.selected_floor == floor else WHITE, "small")
            for wx in range(left + 56, right - 12, 22):
                pygame.draw.rect(self.screen, CYAN if (wx + index) % 3 else GREEN, (wx, y - 25, 8, 13), border_radius=2)
            bots = [bot for bot in self.engine.alive_robots if bot.floor == floor]
            for bot_index, _bot in enumerate(bots[:6]):
                pygame.draw.circle(self.screen, GREEN, (right - 28 + bot_index % 3 * 7, y - 12 - bot_index // 3 * 8), 3)
        pygame.draw.polygon(self.screen, (11, 30, 39), [
            (center_x - 190, base_y + 5), (center_x + 190, base_y + 5),
            (center_x + 250, base_y + 48), (center_x - 250, base_y + 48),
        ])
        pygame.draw.rect(self.screen, (16, 58, 64), (center_x - 55, base_y + 7, 110, 40), border_radius=5)
        self.text("ZÉRO DAY", center_x - 43, base_y + 19, WHITE, "small")
        chart = pygame.Rect(rect.x + 20, rect.bottom - 57, rect.w - 40, 37)
        pygame.draw.rect(self.screen, (5, 13, 19), chart, border_radius=6)
        x = chart.x + 12
        for symbol, color in zip(self.engine.market.prices, (GREEN, CYAN, AMBER, WHITE)):
            self.text(f"{symbol} {self.engine.market.prices[symbol]:,.2f}", x, chart.y + 11, color, "tiny")
            x += 145

    def draw_robot(self, x: int, y: int, bot_id: int) -> None:
        bob = int(math.sin(self.engine.tick_count * 0.16 + bot_id) * 2)
        y += bob
        pygame.draw.ellipse(self.screen, (4, 8, 12), (x - 10, y + 16, 20, 6))
        pygame.draw.rect(self.screen, (20, 58, 67), (x - 7, y - 1, 14, 16), border_radius=4)
        pygame.draw.rect(self.screen, GREEN, (x - 8, y - 10, 16, 12), border_radius=4)
        pygame.draw.rect(self.screen, (2, 17, 22), (x - 4, y - 6, 8, 3), border_radius=2)
        pygame.draw.circle(self.screen, CYAN, (x - 2, y - 5), 1)
        pygame.draw.circle(self.screen, CYAN, (x + 2, y - 5), 1)
        self.text(f"{bot_id:03d}", x - 11, y + 19, MUTED, "tiny")

    def draw_room(self, rect: pygame.Rect) -> None:
        floor = self.selected_floor
        name, description = FLOORS[floor]
        self.panel(rect, f"ANDAR {floor}  /  {name.upper()}")
        self.text(description, rect.x + 15, rect.y + 48, MUTED, "small")
        room = pygame.Rect(rect.x + 24, rect.y + 82, rect.w - 48, rect.h - 158)
        pygame.draw.rect(self.screen, (8, 20, 28), room, border_radius=8)
        pygame.draw.rect(self.screen, BORDER, room, 1, border_radius=8)
        pygame.draw.polygon(self.screen, (14, 40, 47), [
            (room.x + 35, room.y + 130), (room.right - 35, room.y + 130),
            (room.right - 5, room.bottom - 15), (room.x + 5, room.bottom - 15),
        ])
        pygame.draw.polygon(self.screen, (12, 30, 43), [
            (room.x + 35, room.y + 130), (room.x + 35, room.y + 35),
            (room.centerx, room.y + 5), (room.centerx, room.y + 130),
        ])
        pygame.draw.polygon(self.screen, (10, 25, 38), [
            (room.centerx, room.y + 130), (room.centerx, room.y + 5),
            (room.right - 35, room.y + 35), (room.right - 35, room.y + 130),
        ])
        for index in range(1, 8):
            line_y = room.y + 130 + index * 22
            pygame.draw.line(self.screen, (24, 67, 70), (room.x + 20, line_y), (room.right - 20, line_y))
        if floor in (6, 5, 4, -1, 10):
            for index in range(4):
                cx = room.x + 105 + index * 130
                desk = pygame.Rect(cx - 34, room.y + 205 + (index % 2) * 55, 68, 22)
                pygame.draw.rect(self.screen, (17, 62, 69), desk, border_radius=4)
                pygame.draw.rect(self.screen, CYAN, (desk.x + 8, desk.y - 24, 52, 20), 1, border_radius=3)
        elif floor in (9, 8, 2):
            for index in range(4):
                bed = pygame.Rect(room.x + 100 + index * 135, room.y + 210 + (index % 2) * 55, 88, 42)
                pygame.draw.rect(self.screen, (29, 53, 70), bed, border_radius=7)
                pygame.draw.rect(self.screen, (112, 171, 181), (bed.x + 8, bed.y + 5, 24, 14), border_radius=4)
        elif floor == -2:
            self.text("SALA ABANDONADA", room.x + 25, room.y + 175, RED, "large")
            self.text("AGENTES DESATIVADOS / MEMÓRIA DO SISTEMA", room.x + 27, room.y + 220, MUTED, "small")
        else:
            for index in range(4):
                pygame.draw.rect(self.screen, (16, 57, 66), (room.x + 120 + index * 120, room.y + 220, 56, 32), border_radius=5)

        bots = [bot for bot in self.engine.robots.values() if bot.floor == floor]
        if floor == -2:
            bots = self.engine.dead_robots
        for bot in bots[:36]:
            x = room.x + 70 + (bot.robot_id * 83 + self.engine.tick_count * 2) % max(1, room.w - 140)
            y = room.y + 300 + (bot.robot_id * 29) % max(1, room.h - 340)
            if bot.status is RobotStatus.DEAD:
                pygame.draw.rect(self.screen, (80, 42, 51), (x - 8, y - 2, 16, 12), border_radius=2)
                pygame.draw.line(self.screen, RED, (x - 7, y - 9), (x + 7, y + 8), 2)
                pygame.draw.line(self.screen, RED, (x + 7, y - 9), (x - 7, y + 8), 2)
            else:
                self.draw_robot(x, y, bot.robot_id)
        self.text(f"AGENTES NESTE SETOR: {len(bots)}", room.x + 18, room.bottom - 36, GREEN, "small")
        self.button("back", pygame.Rect(rect.x + 16, rect.bottom - 60, 150, 34), "← VISÃO DA TORRE", False, CYAN)

    def draw(self) -> None:
        width, height = self.screen.get_size()
        self.buttons.clear()
        self.risk_buttons.clear()
        self.screen.fill(BG)
        self.draw_header(width)
        margin, gap = 18, 12
        left = pygame.Rect(margin, 88, max(245, int(width * 0.205)), height - 106)
        right = pygame.Rect(width - max(285, int(width * 0.25)) - margin, 88, max(285, int(width * 0.25)), height - 106)
        center = pygame.Rect(left.right + gap, 88, right.x - left.right - gap * 2, height - 106)
        self.draw_stats(left)
        if self.selected_floor is None:
            self.draw_tower(center)
        else:
            self.draw_room(center)
        self.draw_floors(right)
        pygame.display.flip()

    def click(self, pos: tuple[int, int]) -> None:
        for risk, rect in self.risk_buttons.items():
            if rect.collidepoint(pos):
                self.engine.set_risk(risk)
                return
        for floor, rect in self.floor_buttons.items():
            if rect.collidepoint(pos):
                self.selected_floor = floor
                return
        for key, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if key == "pause":
                    self.engine.paused = not self.engine.paused
                elif key == "spawn":
                    self.engine.add_robot(100.0)
                elif key == "back":
                    self.selected_floor = None
                return

    def run(self) -> None:
        while self.running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.engine.paused = not self.engine.paused
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        self.engine.set_risk(("conservador", "moderado", "agressivo")[event.key - pygame.K_1])
                    elif event.key == pygame.K_b:
                        self.selected_floor = None
            if not self.engine.paused:
                self.engine.tick()
            self.draw()
        pygame.quit()
        sys.exit(0)
