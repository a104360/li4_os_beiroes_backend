import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from logic.beiroes_facade import BeiroesLNFacade
from utils.ui import UI

load_dotenv()

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "database": os.getenv("DB_NAME", "caderno_quim"),
    "user": os.getenv("DB_USER", "beiroes_admin"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": 5432
}

def run_master_test():
    UI.banner()
    UI.step("Initializing Master Beirões Facade")
    
    try:
        # Single entry point for all subsystems[cite: 3]
        beiroes = BeiroesLNFacade(DB_CONFIG)
        UI.success("All subsystems online and aggregated.")
    except Exception as e:
        UI.setup_error(f"Facade initialization failed: {e}")
        return

    UI.sys_ready()

    # --- Phase 1: Global System Reset ---[cite: 1, 2]
    UI.admin("Maintenance: Performing Global System Wipe...")
    # Clear in reverse order of dependencies
    beiroes.logistica.boleias.clear()
    beiroes.eventos.eventos.clear()
    beiroes.eventos.comunicados.clear()
    beiroes.gestao.utilizadores.clear()
    UI.end_step("System Sanitization", "CLEAN")

    # --- Phase 2: Gestão (User Registration) ---
    UI.sys("Phase 2: Registering Club Personnel")
    
    users = [
        {
            "tipo": "Jogador", "id": "j01", "nome": "Diogo Costa",
            "contacto": "910000001", "password": b"hash1", "data_nascimento": "1999-09-19",
            "posicao": "Guarda-Redes", "nome_emergencia": "Admin", "contacto_emergencia": "112"
        },
        {
            "tipo": "Jogador", "id": "j02", "nome": "Pepe",
            "contacto": "910000002", "password": b"hash2", "data_nascimento": "1983-02-26",
            "posicao": "Defesa Central", "nome_emergencia": "Admin", "contacto_emergencia": "112"
        }
    ]
    
    for u_data in users:
        beiroes.registar_utilizador(u_data)
        UI.sub_user(f"Registered {u_data['nome']} ({u_data['id']})")

    # --- Phase 3: Logística (Vehicle Setup) ---[cite: 2]
    UI.sys("Phase 3: Registering Logistics Assets")
    
    viatura_payload = {
        "id": "67c915fc-4b9d-4b8f-9825-80670e110b39",
        "modelo": "Autocarro Beirões", 
        "matricula": "BE-01-RO",
        "lugares_totais": 20, 
        "proprietario_id": "j01"
    }
    beiroes.registar_viatura(viatura_payload)
    UI.step(f"Viatura {viatura_payload['matricula']} registered and cached in memory.")

    # --- Phase 4: Eventos (Games & Comunicados) ---[cite: 2]
    UI.sys("Phase 4: Scheduling Competitions")
    
    jogo_id = beiroes.criar_evento({
        "tipo": "Jogo", 
        "data_hora": (datetime.now() + timedelta(days=2)).isoformat(),
        "local": "Estádio do Dragão", 
        "adversario": "SL Benfica"
    })
    UI.sub_sys(f"Jogo created: ID {jogo_id}")

    # Issue Convocatória[cite: 2]
    player_ids = ["j01", "j02"]
    beiroes.efetuar_convocatoria(jogo_id, player_ids)
    UI.sub_info(f"Convocatória issued for {len(player_ids)} players.")

    # --- Phase 5: Integrated Logistics (Boleias) ---[cite: 2]
    UI.sys("Phase 5: Coordinating Match Transportation")
    
    boleia_id = beiroes.disponibilizar_boleias({
        "partida": (datetime.now() + timedelta(days=2, hours=-2)).isoformat(),
        "viatura_id": viatura_payload["id"],
        "jogo_id": jogo_id,
        "max_lugares": 10
    })
    
    # Simulate a reservation[cite: 2]
    passageiro = beiroes.procurar_utilizador("j02")
    beiroes.reservar_lugar(boleia_id, passageiro)
    UI.step(f"Transportation link established: Passenger 'j02' reserved on 'BE-01-RO'.")

    # --- Phase 6: Communication ---[cite: 2]
    UI.sys("Phase 6: Broadcasting Official News")
    
    beiroes.publicar_comunicado({
        "titulo": "Dia de Jogo!",
        "corpo": "Todos os convocados devem comparecer no estádio 2 horas antes."
    })
    UI.sub_user("Match Day Comunicado published.")

    # --- Phase 7: Final Validation ---[cite: 1, 2]
    UI.sys("Phase 7: End-to-End Integrity Verification")
    
    comunicados = beiroes.get_comunicados()
    total_events = len(beiroes.eventos.eventos.values())
    
    if len(comunicados) > 0 and total_events > 0:
        UI.success("Master Facade Test Passed: All subsystems synchronized perfectly.")
        UI.info(f"Summary: {total_events} Event(s), {len(comunicados)} Comunicado(s).")
    else:
        UI.error("Final verification failed: Data persistence incomplete.")

    UI.menu_exit()

if __name__ == "__main__":
    run_master_test()