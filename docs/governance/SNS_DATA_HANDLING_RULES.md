# SNS Data Handling Rules

**Status:** Active operational supplement
**Authority:** Expands constitutional safeguards. When stricter organizational, legal, contractual, or regulatory controls apply, the stricter applicable control governs.

## Default

Use synthetic data for source code, committed fixtures, demos, screenshots, prompts, test logs, tickets, and public or shared previews.

## Historical patient data

Historical patient data may be used only with documented organizational authorization, a defined purpose, minimum necessary records and fields, an approved isolated environment, a dedicated authorized account, strong authentication, least privilege, encryption, audit logging, protected backups, restricted export/screenshot/print/share behavior, rollback and recovery, retention, cleanup, and secure disposal.

Sole-developer access does not remove privacy, confidentiality, security, audit, or minimum-necessary duties.

## Prohibitions

Do not place identifiable patient data in:

- source code or committed fixtures
- pull requests or issue trackers
- external AI prompts or services without explicit authorization
- public screenshots or demos
- ordinary logs
- unsecured local files
- general training environments

Never place credentials, tokens, private keys, connection strings, or production secrets in prompts or tracked files.

## Testing record

When authorized historical-data testing occurs, record authorization reference, purpose, approved environment and user, minimum data, expected result, actions, result, rollback, cleanup, retention deadline, and incident path without copying unnecessary identifiers.

## Incident response

On suspected exposure, unauthorized access, cross-patient or cross-tenant data, or improper transfer: stop, preserve necessary evidence, minimize identifiers in incident records, follow the SNS incident process, and do not resume until authorized.
