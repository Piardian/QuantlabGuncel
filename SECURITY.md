# Security Policy

## Supported versions

Only the current public development branch is considered supported.

## Reporting

Do not publish API keys, credentials, private data, or exploitable security details in public issues.

If GitHub private vulnerability reporting is enabled, use it. Otherwise, contact the repository owner through GitHub with reproducible details and without exposing secrets.

## Secret handling

Never commit API keys, credentials, private datasets, or sensitive generated artifacts. If a secret is exposed, rotate or revoke it immediately; removing the file in a later commit does not remove it from Git history.
