# Mock customer kickoff and first handoff

This is a practice script for an invented consumer brand, not a record of a real customer meeting.

## Open the session (30 minutes)

“Today we will decide what ‘ties to the bank’ means, confirm the source owner for each number, and leave with an exception queue and named follow-ups. We will not change accounting entries during this call.”

| Time | Conversation | Output |
| --- | --- | --- |
| 0–5 min | What decision depends on this number? Daily cash view, month-end close, or sales reporting? | One explicit use case and owner. |
| 5–12 min | Which Shopify payout export, bank account, date basis, currency, and payout ID field are authoritative? | Source inventory and field map. |
| 12–20 min | Are split deposits, reserves, chargebacks, processor adjustments, or manual journal entries possible? | Exception rules to verify. |
| 20–27 min | Review one match and each open exception. What evidence would resolve them? | Owner and evidence request per exception. |
| 27–30 min | Confirm next check-in and who approves any correction. | Action list and sign-off path. |

## Minimum data access request

Ask for a read-only Shopify payouts export and read-only bank or ledger clearing-account extract covering the same currency and period. Request payout IDs, amounts, timestamps, bank transaction IDs, and documented adjustments. Keep raw data in the customer's approved environment; this repository must never receive customer financial records or credentials.

## Initial handoff queue from the synthetic fixture

| Exception | Provisional owner | Evidence request | Due/decision |
| --- | --- | --- | --- |
| `po-1002` duplicate mapping | Finance operations | Bank statement and ledger entry IDs for both rows | Decide whether one row is a mapping error; no deletion until verified. |
| `po-1003` $20 gap | Finance lead | Processor adjustment and bank deposit detail | Classify cause and approve any journal entry. |
| `po-1004` timing | Treasury/finance | Next bank posting extract | Recheck after two-day window. |
| `po-9999` bank-only | Treasury | Deposit memo and source account | Identify source before assigning revenue channel. |

The owners are role placeholders, not commitments by real people. In a real kickoff, replace each with a named owner and a calendar date.

## Acceptance criteria for a real pilot

The customer confirms source definitions and mappings; each payout has one status and evidence link; unresolved exceptions have named owners; finance approves any correction; and the result can be rerun without the FDE manually editing output files. This lab demonstrates only the first, synthetic part of that workflow.
