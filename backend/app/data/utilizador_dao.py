import psycopg2
from psycopg2 import sql
from datetime import date
from typing import Optional

from data.abstract_dao import AbstractDAO
from logic.ss_gestao.utilizador import Utilizador,Jogador,Presidente,Treinador

class UtilizadorDAO(AbstractDAO[Utilizador]):
    def __init__(self, db_config: dict):
        super().__init__("utilizadores", "id", db_config)
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        # We remove the specific columns from the base table for a cleaner design
        queries = [
            """CREATE TABLE IF NOT EXISTS utilizadores (
                id VARCHAR(50) PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                contacto VARCHAR(20) NOT NULL,
                password BYTEA NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                data_nascimento DATE NOT NULL,
                nome_emergencia VARCHAR(100),
                contacto_emergencia VARCHAR(20),
                tipo VARCHAR(20) NOT NULL
            );""",
            """CREATE TABLE IF NOT EXISTS jogadores (
                id VARCHAR(50) PRIMARY KEY REFERENCES utilizadores(id) ON DELETE CASCADE,
                posicao VARCHAR(50) NOT NULL
            );""",
            """CREATE TABLE IF NOT EXISTS treinadores (
                id VARCHAR(50) PRIMARY KEY REFERENCES utilizadores(id) ON DELETE CASCADE,
                licenca DATE NOT NULL
            );""",
            """CREATE TABLE IF NOT EXISTS presidentes (
                id VARCHAR(50) PRIMARY KEY REFERENCES utilizadores(id) ON DELETE CASCADE,
                anos_mandato INTEGER NOT NULL
            );"""
        ]
        try:
            with self.connection.cursor() as cursor:
                for q in queries:
                    cursor.execute(q)
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to initialize tables: {e}")

    def put(self, key: str, value: Utilizador) -> Optional[Utilizador]:
        old_value = self.get(key)
        tipo = value.__class__.__name__

        try:
            with self.connection.cursor() as cursor:
                # 1. Update/Insert Base Table
                upsert_base = sql.SQL("""
                    INSERT INTO utilizadores (id, nome, contacto, password, ativo, data_nascimento, nome_emergencia, contacto_emergencia, tipo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nome=EXCLUDED.nome, contacto=EXCLUDED.contacto, password=EXCLUDED.password,
                        ativo=EXCLUDED.ativo, data_nascimento=EXCLUDED.data_nascimento,
                        nome_emergencia=EXCLUDED.nome_emergencia, contacto_emergencia=EXCLUDED.contacto_emergencia, tipo=EXCLUDED.tipo
                """)
                cursor.execute(upsert_base, (key, value.nome, value.contacto, value.password, value.ativo, 
                                             value.data_nascimento, value.nome_emergencia, value.contacto_emergencia, tipo))

                # 2. Update/Insert Specific Table
                if isinstance(value, Jogador):
                    cursor.execute("INSERT INTO jogadores (id, posicao) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET posicao=EXCLUDED.posicao", (key, value.posicao))
                elif isinstance(value, Treinador):
                    cursor.execute("INSERT INTO treinadores (id, licenca) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET licenca=EXCLUDED.licenca", (key, value.licenca))
                elif isinstance(value, Presidente):
                    cursor.execute("INSERT INTO presidentes (id, anos_mandato) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET anos_mandato=EXCLUDED.anos_mandato", (key, value.anos_mandato))

            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(e)
        return old_value

    def get(self, key: str) -> Optional[Utilizador]:
        if not isinstance(key, str): return None
        
        query = """
            SELECT u.*, j.posicao, t.licenca, p.anos_mandato
            FROM utilizadores u
            LEFT JOIN jogadores j ON u.id = j.id
            LEFT JOIN treinadores t ON u.id = t.id
            LEFT JOIN presidentes p ON u.id = p.id
            WHERE u.id = %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (key,))
                record = cursor.fetchone()
                return self._decode_tuple(record) if record else None
        except psycopg2.Error as e:
            raise RuntimeError(e)

    def _decode_tuple(self, record) -> Optional[Utilizador]:
        # Indices: 0-8 (Base), 9 (posicao), 10 (licenca), 11 (anos_mandato)
        tipo = record[8]
        base_args = {
            'id': record[0], 'nome': record[1], 'contacto': record[2],
            'password': bytes(record[3]), 'ativo': record[4],
            'data_nascimento': record[5], 'nome_emergencia': record[6],
            'contacto_emergencia': record[7]
        }

        if tipo == 'Jogador': return Jogador(**base_args, posicao=record[9])
        if tipo == 'Treinador': return Treinador(**base_args, licenca=record[10])
        if tipo == 'Presidente': return Presidente(**base_args, anos_mandato=record[11])
        return Utilizador(**base_args)

    def values(self) -> list[Utilizador]:
        query = """
            SELECT u.*, j.posicao, t.licenca, p.anos_mandato
            FROM utilizadores u
            LEFT JOIN jogadores j ON u.id = j.id
            LEFT JOIN treinadores t ON u.id = t.id
            LEFT JOIN presidentes p ON u.id = p.id
        """
        results = []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                for record in cursor.fetchall():
                    results.append(self._decode_tuple(record))
        except psycopg2.Error as e:
            raise RuntimeError(e)
        return results