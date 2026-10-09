# zabmap_api

## Tests

```sh
uv run pytest
```

The tests live in `tests/` and don't need a database. Known bugs are written as
the behaviour we want and marked `xfail(strict=True)`, so they show up as
"xfailed". Once a bug is fixed, its test starts passing, and pytest fails the run
so the marker gets removed.

## Database migrations

Schema for the **internal** DB (`Host`, `Filesystem`, `MetaData`) is managed with
[peewee-migrate](https://github.com/klen/peewee-migrate). The source DB
(`ZfsSnapshots`) is read-only and owned by upstream tooling, so it is never migrated.

Migration files live in `src/zabmap_api/migrations/`. The applied-migration log is
stored in a `migratehistory` table in the internal DB. The same `FLASK_DB_*`
environment variables the app uses point the migrator at the right database.

### Commands

```sh
zabmap_migrate list                # show applied + pending migrations
zabmap_migrate migrate             # apply all pending migrations
zabmap_migrate migrate 002_relax   # apply up to (and including) a migration
zabmap_migrate rollback            # roll back the most recently applied migration
zabmap_migrate fake 001_initial    # mark applied WITHOUT running it (see below)
zabmap_migrate create my_change    # new empty migration
zabmap_migrate create my_change -a # new auto-generated migration (diffs zabmap_api.db)
```

### Fresh database

Just run every migration:

```sh
zabmap_migrate migrate
```

### Adopting migrations on the EXISTING production database (one-time)

The production tables already exist and predate migrations, so `001_initial`
(which would `CREATE TABLE`) must be recorded as applied **without** running it,
then the real fixes applied on top:

```sh
zabmap_migrate fake 001_initial    # tables already exist — record, don't create
zabmap_migrate migrate             # runs 002_relax_not_null, which fixes the NOT NULL crash
```

`002_relax_not_null` drops the `NOT NULL` constraints on the columns the scheduler
leaves unset on insert (`host.snapshots_in_sync`, etc.). `DROP NOT NULL` is
idempotent, so this is safe regardless of each column's current state.

### Adding a schema change later

1. Edit the models in `src/zabmap_api/db.py`.
2. Generate a migration: `zabmap_migrate create <name> -a`
3. Review the generated file in `src/zabmap_api/migrations/`.
4. Apply it: `zabmap_migrate migrate`
