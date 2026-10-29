import tempfile
import unittest
from pathlib import Path

from zeroday.backend import store
from zeroday.execution.exchange import SpotExchange
from zeroday.backend.wallets import evm_native_balance


class BackendPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = store.DB_PATH
        store.DB_PATH = Path(self.tmp.name) / "test.db"
        store.init_db()

    def tearDown(self):
        store.DB_PATH = self.original_db
        self.tmp.cleanup()

    def test_agent_and_proposal_persist(self):
        agent = store.create_agent({
            "id":"agent-test", "name":"Test Bot", "strategy":"trend",
            "model":"test-model", "provider_id":"default",
            "risk_profile":"conservative", "allocation":0,
        })
        self.assertEqual(agent["provider_id"], "default")
        store.save_proposal({
            "id":"proposal-test", "agent_id":"agent-test", "symbol":"BTC/USD",
            "action":"HOLD", "confidence":0.8, "rationale":"No clear signal",
            "snapshot":{"last":100}, "status":"pending_validation",
        })
        proposals = store.list_proposals()
        self.assertEqual(proposals[0]["action"], "HOLD")
        self.assertEqual(proposals[0]["snapshot"]["last"], 100)

    def test_live_order_submission_is_always_blocked(self):
        adapter = SpotExchange.__new__(SpotExchange)
        with self.assertRaisesRegex(RuntimeError, "DISABLED"):
            adapter.submit_market_order("BTC/USD", "buy", 0.001, 10)

    def test_onchain_connector_rejects_invalid_address(self):
        with self.assertRaises(ValueError):
            evm_native_balance("ethereum", "not-an-address")


if __name__ == "__main__":
    unittest.main()
