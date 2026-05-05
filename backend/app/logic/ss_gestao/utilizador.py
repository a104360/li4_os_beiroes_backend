
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

    def to_dict(self):
        d = self.__dict__.copy()
        if isinstance(d.get('password'), bytes):
            d['password'] = d['password'].hex()
        if isinstance(d.get('data_nascimento'), date):
            d['data_nascimento'] = d['data_nascimento'].isoformat()
        return d

@dataclass
class Jogador(Utilizador):
    posicao:str

@dataclass
class Treinador(Utilizador):
    licenca : date

@dataclass
class Presidente(Utilizador):
    anos_mandato:int