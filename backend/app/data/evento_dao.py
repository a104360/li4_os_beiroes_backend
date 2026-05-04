import psycopg2
from psycopg2 import sql
from uuid import UUID
from datetime import datetime
from typing import Optional
import json

from data.abstract_dao import AbstractDAO
from logic.ss_eventos.evento import Evento, Treino, Jogo, Convocatoria, Presenca, Resposta

class EventoDAO(AbstractDAO[Evento]):
    def __init__(self, db_config: dict):
        super().__init__("eventos", "id", db_config)
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        queries = [
            """CREATE TABLE IF NOT EXISTS eventos (
                id UUID PRIMARY KEY,
                data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
                local VARCHAR(255) NOT NULL,
                estado VARCHAR(50) NOT NULL,
                tipo VARCHAR(20) NOT NULL
            );""",
            """CREATE TABLE IF NOT EXISTS treinos (
                id UUID PRIMARY KEY REFERENCES eventos(id) ON DELETE CASCADE,
                presencas JSONB NOT NULL DEFAULT '{}'
            );""",
            """CREATE TABLE IF NOT EXISTS convocatorias (
                id UUID PRIMARY KEY,
                data TIMESTAMP NOT NULL
            );""",
            """CREATE TABLE IF NOT EXISTS jogos (
                id UUID PRIMARY KEY REFERENCES eventos(id) ON DELETE CASCADE,
                adversario VARCHAR(255) NOT NULL,
                golos_favor INTEGER DEFAULT 0,
                golos_contra INTEGER DEFAULT 0,
                id_convocatoria UUID REFERENCES convocatorias(id) ON DELETE SET NULL
            );""",
            """CREATE TABLE IF NOT EXISTS respostas (
                id_convocatoria UUID REFERENCES convocatorias(id) ON DELETE CASCADE,
                id_jogador VARCHAR(50) REFERENCES utilizadores(id) ON DELETE CASCADE,
                estado BOOLEAN NOT NULL,
                PRIMARY KEY (id_convocatoria, id_jogador)
            );"""
        ]
        try:
            with self.connection.cursor() as cursor:
                for q in queries:
                    cursor.execute(q)
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to initialize evento tables: {e}")

    def put(self, key: str, value: Evento) -> Optional[Evento]:
        old_value = self.get(key)
        tipo = value.__class__.__name__

        try:
            with self.connection.cursor() as cursor:
                # 1. Base Evento Table
                cursor.execute("""
                    INSERT INTO eventos (id, data_hora, local, estado, tipo)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        data_hora=EXCLUDED.data_hora, local=EXCLUDED.local, 
                        estado=EXCLUDED.estado, tipo=EXCLUDED.tipo
                """, (str(value.id), value.data_hora, value.local, value.estado, tipo))

                # 2. Specialized Logic
                if isinstance(value, Treino):
                    presencas_data = {k: {"presente": v.presente, "nota": v.nota} 
                                     for k, v in value.presencas.items()}
                    cursor.execute("""
                        INSERT INTO treinos (id, presencas) VALUES (%s, %s)
                        ON CONFLICT (id) DO UPDATE SET presencas=EXCLUDED.presencas
                    """, (str(value.id), json.dumps(presencas_data)))

                elif isinstance(value, Jogo):
                    # Save Convocatoria
                    cursor.execute("""
                        INSERT INTO convocatorias (id, data) VALUES (%s, %s)
                        ON CONFLICT (id) DO UPDATE SET data=EXCLUDED.data
                    """, (str(value.convocatoria.uuid), value.convocatoria.data))

                    # Save Respostas (Convocados)
                    for jogador_id, resp in value.convocatoria.convocados.items():
                        cursor.execute("""
                            INSERT INTO respostas (id_convocatoria, id_jogador, estado)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (id_convocatoria, id_jogador) DO UPDATE SET estado=EXCLUDED.estado
                        """, (str(value.convocatoria.uuid), jogador_id, resp.estado))

                    # Save Jogo
                    cursor.execute("""
                        INSERT INTO jogos (id, adversario, golos_favor, golos_contra, id_convocatoria)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET 
                            adversario=EXCLUDED.adversario, golos_favor=EXCLUDED.golos_favor,
                            golos_contra=EXCLUDED.golos_contra, id_convocatoria=EXCLUDED.id_convocatoria
                    """, (str(value.id), value.adversario, value.golos_favor, value.golos_contra, str(value.convocatoria.uuid)))

            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Error in put: {e}")
        return old_value

    def get(self, key: str) -> Optional[Evento]:
        query = """
            SELECT e.id, e.data_hora, e.local, e.estado, e.tipo, 
                   t.presencas, 
                   j.adversario, j.golos_favor, j.golos_contra, 
                   c.id, c.data
            FROM eventos e
            LEFT JOIN treinos t ON e.id = t.id
            LEFT JOIN jogos j ON e.id = j.id
            LEFT JOIN convocatorias c ON j.id_convocatoria = c.id
            WHERE e.id = %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (key,))
                record = cursor.fetchone()
                if not record: return None
                
                # Fetch Respostas separately if it is a Jogo
                respostas = {}
                if record[4] == 'Jogo' and record[9]:
                    cursor.execute("SELECT id_jogador, estado FROM respostas WHERE id_convocatoria = %s", (str(record[9]),))
                    for rid, restado in cursor.fetchall():
                        respostas[rid] = Resposta(jogador=None, estado=restado) # Note: ID only, as per logic.ss_eventos
                
                return self._decode_tuple(record, respostas)
        except psycopg2.Error as e:
            raise RuntimeError(e)

    def _decode_tuple(self, record, respostas=None) -> Optional[Evento]:
        tipo = record[4]
        base_args = {'id': record[0], 'data_hora': record[1], 'local': record[2], 'estado': record[3]}

        if tipo == 'Treino':
            presencas_raw = record[5] or {}
            presencas = {k: Presenca(presente=v['presente'], nota=v['nota']) for k, v in presencas_raw.items()}
            return Treino(**base_args, presencas=presencas)
        
        elif tipo == 'Jogo':
            conv = Convocatoria(
                uuid=record[9],
                data=record[10],
                convocados=respostas or {}
            )
            return Jogo(**base_args, adversario=record[6], golos_favor=record[7], golos_contra=record[8], convocatoria=conv)
        return None

    def values(self) -> list[Evento]:
        # We reuse the get logic internally to ensure responses are populated correctly
        keys = list(self.keys())
        return [self.get(k) for k in keys]