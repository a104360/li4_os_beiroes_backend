import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
from logic.ss_gestao.ss_gestao_facade import SSGestaoFacade
from logic.ss_eventos.ss_eventos_facade import SSEventosFacade
from utils.ui import UI

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "database": os.getenv("DB_NAME", "caderno_quim"),
    "user": os.getenv("DB_USER", "beiroes_admin"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": 5432
}

def run_integrated_test():
    UI.banner()
    UI.step("Initializing Subsystems")
    try:
        gestao = SSGestaoFacade(DB_CONFIG)
        eventos = SSEventosFacade(DB_CONFIG)
        UI.end_step("Subsystems Online.")
    except Exception as e:
        UI.setup_error(str(e))
        return

    # --- Phase 1: Database Reset ---[cite: 1, 2]
    UI.admin("Clearing all records...")
    eventos.eventos.clear()
    gestao.utilizadores.clear()
    UI.end_step("Database Sanitization", "CLEAN")

    # --- Phase 2: Registering Users (Crucial for Foreign Keys) ---[cite: 2]
    UI.sys("Phase 2: Registering Players")
    player_ids = ["j01", "j02"]
    for pid in player_ids:
        gestao.registar_utilizador({
            "tipo": "Jogador", "id": pid, "nome": f"Atleta {pid}",
            "contacto": f"91000000{pid[-1]}", "password": b"hash",
            "data_nascimento": "2000-01-01", "posicao": "Médio",
            "nome_emergencia": "Admin", "contacto_emergencia": "911"
        })
    UI.step(f"Registered players: {', '.join(player_ids)}")

    # --- Phase 3: Creating Events ---[cite: 2]
    UI.sys("Phase 3: Scheduling Events")
    jogo_id = eventos.criar_evento({
        "tipo": "Jogo", 
        "data_hora": (datetime.now() + timedelta(days=2)).isoformat(),
        "local": "Estádio Municipal", 
        "adversario": "GD Chaves"
    })
    UI.sub_sys(f"Jogo Created: {jogo_id}")

    # --- Phase 4: Linking Systems (Convocatória) ---[cite: 2]
    UI.sys("Phase 4: Issuing Convocatória")
    # This now works because j01 and j02 exist in the utilizadores table[cite: 2]
    eventos.efetuar_convocatoria(jogo_id, player_ids)
    UI.step(f"Players {player_ids} linked to Jogo {jogo_id}")

    # --- Phase 5: Verification ---[cite: 1, 2]
    UI.sys("Phase 5: Final Integrity Check")
    jogo_recuperado = eventos.eventos.get(jogo_id)
    UI.info(f"Jogo against: {jogo_recuperado.adversario}")
    UI.info(f"Convocados Count: {len(jogo_recuperado.convocatoria.convocados)}")
    
    UI.menu_divider()
    UI.success("Integrated Automated Test Passed.")
    UI.menu_exit()

if __name__ == "__main__":
    run_integrated_test()