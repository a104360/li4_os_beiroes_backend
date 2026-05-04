import psycopg2
from psycopg2 import sql
from abc import ABC, abstractmethod
from collections.abc import MutableMapping


class AbstractDAO(MutableMapping, ABC):
    def __init__(self, table_name: str, key_name: str, db_config: dict):
        """
        db_config should contain: host, database, user, password, port
        """
        self._table_name = table_name
        self._key_name = key_name
        try:
            self.connection = psycopg2.connect(**db_config)
        except psycopg2.Error as e:
            raise RuntimeError(f"Database connection failed: {e}")

    def clear(self):
        try:
            with self.connection.cursor() as cursor:
                # Use psycopg2.sql to safely inject table names
                query = sql.SQL("DELETE FROM {} WHERE TRUE").format(sql.Identifier(self._table_name))
                cursor.execute(query)
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(e)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL("SELECT {} FROM {} WHERE {} = %s").format(
                    sql.Identifier(self._key_name),
                    sql.Identifier(self._table_name),
                    sql.Identifier(self._key_name)
                )
                cursor.execute(query, (key,))
                return cursor.fetchone() is not None
        except psycopg2.Error as e:
            raise RuntimeError(e)

    def __getitem__(self, key: str):
        if not isinstance(key, str):
            return None
        
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
                    sql.Identifier(self._table_name),
                    sql.Identifier(self._key_name)
                )
                cursor.execute(query, (key,))
                row = cursor.fetchone()
                return self._decode_tuple(row) if row else None
        except psycopg2.Error as e:
            raise RuntimeError(e)

    def __setitem__(self, key: str, value):
        # In Python, __setitem__ handles the 'put' logic
        self.put(key, value)

    def __delitem__(self, key: str):
        # Logic for removing an item
        try:
            # We don't need manual auto-commit toggling as much in Python, 
            # but we use transactions via commit/rollback
            val = self.get(key)
            if val is None:
                raise KeyError(key)

            with self.connection.cursor() as cursor:
                query = sql.SQL("DELETE FROM {} WHERE {} = %s").format(
                    sql.Identifier(self._table_name),
                    sql.Identifier(self._key_name)
                )
                cursor.execute(query, (key,))
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(e)

    def __len__(self) -> int:
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(self._table_name))
                cursor.execute(query)
                return cursor.fetchone()[0]
        except psycopg2.Error as e:
            raise RuntimeError(e)

    def __iter__(self):
        # Corresponds to keySet()
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL("SELECT {} FROM {}").format(
                    sql.Identifier(self._key_name),
                    sql.Identifier(self._table_name)
                )
                cursor.execute(query)
                for row in cursor.fetchall():
                    yield row[0]
        except psycopg2.Error as e:
            raise RuntimeError(e)

    def update(self, other=None, **kwargs):
        """Python's version of putAll"""
        try:
            # Batch the operations in one transaction
            if hasattr(other, 'items'):
                for k, v in other.items():
                    self.put(k, v)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise RuntimeError(e)

    @abstractmethod
    def put(self, key: str, value):
        pass

    @abstractmethod
    def _decode_tuple(self, record):
        """Converts a database row (tuple) into the object V"""
        pass