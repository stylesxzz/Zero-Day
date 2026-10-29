import unittest

from zeroday.execution.risk import OrderProposal, RiskLimits, validate_order


class RiskEngineTests(unittest.TestCase):
    def setUp(self):
        self.limits = RiskLimits(max_order_quote=10, max_daily_loss_quote=25, max_open_positions=3)
        self.allowed = {"BTC/USDT"}

    def validate(self, proposal=None, pnl=0, positions=0):
        validate_order(
            proposal or OrderProposal("BTC/USDT", "buy", 0.001, 5),
            self.limits,
            daily_realized_pnl=pnl,
            open_positions=positions,
            allowed_symbols=self.allowed,
        )

    def test_accepts_order_within_limits(self):
        self.validate()

    def test_rejects_unlisted_symbol(self):
        with self.assertRaises(ValueError):
            self.validate(OrderProposal("DOGE/USDT", "buy", 1, 5))

    def test_rejects_order_over_limit(self):
        with self.assertRaises(ValueError):
            self.validate(OrderProposal("BTC/USDT", "buy", 1, 11))

    def test_halts_at_daily_loss_limit(self):
        with self.assertRaises(ValueError):
            self.validate(pnl=-25)

    def test_rejects_too_many_positions_for_buy(self):
        with self.assertRaises(ValueError):
            self.validate(positions=3)

    def test_rejects_invalid_side(self):
        with self.assertRaises(ValueError):
            self.validate(OrderProposal("BTC/USDT", "hold", 1, 5))


if __name__ == "__main__":
    unittest.main()
