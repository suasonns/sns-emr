# Gate 2 — Alembic Migration Checklist (Updated)

**Generated:** 2026-05-08T02:32:26Z

## Forward‑Only Rule
- Never rewrite or delete migrations.
- Fix drift with new migrations.

## Mandatory Tables / Migrations
- dx_primary_policy
- platform_features
- tenant_features (optional)
- tenants
- system_settings
- platform_announcements
- tenant_announcements
- tenant_messages
- tenant_message_files
- owner_alerts

## Permission Verification
- App DB role must have required grants on new tables.

## Verification Queries
```sql
SELECT current_database(), current_schema(), current_user;
SELECT COUNT(*) FROM system_settings;
SELECT COUNT(*) FROM dx_primary_policy;
SELECT COUNT(*) FROM platform_announcements;
SELECT COUNT(*) FROM tenant_announcements;
SELECT COUNT(*) FROM owner_alerts;
```
