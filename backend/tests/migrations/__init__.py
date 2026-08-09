"""Migration testing package.

Verifies the Alembic revision graph: forward/rollback compatibility, linear
chain, and schema-vs-model drift detection. Runs against a scratch MySQL schema
(`codecoach_migration_test`) independent of the main test database.
"""
