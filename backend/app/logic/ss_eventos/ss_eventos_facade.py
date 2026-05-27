
from logic.ss_eventos.comunicado import Comunicado
from logic.ss_eventos.evento import *

from data.comunicado_dao import ComunicadoDAO
from data.abstract_dao import AbstractDAO
from data.evento_dao import EventoDAO

from utils.utils import *

from datetime import datetime
from uuid import UUID
from typing import Optional

from logic.ss_eventos.comunicado import Comunicado
from logic.ss_eventos.evento import Evento, Treino, Jogo, Convocatoria, Presenca, Resposta
from data.comunicado_dao import ComunicadoDAO
from data.evento_dao import EventoDAO
from data.abstract_dao import AbstractDAO

class SSEventosFacade():
    def __init__(self, db_config: dict):
        self.comunicados: AbstractDAO = ComunicadoDAO(db_config)
        self.eventos: AbstractDAO = EventoDAO(db_config)

    # --- Event Management ---

    def criar_evento(self, data: dict) -> str:
        """
        Expects data: { 'tipo': 'Treino'|'Jogo', 'data_hora': iso_str, 'local': str, ... }
        """
        tipo = data.get('tipo')
        dt = datetime.fromisoformat(data.get('data_hora'))
        local = data.get('local')
        
        if tipo == 'Treino':
            # Treinos start with an empty presencas dict as per logic.ss_eventos.evento
            evento = Treino(data_hora=dt, local=local, estado="Agendado", presencas={})
        elif tipo == 'Jogo':
            evento = Jogo(
                data_hora=dt, local=local, estado="Agendado",
                adversario=data.get('adversario', 'TBD'),
                golos_favor=0, golos_contra=0,
                convocatoria=Convocatoria() # Generates new UUID/Date via default_factory
            )
        else:
            raise ValueError(f"Tipo de evento inválido: {tipo}")

        self.eventos[str(evento.id)] = evento
        return str(evento.id)

    def editar_evento(self, evento_id: str, data: dict):
        """
        Atualiza os dados de um evento existente.
        Expects data: {'data': iso_str, 'hora': str, 'local': str, 'estado': str, 'adversario': str}
        """
        from datetime import datetime, time
        from uuid import UUID

        # 1. Recuperar o evento existente através do DAO
        evento = self.eventos.get(evento_id)
        if not evento:
            raise KeyError(f"Evento {evento_id} não encontrado.")

        # 2. Atualizar os campos comuns a Treinos e Jogos
        if 'data' in data and 'hora' in data:
            data_obj = datetime.fromisoformat(data['data']).date()
            hora_obj = time.fromisoformat(data['hora'])
            evento.data_hora = datetime.combine(data_obj, hora_obj)
        
        if 'local' in data:
            evento.local = data['local']
            
        if 'estado' in data:
            evento.estado = data['estado']

        # 3. Se for um Jogo, atualizar também os atributos específicos do Jogo
        from logic.ss_eventos.evento import Jogo
        if isinstance(evento, Jogo):
            if 'adversario' in data:
                evento.adversario = data['adversario']

        # 4. Persistir a alteração de volta na Base de Dados usando o AbstractDAO
        self.eventos[evento_id] = evento

    def cancelar_evento(self, evento_id: str):
        evento = self.eventos.get(evento_id)
        if evento:
            evento.estado = "Cancelado"
            self.eventos[evento_id] = evento

    def procurar_eventos_na_data(self, data_alvo: str) -> list[Evento]:
        """Returns events for a specific day (YYYY-MM-DD)"""
        alvo = datetime.fromisoformat(data_alvo).date()
        return [e for e in self.eventos.values() if e.data_hora.date() == alvo]
    
    def listar_eventos_por_mes(self, ano: int, mes: int) -> list[Evento]:
        """
        Returns all events (Games and Training) for a specific month and year.
        """
        return [
            e for e in self.eventos.values() 
            if e.data_hora.year == ano and e.data_hora.month == mes
        ]

    # --- Logistics & Attendance ---

    def efetuar_convocatoria(self, jogo_id: str, lista_jogadores_ids: list[str]):
        """Sets the list of players for a game convocatoria[cite: 2]"""
        jogo = self.eventos.get(jogo_id)
        if not isinstance(jogo, Jogo):
            raise ValueError("Convocatórias só podem ser feitas para Jogos.")

        # Rebuild the convocatoria dict[cite: 2]
        new_convocados = {}
        for pid in lista_jogadores_ids:
            # Resposta starts as False/None until the player responds[cite: 2]
            new_convocados[pid] = Resposta(jogador=None, estado=False)
        
        jogo.convocatoria.convocados = new_convocados
        self.eventos[jogo_id] = jogo

    def registar_presencas(self, treino_id: str, presencas_data: dict[str, dict]):
        """
        Expects presencas_data: { 'id_jogador': {'presente': bool, 'nota': str} }[cite: 2]
        """
        treino = self.eventos.get(treino_id)
        if not isinstance(treino, Treino):
            raise ValueError("Presenças só podem ser registadas para Treinos.")

        for pid, info in presencas_data.items():
            p = Presenca(presente=info.get('presente', False), nota=info.get('nota', ""))
            treino.add_presenca(pid, p) # Utilizes Treino.add_presenca method[cite: 2]

        self.eventos[treino_id] = treino

    def registar_resposta_convocatoria(self, jogo_id: str, jogador_id: str, resposta: bool):
        """
        Updates the response status of a specific player for a match.
        Maps to POST /eventos/jogos/<id>/resposta.
        """
        # 1. Retrieve the game from the DAO
        jogo = self.eventos.get(jogo_id)
        
        if not isinstance(jogo, Jogo):
            raise ValueError(f"Evento {jogo_id} não é um Jogo ou não existe.")

        # 2. Check if the player is actually in the convocatoria
        if jogador_id not in jogo.convocatoria.convocados:
            raise KeyError(f"Jogador {jogador_id} não foi convocado para este jogo.")

        # 3. Update the state (logic.ss_eventos.evento handles internal dict update)
        jogo.registar_resposta(jogador_id, resposta)

        # 4. Persist the change back to the database[cite: 1]
        # This will trigger the EventoDAO to update the 'respostas' table
        self.eventos[jogo_id] = jogo

    # --- Comunicados ---

    def get_comunicados(self) -> list[Comunicado]:
        # Returns all Comunicados from the DAO[cite: 2]
        return self.comunicados.values()

    def publicar_comunicado(self,dados:dict):
        try:
            titulo=dados.get('titulo',""),
            data=datetime.fromisoformat(dados.get('data',utc_now_iso())),
            corpo=dados.get('corpo',"")

            if titulo == "":
                raise ValueError(f"Titulo em falta")

            if corpo == "":
                raise ValueError(f"Corpo do comunicado em falta")

            p = Comunicado(
                titulo=titulo,
                data=data,
                corpo=corpo,
            )

            self.comunicados.put(p.id,p)
            return True
        except Exception as e:
            print(e)