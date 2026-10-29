import unittest

from zeroday.models import Action, MarketSnapshot, Robot, RobotStatus
from zeroday.simulation import SimulationEngine
from zeroday.trading import TradingBrain


class TradingBrainTests(unittest.TestCase):
    def test_buy_signal_requires_uptrend_and_rsi_window(self):
        bot = Robot(1, "BTC", 1000.0, 1000.0, risk_name="moderado")
        market = MarketSnapshot("BTC", 101.0, 102.0, 100.0, 55.0, 0.02, 0.01)
        self.assertEqual(TradingBrain().decide(bot, market).action, Action.BUY)

    def test_no_buy_when_market_is_falling(self):
        bot = Robot(1, "BTC", 1000.0, 1000.0, risk_name="moderado")
        market = MarketSnapshot("BTC", 99.0, 98.0, 100.0, 50.0, -0.02, 0.01)
        self.assertEqual(TradingBrain().decide(bot, market).action, Action.HOLD)


class SimulationTests(unittest.TestCase):
    def test_initial_capital_is_conserved(self):
        engine = SimulationEngine(1200.0, 6, seed=10)
        self.assertAlmostEqual(engine.total_balance(), 1200.0, places=6)
        self.assertEqual(len(engine.alive_robots), 6)

    def test_tick_updates_market(self):
        engine = SimulationEngine(1000.0, 4, seed=1)
        before = dict(engine.market.prices)
        engine.tick()
        self.assertEqual(engine.tick_count, 1)
        self.assertTrue(any(engine.market.prices[s] != before[s] for s in before))

    def test_risk_change_updates_existing_agents(self):
        engine = SimulationEngine(1000.0, 4, seed=2)
        engine.set_risk("agressivo")
        self.assertTrue(all(bot.risk_name == "agressivo" for bot in engine.alive_robots))

    def test_dead_robot_is_not_counted_as_alive(self):
        engine = SimulationEngine(1000.0, 1, seed=2)
        robot = engine.alive_robots[0]
        engine._kill_robot(robot, "teste")
        self.assertEqual(robot.status, RobotStatus.DEAD)
        self.assertEqual(robot.floor, -2)
        self.assertEqual(len(engine.alive_robots), 0)

    def test_reproduction_splits_equity_without_creating_capital(self):
        engine = SimulationEngine(1000.0, 1, seed=3)
        robot = engine.alive_robots[0]
        robot.cash = robot.birth_capital * 2.0
        before = engine.total_balance()
        engine._reproduce(robot, robot.equity(engine.market.prices[robot.symbol]))
        self.assertEqual(len(engine.alive_robots), 2)
        self.assertAlmostEqual(engine.total_balance(), before, places=6)


if __name__ == "__main__":
    unittest.main()
