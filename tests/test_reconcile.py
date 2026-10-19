import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.reconcile import ROOT, build, money, read_rows, reconcile


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.payouts = read_rows(ROOT / "data/shopify_payouts.csv", {"payout_id", "paid_at", "net_amount_usd"})
        self.deposits = read_rows(ROOT / "data/bank_deposits.csv", {"bank_transaction_id", "posted_at", "payout_id", "amount_usd"})

    def test_fixture_explains_each_exception(self):
        results = reconcile(self.payouts, self.deposits, date(2026, 10, 6))
        self.assertEqual({row["payout_id"]: row["status"] for row in results}, {
            "po-1001": "MATCHED",
            "po-1002": "DUPLICATE_BANK_ROW",
            "po-1003": "AMOUNT_MISMATCH",
            "po-1004": "PENDING_TIMING",
            "po-9999": "UNMATCHED_BANK_ROW",
        })

    def test_mismatch_dollars_are_exact(self):
        results = {row["payout_id"]: row for row in reconcile(self.payouts, self.deposits, date(2026, 10, 6))}
        self.assertEqual(results["po-1003"]["difference_usd"], "20.00")
        self.assertEqual(results["po-1002"]["difference_usd"], "-840.00")

    def test_pending_ages_into_investigation(self):
        results = {row["payout_id"]: row for row in reconcile(self.payouts, self.deposits, date(2026, 10, 9))}
        self.assertEqual(results["po-1004"]["status"], "AMOUNT_MISMATCH")

    def test_duplicate_source_identifiers_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate payout ID"):
            reconcile(self.payouts + [self.payouts[0]], self.deposits, date(2026, 10, 6))
        with self.assertRaisesRegex(ValueError, "duplicate bank transaction ID"):
            reconcile(self.payouts, self.deposits + [self.deposits[0]], date(2026, 10, 6))

    def test_invalid_money_rejected(self):
        for value in ["NaN", "-1.00", "1.234", "abc"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                money(value)

    def test_missing_column_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("payout_id,paid_at\npo-1,2026-10-01\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing required columns"):
                read_rows(path, {"payout_id", "paid_at", "net_amount_usd"})

    def test_outputs_are_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(output_dir=output)
            first = {path.name: path.read_bytes() for path in output.iterdir()}
            build(output_dir=output)
            self.assertEqual(first, {path.name: path.read_bytes() for path in output.iterdir()})
            with (output / "reconciliation.csv").open(newline="", encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 5)
            self.assertEqual(json.loads((output / "summary.json").read_text())["counts"]["MATCHED"], 1)


if __name__ == "__main__":
    unittest.main()
