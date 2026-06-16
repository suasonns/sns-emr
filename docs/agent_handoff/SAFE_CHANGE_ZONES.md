# Safe vs Unsafe Change Zones

## ✅ Safe
- New task types
- New endpoints
- New audit findings
- New tables (with migrations)
- New partial indexes

## ⚠️ Requires Review
- Task engine logic
- Admission authorization
- Benefit period linking
- SOC handling

## ❌ Forbidden Without Compliance Review
- Removing uniqueness constraints
- Changing SOC semantics
- Weakening audit behavior
