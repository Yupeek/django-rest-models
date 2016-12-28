

from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def do_nothing(*args, **kwargs):  # pragma: no cover
    pass


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    alter_index_together = do_nothing
    column_sql = do_nothing
    alter_db_tablespace = do_nothing
    execute = do_nothing
    alter_db_table = do_nothing
    create_model = do_nothing
    skip_default = do_nothing
    alter_field = do_nothing
    alter_unique_together = do_nothing
    remove_field = do_nothing
    effective_default = do_nothing
    add_field = do_nothing
    prepare_default = do_nothing
    delete_model = do_nothing
    quote_name = do_nothing
    quote_value = do_nothing
