"""Tick-based simulation: capital allocation, trading, death and reproduction."""

from __future__ import annotations

import random
from collections import deque

from .config import (
    BANKRUPTCY_FLOOR, DAY_LENGTH_TICKS, FEE_RATE, MAX_EVENT_LOG,
    REPRODUCTION_MULTIPLIER, RISK_PROFILES,
)
from .market import SimulatedMarket
from .models import Action, BuildingState, FeedEvent, Robot, RobotStatus
from .trading import TradingBrain


class SimulationEngine:
    def __init__(
        self,
        starting_capital: float = 10_000.0,
        initial_robots: int = 8,
        risk_name: str = "moderado",
        seed: int | None = None,
    ) -> None:
        if starting_capital <= 0:
            raise ValueError("O capital inicial precisa ser maior que zero.")
        if initial_robots < 1:
            raise ValueError("É necessário criar pelo menos um robô.")
        if risk_name not in RISK_PROFILES:
            raise ValueError(f"Perfil de risco inválido: {risk_name}")

        self.rng = random.Random(seed)
        self.market = SimulatedMarket(seed=seed)
        self.brain = TradingBrain()
        self.robots: dict[int, Robot] = {}
        self.next_robot_id = 1
        self.tick_count = 0
        self.risk_name = risk_name
        self.building = BuildingState()
        self.events: deque[FeedEvent] = deque(maxlen=MAX_EVENT_LOG)
        self.day_opening_balance = starting_capital
        self.daily_pnl = 0.0
        self.paused = False

        allocation = starting_capital / initial_robots
        for _ in range(initial_robots):
            self._create_robot(allocation, self.rng.choice(tuple(self.market.prices)))
        self._log(f"Edifício inicializado com {initial_robots} robôs e {self._money(starting_capital)}.")
        self._log("Mercado fictício iniciado. Nenhuma corretora ou carteira real está conectada.", "system")

    @staticmethod
    def _money(value: float) -> str:
        return f"₡ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _log(self, message: str, kind: str = "info") -> None:
        self.events.appendleft(FeedEvent(self.tick_count, message, kind))

    def _create_robot(
        self, capital: float, symbol: str,
        parent_id: int | None = None, generation: int = 0,
    ) -> Robot:
        robot = Robot(
            robot_id=self.next_robot_id, symbol=symbol, cash=capital,
            birth_capital=capital, risk_name=self.risk_name,
            generation=generation, peak_equity=capital,
            created_at_tick=self.tick_count, parent_id=parent_id,
            floor=self.rng.choice((4, 6)),
        )
        self.robots[robot.robot_id] = robot
        self.next_robot_id += 1
        return robot

    @property
    def alive_robots(self) -> list[Robot]:
        return [robot for robot in self.robots.values() if robot.status is RobotStatus.ACTIVE]

    @property
    def dead_robots(self) -> list[Robot]:
        return [robot for robot in self.robots.values() if robot.status is RobotStatus.DEAD]

    def total_balance(self) -> float:
        return sum(robot.equity(self.market.prices[robot.symbol]) for robot in self.alive_robots)

    def total_pnl(self) -> float:
        return self.total_balance() - self.day_opening_balance

    def set_risk(self, risk_name: str) -> None:
        if risk_name not in RISK_PROFILES:
            raise ValueError(f"Perfil de risco inválido: {risk_name}")
        self.risk_name = risk_name
        for robot in self.alive_robots:
            robot.risk_name = risk_name
        self._log(f"Política global alterada para risco {RISK_PROFILES[risk_name].name}.", "system")

    def add_robot(self, capital: float = 100.0) -> bool:
        if capital <= 0 or self.total_balance() < capital:
            return False
        contributors = self.alive_robots
        remaining = capital
        ledger: list[tuple[Robot, float]] = []
        for robot in contributors:
            available = max(0.0, robot.cash - BANKRUPTCY_FLOOR)
            take = min(available, remaining)
            if take > 0:
                robot.cash -= take
                ledger.append((robot, take))
                remaining -= take
            if remaining <= 0.000001:
                break
        if remaining > 0.000001:
            for robot, amount in ledger:
                robot.cash += amount
            return False
        new_robot = self._create_robot(capital, self.rng.choice(tuple(self.market.prices)))
        self._log(f"Robô #{new_robot.robot_id:03d} foi criado no laboratório.", "success")
        return True

    def _execute(self, robot: Robot, action: Action, price: float) -> None:
        if action is Action.BUY and robot.cash > BANKRUPTCY_FLOOR:
            profile = RISK_PROFILES[robot.risk_name]
            budget = min(robot.cash, robot.equity(price) * profile.allocation_pct)
            quantity = budget / (price * (1.0 + FEE_RATE))
            cost = quantity * price * (1.0 + FEE_RATE)
            if quantity > 0 and cost <= robot.cash:
                old_quantity = robot.quantity
                robot.average_entry = (
                    (robot.average_entry * old_quantity + price * quantity) / (old_quantity + quantity)
                    if old_quantity + quantity > 0 else price
                )
                robot.quantity += quantity
                robot.cash -= cost
                robot.total_trades += 1
                robot.floor = 4
                self._log(f"Robô #{robot.robot_id:03d} comprou {robot.symbol} a {self._money(price)}.", "trade")

        elif action is Action.SELL and robot.quantity > 0:
            proceeds = robot.quantity * price * (1.0 - FEE_RATE)
            profitable = price >= robot.average_entry
            robot.cash += proceeds
            robot.quantity = 0.0
            robot.average_entry = 0.0
            robot.total_trades += 1
            if profitable:
                robot.wins += 1
            else:
                robot.losses += 1
            robot.cooldown = 3
            robot.floor = 2
            self._log(
                f"Robô #{robot.robot_id:03d} vendeu {robot.symbol} em {self._money(price)} "
                f"({'lucro' if profitable else 'prejuízo'}).",
                "success" if profitable else "warning",
            )

    def _kill_robot(self, robot: Robot, reason: str) -> None:
        robot.cash = 0.0
        robot.quantity = 0.0
        robot.average_entry = 0.0
        robot.status = RobotStatus.DEAD
        robot.floor = -2
        robot.death_reason = reason
        self._log(f"Robô #{robot.robot_id:03d} quebrou: {reason}. Enviado à Sala Abandonada.", "danger")

    def _reproduce(self, robot: Robot, equity: float) -> None:
        if equity < robot.birth_capital * REPRODUCTION_MULTIPLIER:
            return
        child_capital = equity / 2.0
        robot.cash = child_capital
        robot.quantity = 0.0
        robot.average_entry = 0.0
        robot.birth_capital = child_capital
        robot.peak_equity = child_capital
        robot.generation += 1
        robot.floor = 6
        child = self._create_robot(
            child_capital, robot.symbol,
            parent_id=robot.robot_id, generation=robot.generation,
        )
        child.risk_name = robot.risk_name
        self._log(
            f"Robô #{robot.robot_id:03d} atingiu +100% e se dividiu: nasceu #{child.robot_id:03d}.",
            "success",
        )

    def tick(self) -> None:
        if self.paused:
            return
        self.tick_count += 1
        self.market.step()

        for robot in list(self.alive_robots):
            price = self.market.prices[robot.symbol]
            if robot.cooldown > 0:
                robot.cooldown -= 1
                robot.floor = self.rng.choice((2, 8, 9))
                continue

            snapshot = self.market.snapshot(robot.symbol)
            decision = self.brain.decide(robot, snapshot)
            self._execute(robot, decision.action, price)
            equity = robot.equity(price)
            robot.peak_equity = max(robot.peak_equity, equity)

            if equity <= BANKRUPTCY_FLOOR:
                self._kill_robot(robot, "saldo abaixo do limite de sobrevivência")
                continue

            self._reproduce(robot, equity)
            if decision.action is Action.HOLD:
                robot.floor = 6 if self.tick_count % 2 else 5

        self.daily_pnl = self.total_balance() - self.day_opening_balance
        if self.tick_count % DAY_LENGTH_TICKS == 0:
            self.day_opening_balance = self.total_balance()
            self._log(f"Fechamento do ciclo: saldo {self._money(self.total_balance())}.", "system")

        if len(self.alive_robots) >= self.building.floor_capacity and not self.building.expansion_unlocked:
            self.building.expansion_unlocked = True
            self._log("População crítica: uma filial foi desbloqueada no mapa.", "success")
        elif self.building.expansion_unlocked and len(self.alive_robots) >= self.building.floor_capacity * self.building.branch_count:
            self.building.branch_count += 1
            self._log(f"Nova filial construída. Total de prédios: {self.building.branch_count}.", "success")

    def run(self, ticks: int) -> None:
        for _ in range(max(0, ticks)):
            self.tick()

    def leaderboard(self, limit: int = 10) -> list[tuple[Robot, float]]:
        ranked = [(robot, robot.equity(self.market.prices[robot.symbol])) for robot in self.alive_robots]
        return sorted(ranked, key=lambda item: item[1], reverse=True)[:limit]
