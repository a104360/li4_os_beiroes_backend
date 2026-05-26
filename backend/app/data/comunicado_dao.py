import psycopg2
from psycopg2 import sql
from uuid import UUID,uuid4
from datetime import datetime
from typing import Optional
from data.abstract_dao import AbstractDAO
from logic.ss_eventos.comunicado import Comunicado

class ComunicadoDAO(AbstractDAO[Comunicado]):
    def __init__(self, db_config: dict):
        # Table name: comunicados, Primary Key: id
        super().__init__("comunicados", "id", db_config)
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        query = """
            CREATE TABLE IF NOT EXISTS comunicados (
                id VARCHAR(50) PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                data TIMESTAMP WITH TIME ZONE NOT NULL,
                corpo TEXT NOT NULL
            );
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to initialize comunicados table: {e}")

    def containsValue(self, value: object) -> bool:
        if isinstance(value, Comunicado):
            return value.id in self
        return False

    def put(self, key: str, value: Comunicado) -> Optional[Comunicado]:
        """
        Note: key is usually str(value.id). 
        PostgreSQL will accept the string representation for the UUID column.
        """
        old_value = self.get(key)

        query = sql.SQL("""
            INSERT INTO {} (id, titulo, data, corpo)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                titulo = EXCLUDED.titulo,
                data = EXCLUDED.data,
                corpo = EXCLUDED.corpo
        """).format(sql.Identifier(self._table_name))

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (
                    # str(value.id), 
                    str(uuid4()),
                    value.titulo, 
                    value.data, 
                    value.corpo
                ))
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(e)
            
        return old_value

    def _decode_tuple(self, record) -> Optional[Comunicado]:
        if not record:
            return None
        
        # record[0]: id (UUID/str), record[1]: titulo, record[2]: data, record[3]: corpo
        return Comunicado(
            id=record[0], # if not isinstance(record[0], str) else record[0],
            titulo=record[1],
            data=record[2],
            corpo=record[3]
        )