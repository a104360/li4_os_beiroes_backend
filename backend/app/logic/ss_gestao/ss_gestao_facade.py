from typing import Optional
from logic.ss_gestao.utilizador import Utilizador, Jogador, Treinador, Presidente
from data.utilizador_dao import UtilizadorDAO
from data.abstract_dao import AbstractDAO
from datetime import date

class SSGestaoFacade:
    def __init__(self, db_config: dict):
        self.utilizadores: AbstractDAO = UtilizadorDAO(db_config)

    def autenticar(self, contacto: str, password_hash: bytes) -> Optional[Utilizador]:
        """Authenticates a user by checking contact and password hash."""
        # Note: In a real app, you'd fetch by contact, but our DAO uses ID as key
        for user in self.utilizadores.values():
            if user.contacto == contacto and user.password == password_hash:
                return user
        return None

    def registar_utilizador(self, data: dict):
        """Creates a new user from a dictionary."""
        tipo = data.get("tipo")
        base_args = {
            "id": data.get("id"),
            "nome": data.get("nome"),
            "contacto": data.get("contacto"),
            "password": data.get("password"),  # Expects bytes
            "ativo": data.get("ativo", True),
            "data_nascimento": date.fromisoformat(data.get("data_nascimento")),
            "nome_emergencia": data.get("nome_emergencia"),
            "contacto_emergencia": data.get("contacto_emergencia")
        }

        if tipo == "Jogador":
            u = Jogador(**base_args, posicao=data.get("posicao"))
        elif tipo == "Treinador":
            u = Treinador(**base_args, licenca=date.fromisoformat(data.get("licenca")))
        elif tipo == "Presidente":
            u = Presidente(**base_args, anos_mandato=int(data.get("anos_mandato")))
        else:
            u = Utilizador(**base_args)

        self.utilizadores[u.id] = u

    def procurar_utilizador(self, user_id: str) -> Optional[Utilizador]:
        return self.utilizadores.get(user_id)

    def editar_utilizador(self, user_id: str, data: dict):
        user = self.utilizadores.get(user_id)
        if not user:
            raise KeyError(f"Utilizador {user_id} não encontrado.")
        
        # Update attributes if present in data
        for key, value in data.items():
            if hasattr(user, key):
                if "data" in key or "licenca" in key:
                    setattr(user, key, date.fromisoformat(value))
                else:
                    setattr(user, key, value)
        
        self.utilizadores[user_id] = user

    def desativar_utilizador(self, user_id: str):
        user = self.utilizadores.get(user_id)
        if user:
            user.ativo = False
            self.utilizadores[user_id] = user

    def get_all_utilizadores(self):
        return self.utilizadores.values()
        