# Copyright 2026 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.db import connection


def get_row_count(table_name):
    cursor = connection.cursor()
    query = cursor.execute('SELECT COUNT(*) FROM "{table_name}"'
                           .format(table_name=table_name))
    return query.fetchone()[0]


def get_row_count_where_status_equals(table_name, status):
    cursor = connection.cursor()
    query = cursor.execute('''SELECT COUNT(*)
                              FROM "{table_name}"
                              WHERE status = '{status}'
                           '''
                           .format(table_name=table_name,
                                   status=status))
    return query.fetchone()[0]
