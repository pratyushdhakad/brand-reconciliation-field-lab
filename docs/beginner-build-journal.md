# Day 1 build journal: from messy question to exception queue

This document explains the actual small build in plain language. All sample data is invented.

1. **Started with the customer's decision.** A finance lead needs to know which Shopify payouts can be considered matched to bank cash. That is narrower and more useful than “build a finance dashboard.”
2. **Chose the comparison carefully.** Gross sales and bank deposits are different things. The payout file already expresses the processor's net cash instruction, so I matched that to bank deposits using the payout ID.
3. **Made two tiny source files.** One CSV stands in for Shopify payouts; the other stands in for bank deposits. I included one clean match, a repeated payout mapping, a $20 gap, a recent payout with no bank row, and a bank row with no known payout.
4. **Wrote a Python script.** It reads both files, rejects bad identifiers and amounts, groups bank rows by payout ID, and assigns an explainable status. It uses `Decimal` so money is not rounded by binary floating-point math.
5. **Generated handoff files.** The CSV gives finance a row-by-row queue with a next action. The JSON gives an automated workflow a small summary. A fixed as-of date means two people running it get the same result.
6. **Added tests and CI.** Seven automated tests cover each exception, exact dollars, timing aging, invalid source data, and repeatability. CI (continuous integration) means GitHub runs those checks whenever code is pushed; it flags a problem before someone relies on the output.
7. **Wrote a mock kickoff.** The meeting agenda asks what decision matters, which extracts are authoritative, and who owns each open item. The script does not pretend to have met a customer or resolved the unexplained $20.

GitHub basics for this project: a **repository** is the folder and its history; a **commit** is a saved checkpoint; `git push` sends committed checkpoints to GitHub; a **workflow** is an automated check described in `.github/workflows/ci.yml`; and an **artifact** here is the CSV or JSON the script produces, not proof of a live deployment. The next checkpoint should be small too: verify payout mapping and retain evidence before automating decisions.
