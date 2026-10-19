# Brand Reconciliation Field Lab

A small, synthetic Forward Deployed Engineer exercise: a consumer-brand finance lead asks, “Why don't Shopify payouts match the bank?” The first useful answer is not a dashboard. It is a trustworthy comparison at the right grain, an exception list, and a decision about who investigates what.

This is **not** a Drivepoint product, integration, customer deployment, or real brand data. It is a portfolio lab inspired by the type of problem described in a public FDE role. All names, dates, and amounts are invented.

## The decision

Can finance mark each closed Shopify payout as matched to bank cash, or does someone need to investigate? This first slice compares **payout net amount to bank deposits by payout ID**. It intentionally does **not** compare Shopify gross sales with bank cash: sales, refunds, taxes, payment fees, and settlement timing can make those different even when the books are correct.

## What the fixture shows

| Payout | Result | What a human does next |
| --- | --- | --- |
| `po-1001` | Matched | Retain evidence. |
| `po-1002` | Duplicate bank row | Confirm whether the same payout was mapped twice before correcting a ledger row. |
| `po-1003` | $20 short | Request bank detail and adjustment evidence; do not invent the cause. |
| `po-1004` | Pending timing | Recheck after the two-day window. |
| `po-9999` | Bank-only row | Identify its true source; do not attribute it to Shopify. |

## Run it

Requires Python 3.11+ and only the standard library.

```bash
make test
make run
```

The input CSVs live in `data/`; the generated `artifacts/reconciliation.csv` is the handoff queue and `artifacts/summary.json` is the machine-readable status. The as-of date and settlement window are fixed fixture settings in `src/reconcile.py`, so every run is reproducible. CI reruns tests and rejects generated-file drift.

## What this demonstrates

- Frame the operational question before coding.
- Select a comparison grain and document why another apparently obvious metric is wrong.
- Validate identifiers and money before producing a result.
- Separate a timing exception from a confirmed amount mismatch.
- Give each exception an owner-oriented next action without auto-posting accounting changes.
- Leave a written [mock kickoff and handoff](docs/kickoff-and-handoff.md) and a [beginner build journal](docs/beginner-build-journal.md).

## Boundaries and next slice

This is a deterministic, five-group teaching fixture, not a production close. It has no live Shopify or bank connector, no access control, no real customer, no accounting approval, and no claim that the duplicate is truly a duplicate deposit rather than a bad mapping. The next increment should add a mapping review and evidence trail for payout-to-bank ownership before extending to order/refund or SKU-level revenue questions.
