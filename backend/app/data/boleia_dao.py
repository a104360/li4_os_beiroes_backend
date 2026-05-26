import psycopg2
from psycopg2 import sql
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict

from data.abstract_dao import AbstractDAO

from logic.ss_eventos.evento import Jogo
from logic.ss_gestao.utilizador import Utilizador
from logic.ss_logistica.boleia import Viatura, Boleia 

class BoleiaDAO(AbstractDAO[Boleia]):
    def __init__(self, db_config: dict):
        super().__init__("boleias", "id", db_config)
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        queries = [
            """CREATE TABLE IF NOT EXISTS viaturas (
                id VARCHAR(50) PRIMARY KEY,
                modelo VARCHAR(100) NOT NULL,
                matricula VARCHAR(20) UNIQUE NOT NULL,
                lugares_totais INTEGER NOT NULL,
                id_proprietario VARCHAR(50) REFERENCES utilizadores(id)
            );""",
            """CREATE TABLE IF NOT EXISTS boleias (
                id VARCHAR(50) PRIMARY KEY,
                partida TIMESTAMP WITH TIME ZONE NOT NULL,
                lugares_vagos INTEGER NOT NULL,
                max_lugares INTEGER NOT NULL,
                id_viatura VARCHAR(50) REFERENCES viaturas(id),
                id_jogo VARCHAR(50) REFERENCES eventos(id) ON DELETE CASCADE
            );""",
            """CREATE TABLE IF NOT EXISTS boleia_passageiros (
                id_boleia VARCHAR(50) REFERENCES boleias(id) ON DELETE CASCADE,
                id_utilizador VARCHAR(50) REFERENCES utilizadores(id) ON DELETE CASCADE,
                PRIMARY KEY (id_boleia, id_utilizador)
            );"""
        ]
        try:
            with self.connection.cursor() as cursor:
                for q in queries:
                    cursor.execute(q)
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to initialize logistica tables: {e}")

    # --- Memory Loading Method ---

    def load_viaturas_to_memory(self) -> Dict[str, Viatura]:
        """Loads all Viaturas into a dictionary keyed by their ID string."""
        viaturas = {}
        query = """
            SELECT v.*,u.nome 
            FROM viaturas v 
            JOIN utilizadores u 
            ON v.id_proprietario = u.id;
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                for row in cursor.fetchall():
                    # Note: This assumes you have a way to reconstruct the owner Utilizador
                    # For simplicity, we create a placeholder Utilizador with just the ID
                    owner = Utilizador(id=row[4], nome=row[5], contacto="", password=b"", 
                                      ativo=True, data_nascimento=None, 
                                      nome_emergencia="", contacto_emergencia="")
                    v = Viatura(id=row[0], modelo=row[1], matricula=row[2], 
                                lugares_totais=row[3], proprietario=owner)
                    viaturas[str(v.id)] = v
        except psycopg2.Error as e:
            raise RuntimeError(f"Error loading viaturas: {e}")
        return viaturas

    # --- Standard DAO Methods ---

    def put(self, key: str, value: Boleia) -> Optional[Boleia]:
        old_value = self.get(key)
        try:
            with self.connection.cursor() as cursor:
                # 1. Ensure Viatura exists
                cursor.execute("""
                    INSERT INTO viaturas (id, modelo, matricula, lugares_totais, id_proprietario)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (str(value.viatura.id), value.viatura.modelo, value.viatura.matricula, 
                      value.viatura.lugares_totais, value.viatura.proprietario.id))

                # 2. Upsert Boleia
                cursor.execute("""
                    INSERT INTO boleias (id, partida, lugares_vagos, max_lugares, id_viatura, id_jogo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        partida=EXCLUDED.partida, lugares_vagos=EXCLUDED.lugares_vagos,
                        max_lugares=EXCLUDED.max_lugares, id_viatura=EXCLUDED.id_viatura
                """, (str(value.id), value.partida, value.lugares_vagos, value.max_lugares, 
                      str(value.viatura.id), str(value.jogo.id)))

                # 3. Sync Passengers (Delete and Re-insert current set)
                cursor.execute("DELETE FROM boleia_passageiros WHERE id_boleia = %s", (str(value.id),))
                for passageiro in value.passageiros:
                    cursor.execute("""
                        INSERT INTO boleia_passageiros (id_boleia, id_utilizador) 
                        VALUES (%s, %s)
                    """, (str(value.id), passageiro.id))

            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(e)
        return old_value

    def get(self, key: str) -> Optional[Boleia]:
        query = """
            SELECT b.*, v.modelo, v.matricula, v.lugares_totais, v.id_proprietario,u.nome
            FROM boleias b
            JOIN viaturas v ON b.id_viatura = v.id
            JOIN utilizadores u ON u.id = v.id_proprietario
            WHERE b.id = %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (key,))
                row = cursor.fetchone()
                if not row: return None
                
                # Fetch Passengers
                cursor.execute("SELECT id_utilizador FROM boleia_passageiros WHERE id_boleia = %s", (key,))
                passengers = [Utilizador(id=r[0], nome="", contacto="", password=b"", 
                                         ativo=True, data_nascimento=None, 
                                         nome_emergencia="", contacto_emergencia="") 
                              for r in cursor.fetchall()]
                
                return self._decode_tuple(row, passengers)
        except psycopg2.Error as e:
            raise RuntimeError(e)
    def _decode_tuple(self, record, passengers=None) -> Optional[Boleia]:
        # Check if the record has the joined columns (length 10)
        # If not (length 6), we only have the IDs and need to handle it
        has_joined_data = len(record) >= 10

        if has_joined_data:
            viatura = Viatura(
                id=record[4], 
                modelo=record[6], 
                matricula=record[7], 
                lugares_totais=record[8], 
                proprietario=Utilizador(id=record[9], nome=record[10], contacto="", password=b"", 
                                        ativo=True, data_nascimento=None, 
                                        nome_emergencia="", contacto_emergencia="")
            )
        else:
            # Fallback: We only have the viatura ID. 
            # You might want to fetch the full Viatura from memory/DB here
            # viatura = Viatura(id=record[4], modelo="Desconhecido", matricula="??-??-??", 
            #                 lugares_totais=0, proprietario=None)
            viatura = self.load_viaturas_to_memory().get(record[4])
        
        return Boleia(
            id=record[0], partida=record[1], lugares_vagos=record[2], 
            max_lugares=record[3], viatura=viatura, 
            passageiros=passengers or [], 
            jogo=Jogo(id=record[5], data_hora=None, local="", estado="", adversario="", 
                    golos_favor=0, golos_contra=0, convocatoria=None)
        )

    def containsValue(self, value: object) -> bool:
        return isinstance(value, Boleia) and value.id in self
    
    def put_viatura(self, viatura: Viatura):
        """Inserts or updates a single Viatura in the database."""
        query = """
            INSERT INTO viaturas (id, modelo, matricula, lugares_totais, id_proprietario)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                modelo = EXCLUDED.modelo,
                matricula = EXCLUDED.matricula,
                lugares_totais = EXCLUDED.lugares_totais,
                id_proprietario = EXCLUDED.id_proprietario
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (
                    str(viatura.id), 
                    viatura.modelo, 
                    viatura.matricula, 
                    viatura.lugares_totais, 
                    viatura.proprietario.id
                ))
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Error persisting viatura: {e}")

    def put_all_viaturas(self, viaturas: Dict[str, Viatura]):
        """Persists a dictionary of Viaturas to the database in a single transaction."""
        try:
            # We use the existing connection to wrap everything in one transaction
            for v_id, viatura in viaturas.items():
                self.put_viatura(viatura)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise RuntimeError(f"Error in batch viatura persistence: {e}")
        
    def clear_viaturas(self):
        """Removes all records from the viaturas table."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM viaturas WHERE TRUE")
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to clear viaturas: {e}")

    def clear(self):
        """Overriding clear to ensure correct order of deletion within this DAO."""
        # 1. Clear junction table and rides first
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM boleia_passageiros WHERE TRUE")
                cursor.execute("DELETE FROM boleias WHERE TRUE")
                # 2. Clear viaturas
                cursor.execute("DELETE FROM viaturas WHERE TRUE")
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to clear logistics data: {e}")
        

    def get_all(self) -> list[Boleia]:
        # Query that fetches the ride along with its corresponding vehicle and owner details
        query = """
            SELECT b.*, v.modelo, v.matricula, v.lugares_totais, v.id_proprietario,u.nome
            FROM boleias b
            JOIN viaturas v ON b.id_viatura = v.id
            JOIN utilizadores u ON u.id = v.id_proprietario
            WHERE b.partida >= NOW();
        """
        boleias_list = []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    boleia_id = row[0] # b.id
                    
                    # Fetch all passengers registered for this specific ride
                    cursor.execute(
                        "SELECT bp.id_utilizador,u.nome FROM boleia_passageiros bp JOIN utilizadores u ON bp.id_utilizador = u.id WHERE id_boleia = %s", 
                        (boleia_id,)
                    )
                    passengers = [
                        Utilizador(
                            id=r[0], nome=r[1], contacto="", password=b"", 
                            ativo=True, data_nascimento=None, 
                            nome_emergencia="", contacto_emergencia=""
                        ) 
                        for r in cursor.fetchall()
                    ]
                    
                    # Safely decode the tuple row into a fully populated Boleia object
                    boleia_obj = self._decode_tuple(row, passengers)
                    if boleia_obj:
                        boleias_list.append(boleia_obj)
                        
        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to get the future rides: {e}")
        
        return boleias_list
    
    def delete_viatura(self, id_viatura: str):
        """
        Remove uma viatura e todas as boleias/passageiros associados a ela.
        """
        try:
            with self.connection.cursor() as cursor:
                # 1. Obter os IDs das boleias que usam esta viatura
                cursor.execute("SELECT id FROM boleias WHERE id_viatura = %s", (id_viatura,))
                boleia_ids = [row[0] for row in cursor.fetchall()]

                if boleia_ids:
                    # 2. Remover os passageiros dessas boleias
                    cursor.execute(
                        sql.SQL("DELETE FROM boleia_passageiros WHERE id_boleia IN ({})").format(
                            sql.SQL(', ').join(sql.Literal(bid) for bid in boleia_ids)
                        )
                    )
                    # 3. Remover as boleias
                    cursor.execute("DELETE FROM boleias WHERE id_viatura = %s", (id_viatura,))

                # 4. Remover a viatura
                cursor.execute("DELETE FROM viaturas WHERE id = %s", (id_viatura,))
                
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao remover viatura e dependências: {e}")