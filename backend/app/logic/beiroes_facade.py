
from logic.ss_eventos.ss_eventos_facade import SSEventosFacade
from logic.ss_gestao.ss_gestao_facade import SSGestaoFacade
from logic.ss_logistica.ss_logistica_facade import SSLogisticaFacade

from typing import Optional
from logic.ss_eventos.ss_eventos_facade import SSEventosFacade
from logic.ss_gestao.ss_gestao_facade import SSGestaoFacade
from logic.ss_logistica.ss_logistica_facade import SSLogisticaFacade

# Domain model imports for type hinting
from logic.ss_gestao.utilizador import Utilizador
from logic.ss_eventos.evento import Evento
from logic.ss_eventos.comunicado import Comunicado
from logic.ss_logistica.boleia import Boleia

class BeiroesLNFacade():
    def __init__(self, db_config: dict):
        self.gestao = SSGestaoFacade(db_config)
        self.eventos = SSEventosFacade(db_config)
        self.logistica = SSLogisticaFacade(db_config)

    # ------------------ Gestão ------------------
    # Delegated to SSGestaoFacade

    def autenticar(self, contacto: str, password_hash: bytes) -> Optional[Utilizador]:
        return self.gestao.autenticar(contacto, password_hash)
    
    def registar_utilizador(self, data: dict):
        self.gestao.registar_utilizador(data)
    
    def procurar_utilizador(self, user_id: str) -> Optional[Utilizador]:
        return self.gestao.procurar_utilizador(user_id)
    
    def editar_utilizador(self, user_id: str, data: dict):
        self.gestao.editar_utilizador(user_id, data)
    
    def desativar_utilizador(self, user_id: str):
        self.gestao.desativar_utilizador(user_id)
    

    # ------------------ Eventos ------------------
    # Delegated to SSEventosFacade

    def criar_evento(self, data: dict) -> str:
        return self.eventos.criar_evento(data)
    
    def editar_evento(self, evento_id: str, data: dict):
        self.eventos.editar_evento(evento_id, data)
    
    def cancelar_evento(self, evento_id: str):
        self.eventos.cancelar_evento(evento_id)
    
    def procurar_eventos_na_data(self, data_alvo: str) -> list[Evento]:
        return self.eventos.procurar_eventos_na_data(data_alvo)
        
    def listar_eventos_por_mes(self, ano: int, mes: int) -> list[Evento]:
        return self.eventos.listar_eventos_por_mes(ano, mes)
    
    def efetuar_convocatoria(self, jogo_id: str, lista_jogadores_ids: list[str]):
        self.eventos.efetuar_convocatoria(jogo_id, lista_jogadores_ids)
    
    def registar_presencas(self, treino_id: str, presencas_data: dict[str, dict]):
        self.eventos.registar_presencas(treino_id, presencas_data)

    def registar_resposta_convocatoria(self, jogo_id: str, jogador_id: str, resposta: bool):
        self.eventos.registar_resposta_convocatoria(jogo_id, jogador_id, resposta)
    
    def get_comunicados(self) -> list[Comunicado]:
        return self.eventos.get_comunicados()
    
    def publicar_comunicado(self, dados: dict):
        self.eventos.publicar_comunicado(dados)
    

    # ------------------ Boleias (Logística) ------------------
    # Delegated to SSLogisticaFacade[cite: 2, 3]

    def disponibilizar_boleias(self, data: dict) -> str:
        return self.logistica.disponibilizar_boleias(data)
    
    def editar_lugares(self, boleia_id: str, novos_lugares: int):
        self.logistica.editar_lugares(boleia_id, novos_lugares)
    
    def cancelar_boleia(self, boleia_id: str):
        self.logistica.cancelar_boleia(boleia_id)
    
    def reservar_lugar(self, boleia_id: str, utilizador: Utilizador):
        self.logistica.reservar_lugar(boleia_id, utilizador)
    
    def cancelar_reserva(self, boleia_id: str, user_id: str):
        self.logistica.cancelar_reserva(boleia_id, user_id)
    
    def consultar_boleias_de_jogo(self, jogo_id: str) -> list[Boleia]:
        return self.logistica.consultar_boleias_de_jogo(jogo_id)
    
    def registar_viatura(self, data: dict):
        self.logistica.registar_viatura(data)

    def get_viaturas(self):
        return self.logistica.get_viaturas()