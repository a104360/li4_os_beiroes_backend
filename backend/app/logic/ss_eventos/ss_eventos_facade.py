
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
        evento = self.eventos.get(evento_id)
        if not evento:
            raise KeyError(f"Evento {evento_id} não encontrado.")

        # Update common fields
        if 'data_hora' in data:
            evento.data_hora = datetime.fromisoformat(data['data_hora'])
        if 'local' in data:
            evento.local = data['local']
        if 'estado' in data:
            evento.estado = data['estado']

        # Update specific fields based on class type[cite: 2]
        if isinstance(evento, Jogo):
            if 'adversario' in data:
                evento.adversario = data['adversario']
            if 'golos_favor' in data:
                evento.golos_favor = int(data['golos_favor'])
            if 'golos_contra' in data:
                evento.golos_contra = int(data['golos_contra'])

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

    # --- Comunicados ---

    def get_comunicados(self) -> list[Comunicado]:
        # Returns all Comunicados from the DAO[cite: 2]
        return self.comunicados.values()

    def publicar_comunicado(self,dados:dict):
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