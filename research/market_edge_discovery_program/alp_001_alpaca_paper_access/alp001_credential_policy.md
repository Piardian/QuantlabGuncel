# ALP-001 Credential Policy

## Credential Storage

Credentials must not be written into:

- Markdown reports
- CSV files
- JSON manifests
- Git-tracked files
- chat logs
- screenshots

## Accepted Local Mechanisms

Use one of:

- environment variables
- local untracked `.env`
- OS secret manager
- secure local credential vault

## Expected Environment Variables

Preferred names:

```text
APCA_API_KEY_ID
APCA_API_SECRET_KEY
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

Alternative names may be supported later, but must be explicitly registered before use.

## Credential Recording Rule

Reports may record only:

```text
credential_available = YES / NO
authentication_method = API_KEY
endpoint = PAPER
```

Never record actual secrets.

