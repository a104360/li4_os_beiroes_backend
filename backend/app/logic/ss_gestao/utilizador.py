
from dataclasses import dataclass
from datetime import date

@dataclass
class Utilizador:
    id:str
    nome:str
    contacto:str
    password:bytes
    ativo:bool
    data_nascimento:date
    nome_emergencia:str
    contacto_emergencia:str

    def validar_password(self,password_hash:bytes) -> bool:
        pass

@dataclass
class Jogador(Utilizador):
    posicao:str

@dataclass
class Treinador(Utilizador):
    licenca : date

class Presidente(Utilizador):
    anos_mandato:int