# ALP-001 Local Verification Instructions

## Purpose

Verify Alpaca Paper `/v2/account` access without storing secrets in tracked files.

## Setup

Copy:

```text
.env.example
```

to:

```text
.env
```

Then fill locally:

```text
APCA_API_BASE_URL=https://paper-api.alpaca.markets
APCA_API_KEY_ID=<paper key id>
APCA_API_SECRET_KEY=<paper secret key>
```

`.env` is ignored by `.gitignore`.

## Run

```powershell
.\.venv\Scripts\python.exe scripts\alpaca_verify_account.py
```

## PASS Output

The script should return:

```json
{
  "status": "PASS",
  "account_id_present": true
}
```

It will not print API keys or secrets.

## Current Verified State

`NOT_READY_NO_LOCAL_CREDENTIAL`

