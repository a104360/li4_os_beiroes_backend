from datetime import datetime
from uuid import UUID
from typing import Optional

from logic.ss_logistica.boleia import Viatura, Boleia
from logic.ss_eventos.evento import Jogo
from logic.ss_gestao.utilizador import Utilizador
from data.boleia_dao import BoleiaDAO

class SSLogisticaFacade:
    def __init__(self, db_config: dict):
        self.boleias: BoleiaDAO = BoleiaDAO(db_config)
        self.viatura: dict[str, Viatura] = self.boleias.load_viaturas_to_memory()

    def disponibilizar_boleias(self, data: dict) -> str:
        """
        Creates a new ride. 
        Expects: {'partida': iso_str, 'viatura_id': str, 'jogo_id': str, 'max_lugares': int}
        """
        v_id = data.get('viatura_id')
        if v_id not in self.viatura:
            raise KeyError(f"Viatura {v_id} não encontrada na memória.")

        viatura = self.viatura[v_id]
        # Max places cannot exceed vehicle capacity
        max_l = min(int(data.get('max_lugares', 0)), viatura.lugares_totais)
        
        nova_boleia = Boleia(
            partida=datetime.fromisoformat(data.get('partida')),
            max_lugares=max_l,
            lugares_vagos=max_l,
            viatura=viatura,
            jogo=Jogo(id=UUID(data.get('jogo_id')), data_hora=None, local="", 
                     estado="", adversario="", golos_favor=0, golos_contra=0, convocatoria=None),
            passageiros=[]
        )
        
        self.boleias[str(nova_boleia.id)] = nova_boleia
        return str(nova_boleia.id)

    def editar_lugares(self, boleia_id: str, novos_lugares: int):
        boleia = self.boleias.get(boleia_id)
        if not boleia:
            raise KeyError(f"Boleia {boleia_id} não encontrada.")
            
        # Ensure new max isn't less than currently occupied seats[cite: 2]
        ocupados = boleia.max_lugares - boleia.lugares_vagos
        if novos_lugares < ocupados:
            raise ValueError(f"Impossível reduzir para {novos_lugares}: {ocupados} lugares já ocupados.")
            
        boleia.max_lugares = novos_lugares
        boleia.lugares_vagos = novos_lugares - ocupados
        self.boleias[boleia_id] = boleia

    def cancelar_boleia(self, boleia_id: str):
        if boleia_id in self.boleias:
            del self.boleias[boleia_id] # Uses AbstractDAO __delitem__[cite: 2]

    def reservar_lugar(self, boleia_id: str, utilizador: Utilizador):
        """Adds a passenger to the ride if places are available[cite: 2]."""
        boleia = self.boleias.get(boleia_id)
        if not boleia:
            raise KeyError("Boleia não encontrada.")
        
        if boleia.lugares_vagos <= 0:
            raise ValueError("Não há lugares disponíveis nesta boleia.")
            
        # Check if user is already a passenger[cite: 2]
        if any(p.id == utilizador.id for p in boleia.passageiros):
            raise ValueError("Utilizador já reservou lugar nesta boleia.")

        boleia.passageiros.append(utilizador)
        boleia.lugares_vagos -= 1
        self.boleias[boleia_id] = boleia

    def cancelar_reserva(self, boleia_id: str, user_id: str):
        boleia = self.boleias.get(boleia_id)
        if not boleia:
            raise KeyError("Boleia não encontrada.")
            
        initial_len = len(boleia.passageiros)
        boleia.passageiros = [p for p in boleia.passageiros if p.id != user_id]
        
        if len(boleia.passageiros) < initial_len:
            boleia.lugares_vagos += 1
            self.boleias[boleia_id] = boleia

    def consultar_boleias_de_jogo(self, jogo_id: str) -> list[Boleia]:
        """Returns all rides associated with a specific match ID[cite: 2]."""
        return [b for b in self.boleias.values() if str(b.jogo.id) == jogo_id]
    
    def registar_viatura(self, data: dict):
        """
        Registers a vehicle and updates both the database and the memory cache.
        Expects: {'id': str, 'modelo': str, 'matricula': str, 'lugares_totais': int, 'proprietario_id': str}
        """
        # Create the Viatura object
        owner = Utilizador(id=data['proprietario_id'], nome="", contacto="", password=b"", 
                          ativo=True, data_nascimento=None, 
                          nome_emergencia="", contacto_emergencia="")
        
        nova_v = Viatura(
            id=UUID(data['id']), 
            modelo=data['modelo'], 
            matricula=data['matricula'],
            lugares_totais=int(data['lugares_totais']), 
            proprietario=owner
        )

        # 1. Persist to Database
        self.boleias.put_viatura(nova_v)
        
        # 2. Update memory cache for immediate use without reloading[cite: 2]
        self.viatura[str(nova_v.id)] = nova_v