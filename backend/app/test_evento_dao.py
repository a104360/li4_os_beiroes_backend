import os
from dotenv import load_dotenv
from datetime import datetime
from logic.ss_eventos.evento import Treino, Jogo, Convocatoria
from data.evento_dao import EventoDAO
from utils.ui import UI
from utils.facade import Menu, MenuEntry, Facade

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "database": os.getenv("DB_NAME", "beiroes_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": 5432
}

class EventoTestManager:
    def __init__(self):
        UI.step("Connecting to database...")
        self.dao = EventoDAO(DB_CONFIG)
        UI.success("EventoDAO Initialized.")

    def test_add_treino(self):
        local = UI.menu_prompt_message("Enter Training Local")
        novo = Treino(data_hora=datetime.now(), local=local, estado="Agendado", presencas={})
        self.dao.put(str(novo.id),novo)
        UI.success(f"Treino added at {local}")

    def test_add_jogo(self):
        adv = UI.menu_prompt_message("Enter Opponent")
        local = UI.menu_prompt_message("Enter Field Location")
        novo = Jogo(data_hora=datetime.now(), local=local, estado="Agendado",
                    adversario=adv, golos_favor=0, golos_contra=0, 
                    convocatoria=Convocatoria())
        self.dao.put(str(novo.id),novo)
        UI.success(f"Jogo against {adv} registered.")

    def test_list_all(self):
        UI.sys("Fetching all events...")
        for e in self.dao.values():
            UI.menu_divider()
            tipo = type(e).__name__
            UI.sub_sys(f"[{tipo}] ID: {e.id}")
            UI.sub_user(f"Local: {e.local} | Status: {e.estado}")
            if isinstance(e, Jogo):
                UI.sub_info(f"Opponent: {e.adversario}")

    def test_clear(self):
        UI.warn("Resetting events database...")
        self.dao.clear()
        UI.success("Done.")

def main():
    manager = EventoTestManager()
    UI.banner()
    
    test_menu = Menu(
        "Evento DAO Testing",
        MenuEntry("List Events", manager.test_list_all),
        MenuEntry("Add Treino", manager.test_add_treino),
        MenuEntry("Add Jogo", manager.test_add_jogo),
        MenuEntry("Clear Database", manager.test_clear),
        allow_back=False
    )

    facade = Facade()
    facade.add_menu("main", test_menu)
    facade.run("main")

if __name__ == "__main__":
    main()