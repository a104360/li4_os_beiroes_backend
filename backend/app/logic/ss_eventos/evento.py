
from datetime import datetime
from uuid import uuid4,UUID
from dataclasses import dataclass,field
from logic.ss_gestao.utilizador import Jogador
from utils.utils import utc_now_datetime,utc_now_iso

@dataclass
class Presenca:
    presente: bool = False
    nota: str = ""

@dataclass
class Resposta:
    jogador: Jogador
    estado:bool


@dataclass
class Convocatoria:
   uuid : str = field(default_factory=lambda: str(uuid4()))
   data : datetime = field(default_factory=utc_now_datetime)
   convocados : dict[str,Resposta] = field(default_factory=dict)

@dataclass
class Evento:
    data_hora : datetime
    local : str
    estado : str
    id : str = field(default_factory=lambda: str(uuid4()))

@dataclass
class Treino(Evento):
    presencas : dict[str,Presenca] = field(default_factory=dict)

    def add_presenca(self,id_jogador:str,p:Presenca) -> None:
        self.presencas[id_jogador] = p

    def get_presencas(self) -> dict[str,Presenca]:
        return dict(self.presencas)


@dataclass
class Jogo(Evento):
    adversario:str = ""
    golos_favor:int = -1
    golos_contra:int = -1
    convocatoria:Convocatoria = field(default_factory=Convocatoria)


    def set_resultados(self,favor:int,contra:int)->None:
        self.golos_favor = favor
        self.golos_contra = contra

    def convocar_jogadores(self,jogadores : list[Jogador]):
        self.convocatoria = dict()
        for j in jogadores:
            self.convocatoria.convocados[j.id] = Presenca()

    def registar_resposta(self,id_jogador:str,r:bool):
        self.convocatoria.convocados[id_jogador].estado = r