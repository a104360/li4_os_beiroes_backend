import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from utils.ui import UI
from logic.ss_gestao.ss_gestao_facade import SSGestaoFacade
from logic.ss_eventos.ss_eventos_facade import SSEventosFacade
from logic.ss_logistica.ss_logistica_facade import SSLogisticaFacade

load_dotenv()

# Database Configuration[cite: 3]
DB_CONFIG = {
    "host": "localhost",
    "database": os.getenv("DB_NAME", "caderno_quim"),
    "user": os.getenv("DB_USER", "beiroes_admin"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": 5432
}

def run_logistica_test():
    UI.banner()
    UI.step("Connecting Logistics Subsystems")
    
    try:
        gestao = SSGestaoFacade(DB_CONFIG)
        eventos = SSEventosFacade(DB_CONFIG)
        logistica = SSLogisticaFacade(DB_CONFIG)
        UI.success("Logistics, Events, and Management Subsystems Online.")
    except Exception as e:
        UI.setup_error(f"Boot failed: {e}")
        return

    # --- Phase 1: Clean Slate ---
    UI.admin("Phase 1: Sanitizing Relational Environment...")
    # Clear in reverse order of dependencies to respect FKs
    logistica.boleias.clear() 
    eventos.eventos.clear()
    gestao.utilizadores.clear()
    UI.end_step("Database Sanitization", "CLEAN")

    # --- Phase 2: Dependency Injection (Users & Events) ---
    UI.sys("Phase 2: Registering Required Entities")
    
    # 1. Register Owner and Passenger via Gestao Facade
    players = [
        {
            "tipo": "Jogador", "id": "u_owner", "nome": "Condutor Silva",
            "contacto": "911111111", "password": b"pass", "data_nascimento": "1990-01-01",
            "posicao": "Guarda-Redes", "nome_emergencia": "Admin", "contacto_emergencia": "911"
        },
        {
            "tipo": "Jogador", "id": "u_pass", "nome": "Passageiro Santos",
            "contacto": "922222222", "password": b"pass", "data_nascimento": "1995-05-05",
            "posicao": "Avancado", "nome_emergencia": "Admin", "contacto_emergencia": "911"
        }
    ]
    for p in players:
        gestao.registar_utilizador(p)
    UI.step(f"Registered {len(players)} Users.")

    # 2. Register Jogo via Eventos Facade[cite: 2]
    jogo_id = eventos.criar_evento({
        "tipo": "Jogo", "local": "Estádio da Luz", "adversario": "SLB",
        "data_hora": (datetime.now() + timedelta(days=2)).isoformat()
    })
    UI.sub_sys(f"Jogo Reference Created: {jogo_id}")

    # --- Phase 3: Logistics Setup[cite: 2] ---
    UI.sys("Phase 3: Viatura and Cache Management")
    
    # Register Viatura: This updates DB and self.viatura cache[cite: 2]
    viatura_payload = {
        "id": "67c915fc-4b9d-4b8f-9825-80670e110b39", # Example UUID string
        "modelo": "Tesla Model 3", 
        "matricula": "AA-00-BB",
        "lugares_totais": 5, 
        "proprietario_id": "u_owner"
    }
    logistica.registar_viatura(viatura_payload)
    UI.sub_user(f"Viatura {viatura_payload['matricula']} registered and cached.")

    # --- Phase 4: Boleia Lifecycle[cite: 2] ---
    UI.sys("Phase 4: Testing Ride Creation and Reservations")
    
    boleia_payload = {
        "partida": (datetime.now() + timedelta(days=2, hours=-2)).isoformat(),
        "viatura_id": viatura_payload["id"],
        "jogo_id": jogo_id,
        "max_lugares": 4
    }
    
    boleia_id = logistica.disponibilizar_boleias(boleia_payload)
    UI.step(f"Boleia offered for Jogo {jogo_id}")

    # Test Reservation[cite: 2]
    passenger = gestao.procurar_utilizador("u_pass")
    logistica.reservar_lugar(boleia_id, passenger)
    UI.step(f"Seat reserved for player 'u_pass'.")

    # --- Phase 5: Verification[cite: 2] ---
    UI.sys("Phase 5: Final Persistence Validation")
    
    final_b = logistica.boleias.get(boleia_id)
    if final_b and len(final_b.passageiros) == 1:
        UI.success("Logistics Integration Test Passed.")
        UI.sub_info(f"Viatura: {final_b.viatura.modelo}")
        UI.sub_info(f"Seats Remaining: {final_b.lugares_vagos}")
    else:
        UI.error("Data mismatch in persisted Boleia object.")

    UI.menu_exit()

if __name__ == "__main__":
    run_logistica_test()