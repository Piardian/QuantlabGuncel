# ALP-001 Security Incident — Credential Exposure

## Incident

`ALP001-SEC-001`

## Description

Alpaca Paper credentials were pasted into the chat. The agent will not write those credentials into repository files, reports, manifests, command history, or logs.

## Risk

The exposed credentials should be treated as compromised.

## Recommended Owner Action

Revoke the exposed Alpaca Paper key and create a new Paper key.

## Current Agent Action

The repository now contains:

- `.gitignore` entries for `.env` and secret files
- `.env.example` with placeholder values only
- `scripts/alpaca_verify_account.py`, which reads credentials from local environment or an untracked `.env`

## Status

`OPEN_OWNER_ROTATION_RECOMMENDED`

