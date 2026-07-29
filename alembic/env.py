"""Alembic env — async-capable, driven by our own settings + model metadata.

Highlights:
  * `sqlalchemy.url` in alembic.ini is overridden at runtime from
    `app_base.core.settings.settings.database_url` — so `.env` controls
    the migrate target, not alembic.ini.
  * Multiple schemas are in play (`auth`, `ride`, `payment`).
    `include_schemas` makes Alembic diff those in addition to public.
  * PostGIS geography columns need geoalchemy2's renderers registered —
    `geoalchemy2.alembic_helpers` does that automatically when imported.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from geoalchemy2 import alembic_helpers  # registers GA2 renderers on import
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import Base so its metadata is populated when model modules are imported
# below. Order matters: Base must exist before the model modules are touched.
from app_base.core.database import Base  # noqa: F401
from app_base.core.settings import settings

# Force model registration — each import registers its SQLAlchemy models
# onto Base.metadata so Alembic can see them for autogenerate.
from app_base.modules.auth.infra import models as _auth_models  # noqa: F401
from app_base.modules.payment.infra import models as _payment_models  # noqa: F401
from app_base.modules.ride.infra import models as _ride_models  # noqa: F401

# Alembic Config object — provides access to alembic.ini values.
config = context.config

# Override sqlalchemy.url from our settings (case-insensitive).
# Pydantic-settings has already loaded .env if present; in tests the caller
# sets the env var and the module-level `settings` reflects it.
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Schemas managed by this project. Alembic will ignore anything outside.
INCLUDE_SCHEMAS = {"auth", "ride", "payment"}


def include_object(obj, name, type_, reflected, compare_to):
    """Restrict diff to project schemas. Indexes/constraints live under
    their parent table, which already satisfies `include_schemas`, so we
    only need to filter tables themselves (and schemas)."""
    if type_ == "table":
        return obj.schema in INCLUDE_SCHEMAS
    if type_ == "schema":
        return name in INCLUDE_SCHEMAS
    return True


def run_migrations_offline() -> None:
    """Run in 'offline' mode — emit SQL to stdout. Useful for reviewing
    the migration before executing it against a live DB."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=INCLUDE_SCHEMAS,
        include_object=include_object,
        compare_type=True,
        include_name=lambda name, type_, parent_names: True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=INCLUDE_SCHEMAS,
        include_object=include_object,
        # PostGIS uses custom types like Geography; compare them via
        # geoalchemy2's helpers instead of treating every column as "changed".
        render_as_batch=False,
        compare_type=True,
        process_revision_directives=alembic_helpers.writer,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run in 'online' mode — connect to the DB and apply migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
