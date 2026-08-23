# PEAD-001 / IM-001 Implementation Development & Verification

Purpose: implement the frozen PEAD-001 point-in-time analyst-surprise event-state construct.

IM-001 must first verify whether required data exists.

Required:

- Earnings announcement events.
- Announcement timing/session.
- Actual EPS.
- Pre-announcement analyst consensus expected EPS.
- Consensus timestamp.
- Pre-announcement price reference.
- Trading calendar.

If required data is unavailable, IM-001 must conclude:

**Implementation incomplete / blocked by missing point-in-time earnings data**

Forbidden:

- Using revised estimates.
- Using fiscal period end as announcement date.
- Treating after-close information as same-close tradable.
- Backtesting.
- Profitability claims.
- Parameter optimization.
