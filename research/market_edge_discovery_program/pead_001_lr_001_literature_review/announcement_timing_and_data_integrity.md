# Announcement Timing And Data Integrity

Announcement timing is central to PEAD.

Required fields for safe implementation:

- Announcement date.
- Announcement timestamp or session classification.
- Before-market-open, during-market, or after-market-close flag.
- Actual reported earnings.
- Point-in-time expectation or time-series model input.
- Tradable first price after information availability.

Critical look-ahead risks:

- Using same-day close for after-close announcements.
- Using post-announcement analyst consensus.
- Using restated accounting data.
- Treating preliminary and final earnings inconsistently.
- Ignoring delisted securities.

CD-001 must explicitly define the first tradable observation after the announcement.

If timestamp data is unavailable, the construct should use a conservative next-session timing convention or remain limited in scope.
