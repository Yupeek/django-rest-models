from __future__ import unicode_literals

from django.db.backends.base.features import BaseDatabaseFeatures


class DatabaseFeatures(BaseDatabaseFeatures):
    # SQLite cannot handle us only partially reading from a cursor's result set
    # and then writing the same rows to the database in another cursor. This
    # setting ensures we always read result sets fully into memory all in one
    # go.
    can_use_chunked_reads = True
    test_db_allows_multiple_connections = True
    supports_unspecified_pk = True
    supports_timezones = False
    supports_1000_query_parameters = False
    supports_mixed_date_datetime_comparisons = False
    has_bulk_insert = True
    can_return_id_from_insert = True
    can_combine_inserts_with_and_without_auto_increment_pk = False
    supports_foreign_keys = True
    supports_column_check_constraints = False
    autocommits_when_autocommit_is_off = False
    can_introspect_decimal_field = False
    can_introspect_positive_integer_field = True
    can_introspect_small_integer_field = True
    supports_transactions = False
    atomic_transactions = False
    can_rollback_ddl = False
    supports_paramstyle_pyformat = False
    supports_sequence_reset = False
    has_select_for_update_skip_locked = False

    uses_savepoints = False

    can_release_savepoints = False
    can_share_in_memory_db = False
    supports_stddev = False

    has_zoneinfo_database = False
