import os
from dotenv import load_dotenv

import time
from logic.ss_gestao.ss_gestao_facade import SSGestaoFacade
from datetime import datetime, timedelta,date
from logic.ss_eventos.ss_eventos_facade import SSEventosFacade
from utils.ui import UI

load_dotenv()

# 1. Setup Environment and Config
DB_CONFIG = {
    "host": "localhost",
    "database": os.getenv("DB_NAME", "caderno_quim"),
    "user": os.getenv("DB_USER", "beiroes_admin"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": 5432
}

def run_integrated_test():
    # --- Initialization ---[cite: 1]
    UI.banner()
    UI.step("Booting Subsystems")
    
    try:
        # Initialize Facades instead of DAOs directly
        gestao = SSGestaoFacade(DB_CONFIG)
        eventos = SSEventosFacade(DB_CONFIG)
        UI.success("Subsystems Synchronized.")
    except Exception as e:
        UI.setup_error(f"Initialization failed: {e}")
        return

    UI.sys_ready()

    # --- Phase 1: Total System Reset ---[cite: 1, 2]
    # We clear events first because they depend on users (Foreign Keys)
    UI.admin("Maintenance: Performing Full System Wipe...")
    eventos.eventos.clear()
    eventos.comunicados.clear()
    gestao.utilizadores.clear()
    UI.end_step("System Sanitization", "CLEAN")

    # --- Phase 2: User Management via Facade ---
    UI.sys("Phase 2: Registering Official Personnel")
    
    players_to_register = [
        {"id": "j01", "nome": "Diogo Costa", "posicao": "Guarda-redes", "tipo":"Jogador"},
        {"id": "j02", "nome": "Pepe", "posicao": "Defesa", "tipo":"Jogador"}
    ]

    for p_data in players_to_register:
        # Constructing the payload exactly as the Flask middleware would[cite: 2]
        payload = {
            "tipo": "Jogador",
            "id": p_data["id"],
            "nome": p_data["nome"],
            "contacto": f"91000000{p_data['id'][-1]}",
            "password": b"secure_hash_example",
            "data_nascimento": "1999-01-01",
            "posicao": p_data["posicao"],
            "nome_emergencia": "Admin",
            "contacto_emergencia": "112"
        }
        gestao.registar_utilizador(payload)
        UI.sub_user(f"Registered {p_data['tipo']}: {p_data['nome']} ({p_data['id']})")

    # --- Phase 3: Event Scheduling via Facade ---[cite: 2]
    UI.sys("Phase 3: Automated Event Scheduling")
    
    jogo_payload = {
        "tipo": "Jogo",
        "data_hora": (datetime.now() + timedelta(days=5)).isoformat(),
        "local": "Estádio do Dragão",
        "adversario": "Benfica"
    }
    jogo_id = eventos.criar_evento(jogo_payload)
    UI.sub_sys(f"Jogo Created: ID {jogo_id}")

    # --- Phase 4: Integrated Logistics (The FK Test) ---[cite: 2]
    UI.sys("Phase 4: Executing Convocatória")
    
    player_ids = [p["id"] for p in players_to_register]
    try:
        # This will fail if players were not correctly saved in Phase 2[cite: 2]
        eventos.efetuar_convocatoria(jogo_id, player_ids)
        UI.step(f"Convocatória successfully linked players to Jogo {jogo_id}")
    except Exception as e:
        UI.error(f"Integrity Error: {e}")
        return

    # --- Phase 5: Verification ---[cite: 1, 2]
    UI.sys("Phase 5: Data Persistence Verification")
    
    retrieved_jogo = eventos.eventos.get(jogo_id)
    if retrieved_jogo and len(retrieved_jogo.convocatoria.convocados) == len(player_ids):
        UI.success("Persistence Check Passed: All relationships valid.")
        UI.sub_info(f"Match: Beirões vs {retrieved_jogo.adversario}")
    else:
        UI.error("Persistence Check Failed: Data mismatch.")

    UI.menu_divider()
    UI.success("Integrated Automated Sequence Finished.")
    UI.menu_exit()

if __name__ == "__main__":
    run_integrated_test()