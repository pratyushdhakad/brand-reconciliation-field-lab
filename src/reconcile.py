"""Reconcile closed Shopify payout IDs to bank deposits, not sales to cash."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 10, 6)
TIMING_WINDOW_DAYS = 2
STATUSES = (
    "MATCHED",
    "PENDING_TIMING",
    "AMOUNT_MISMATCH",
    "DUPLICATE_BANK_ROW",
    "UNMATCHED_BANK_ROW",
)


def read_rows(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path.name}: missing required columns")
        rows = list(reader)
    if any(not all(row.get(field, "").strip() for field in required) for row in rows):
        raise ValueError(f"{path.name}: blank required value")
    return rows


def money(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid USD amount: {value}") from exc
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise ValueError(f"invalid USD amount: {value}")
    return amount


def reconcile(payouts: list[dict[str, str]], deposits: list[dict[str, str]], as_of: date) -> list[dict[str, str]]:
    payout_ids: set[str] = set()
    bank_ids: set[str] = set()
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in deposits:
        transaction_id = row["bank_transaction_id"]
        if transaction_id in bank_ids:
            raise ValueError(f"duplicate bank transaction ID: {transaction_id}")
        bank_ids.add(transaction_id)
        date.fromisoformat(row["posted_at"])
        money(row["amount_usd"])
        grouped[row["payout_id"]].append(row)

    results: list[dict[str, str]] = []
    for row in payouts:
        payout_id = row["payout_id"]
        if payout_id in payout_ids:
            raise ValueError(f"duplicate payout ID: {payout_id}")
        payout_ids.add(payout_id)
        paid_at = date.fromisoformat(row["paid_at"])
        expected = money(row["net_amount_usd"])
        matches = grouped.get(payout_id, [])
        observed = sum((money(item["amount_usd"]) for item in matches), Decimal("0.00"))
        if len(matches) > 1:
            status = "DUPLICATE_BANK_ROW"
            action = "Check repeated payout mapping with finance before correcting a ledger row."
        elif len(matches) == 1 and observed == expected:
            status = "MATCHED"
            action = "No action; retain the payout-to-bank evidence."
        elif not matches and 0 <= (as_of - paid_at).days <= TIMING_WINDOW_DAYS:
            status = "PENDING_TIMING"
            action = "Check again after the settlement window; do not book a missing-cash loss yet."
        else:
            status = "AMOUNT_MISMATCH"
            action = "Ask finance for bank detail and fee or adjustment evidence; do not auto-post a correction."
        results.append({
            "payout_id": payout_id,
            "status": status,
            "expected_usd": f"{expected:.2f}",
            "observed_usd": f"{observed:.2f}",
            "difference_usd": f"{expected - observed:.2f}",
            "bank_transaction_ids": "|".join(item["bank_transaction_id"] for item in matches),
            "next_action": action,
        })

    for payout_id in sorted(grouped.keys() - payout_ids):
        matches = grouped[payout_id]
        observed = sum((money(item["amount_usd"]) for item in matches), Decimal("0.00"))
        results.append({
            "payout_id": payout_id,
            "status": "UNMATCHED_BANK_ROW",
            "expected_usd": "0.00",
            "observed_usd": f"{observed:.2f}",
            "difference_usd": f"{-observed:.2f}",
            "bank_transaction_ids": "|".join(item["bank_transaction_id"] for item in matches),
            "next_action": "Identify the bank deposit owner and source; do not attribute it to Shopify without evidence.",
        })
    return results


def build(data_dir: Path = ROOT / "data", output_dir: Path = ROOT / "artifacts", as_of: date = AS_OF) -> list[dict[str, str]]:
    payouts = read_rows(data_dir / "shopify_payouts.csv", {"payout_id", "paid_at", "net_amount_usd"})
    deposits = read_rows(data_dir / "bank_deposits.csv", {"bank_transaction_id", "posted_at", "payout_id", "amount_usd"})
    results = reconcile(payouts, deposits, as_of)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "reconciliation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, lineterminator="\n", fieldnames=list(results[0]) if results else [
            "payout_id", "status", "expected_usd", "observed_usd", "difference_usd", "bank_transaction_ids", "next_action"
        ])
        writer.writeheader()
        writer.writerows(results)
    summary = {
        "as_of": as_of.isoformat(),
        "basis": "Shopify payout net amount versus bank deposit amount by payout ID",
        "counts": {status: sum(row["status"] == status for row in results) for status in STATUSES},
        "unresolved_payout_ids": [row["payout_id"] for row in results if row["status"] != "MATCHED"],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    rows = build()
    print(f"Reconciled {len(rows)} payout/deposit groups; {sum(r['status'] == 'MATCHED' for r in rows)} matched.")
