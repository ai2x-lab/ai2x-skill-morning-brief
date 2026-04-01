# Upgrade path

## v1 -> v2
1. Keep running v1 in production
2. Run `python3 v2/migrations/migrate_v1_to_v2.py`
3. Review `v2/profiles/user.json`
4. Switch runner to v2 when ready

## Non-overwrite rule
- Do NOT overwrite: `v2/profiles/user.json`
- Safe to overwrite: `v2/core/*`, `v2/scripts/*`, `v2/references/*`
