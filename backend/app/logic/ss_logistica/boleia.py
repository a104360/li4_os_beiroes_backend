from dataclasses import dataclass,field
from uuid import UUID,uuid4
from datetime import datetime

from logic.ss_eventos.evento import Jogo
from logic.ss_gestao.utilizador import Utilizador


@dataclass
class Viatura:
    modelo:str
    matricula:str
    lugares_totais:int
    proprietario : Utilizador = field(default_factory=Utilizador)
    id:UUID = field(default_factory=uuid4)


@dataclass
class Boleia:
    partida : datetime
    lugares_vagos : int = 0
    max_lugares: int = 0
    viatura: Viatura = field(default_factory=Viatura)
    passageiros : dict[Utilizador] = field(default_factory=Utilizador)
    jogo:Jogo = field(default_factory=Jogo)
    id:UUID = field(default_factory=uuid4)