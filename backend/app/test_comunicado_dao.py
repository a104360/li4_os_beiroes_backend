
import os
from dotenv import load_dotenv
from uuid import uuid4

from logic.ss_eventos.comunicado import Comunicado
from data.comunicado_dao import ComunicadoDAO
from utils.ui import UI
from utils.facade import Menu, MenuEntry, Facade, MenuExit

# 1. Database Configuration (Loaded from Environment)

load_dotenv(dotenv_path="../../.env")

DB_CONFIG = {
    "host": "localhost",
    "database": os.getenv("DB_NAME", "caderno_quim"),
    "user": os.getenv("DB_USER", "beiroes_admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": 5432
}

class ComunicadoTestManager:
    def __init__(self):
        UI.step("Connecting to database...")
        try:
            self.dao = ComunicadoDAO(DB_CONFIG)
            UI.success("ComunicadoDAO Initialized.")
        except Exception as e:
            UI.setup_error(str(e))
            exit(1)

    def test_clear(self):
        UI.warn("Clearing all records from 'comunicados'...")
        self.dao.clear()
        UI.success("Table cleared.")

    def test_insert(self):
        titulo = UI.menu_prompt_message("Enter Title")
        corpo = UI.menu_prompt_message("Enter Content Body")
        
        novo = Comunicado(titulo=titulo, corpo=corpo)
        UI.info(f"Generating ID: {novo.id}")
        
        self.dao[str(novo.id)] = novo
        UI.success(f"Comunicado '{titulo}' inserted successfully.")

    def test_list_all(self):
        UI.sys("Fetching all comunicados...")
        items = self.dao.values()
        
        if not items:
            UI.sub_warn("No records found in database.")
            return

        for c in items:
            UI.menu_divider()
            UI.sub_sys(f"ID: {c.id}")
            UI.sub_user(f"TITULO: {c.titulo}")
            UI.sub_info(f"DATA: {c.data}")
            UI.sub_info(f"CORPO: {c.corpo[:50]}...") # Truncated for display

    def test_get_by_id(self):
        search_id = UI.menu_prompt_message("Enter UUID to find")
        UI.info(f"Searching for {search_id}...")
        
        res = self.dao.get(search_id)
        if res:
            UI.success("Match found!")
            UI.sub_user(f"Title: {res.titulo}")
        else:
            UI.error("No record found with that ID.")

def main():
    manager = ComunicadoTestManager()
    facade = Facade()

    # Define Menu Entries linked to our test methods
    test_menu = Menu(
        "Comunicado DAO Testing",
        MenuEntry("List All Comunicados", manager.test_list_all),
        MenuEntry("Create New Comunicado", manager.test_insert),
        MenuEntry("Get Comunicado by ID", manager.test_get_by_id),
        MenuEntry("Clear Database (Reset)", manager.test_clear),
        allow_back=False
    )

    facade.add_menu("main", test_menu)
    facade.run("main")

if __name__ == "__main__":
    main()