# Database lifecycle

`init/001_init.sql` is the complete **fresh-database baseline**, reconciled with
the production product tables on 2026-09-06. It contains schema only, without
production jobs, credentials, n8n internals or unrelated MCP integration tables.
The n8n schema is created empty; n8n manages its own migrations.

Docker executes this baseline only for a new PostgreSQL volume. Never run it
against an existing production database. It does not replace a production backup.

Migrations `002` through both historical `021` files are already incorporated in
the baseline. Do **not** replay those historical migrations after initialization:
some restore older constraints and the historical chain is incomplete. For an
existing database, inspect the actual schema and apply only the reviewed upgrade
migration for that deployment. Future changes must update the baseline and add a
separately numbered upgrade migration (start at `022`).

Run `python3 tests/integration/fresh_database_contract.py` from the repository
root. This starts and removes an isolated local PostgreSQL 18 container, imports
the baseline, prepares every product workflow SQL statement, and exercises the
staged job/scene/visual schema. It never connects to production.
