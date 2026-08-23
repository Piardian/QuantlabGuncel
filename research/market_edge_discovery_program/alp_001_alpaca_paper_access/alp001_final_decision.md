# ALP-001 Final Decision

Program:
ALP-001 Alpaca Paper Access

Purpose:
Verify owner-provided Alpaca Paper access.

Paper endpoint:
https://paper-api.alpaca.markets

Credential available:
YES

Authenticated `/v2/account` request:
PASS

Account verified:
YES_ACTIVE

Alpha logic changed:
NO

Performance evaluation performed:
NO

Performance peeking detected:
NO

Scientific T0 established:
NO

Overall decision:
ALPACA_ACCESS_VERIFIED

ALP-002 authorized:
YES

EXB-001 authorized:
NO

PAPER-001 authorized:
NO

Production authorized:
NO

Authorized next action:
ALP-002 READ-ONLY INTEGRATION

Security incident:
ALP001-SEC-001 OPEN_OWNER_ROTATION_RECOMMENDED

Verification helper:
scripts/alpaca_verify_account.py

## Required Owner Action

Credentials are available locally. Continue to ALP-002 using:

```text
APCA_API_KEY_ID
APCA_API_SECRET_KEY
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

Do not paste keys into reports or chat.

If using local `.env`, copy `.env.example` to `.env`, fill values locally, and keep `.env` untracked.
