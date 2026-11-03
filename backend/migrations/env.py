from alembic import context
import models  # noqa: F401 — register mapped tables before autogeneration
from database import Base, configured_url, engine_for

config = context.config
if context.is_offline_mode():
    context.configure(url=configured_url(), target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine_for(configured_url()).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
