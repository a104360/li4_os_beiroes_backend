import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from logic.beiroes_facade import BeiroesLNFacade
from utils.ui import UI

# 1. Configuration
load_dotenv()
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "caderno_quim"),
    "user": os.getenv("DB_USER", "beiroes_admin"),
    "password": os.getenv("DB_PASSWORD")
}

def seed_database():
    UI.banner()
    UI.step("Initializing Seeding Process...")
    
    try:
        ln = BeiroesLNFacade(DB_CONFIG)
        UI.success("Connected to Subsystems.")
    except Exception as e:
        UI.setup_error(f"Connection failed: {e}")
        return

    # --- Phase 1: Reset (Optional) ---
    UI.warn("Clearing existing data for a clean seed...")
    ln.logistica.boleias.clear()
    ln.eventos.eventos.clear()
    ln.eventos.comunicados.clear()
    ln.gestao.utilizadores.clear()

    # --- Phase 2: Users (Gestão) ---
    UI.sys("Seeding Users...")
    users = [
        {"id": "u1", "nome": "Quim Barrela", "contacto": "910000001", "password": b"quim123", "tipo": "Presidente", "data_nascimento": "1975-06-15", "anos_mandato": 4},
        {"id": "u2", "nome": "Mister Zé", "contacto": "910000010", "password": b"mister123", "tipo": "Treinador", "data_nascimento": "1980-03-10", "licenca": "2028-12-31"},
        {"id": "u3", "nome": "Tiago Silva", "contacto": "910000002", "password": b"tiago123", "tipo": "Jogador", "data_nascimento": "1995-05-12", "posicao": "Defesa Central"},
        {"id": "j2", "nome": "Bruno Ferreira", "contacto": "910000004", "password": b"bruno123", "tipo": "Jogador", "data_nascimento": "1998-02-22", "posicao": "Avançado"},
        {"id": "j3", "nome": "Carlos Mota", "contacto": "910000005", "password": b"carlos123", "tipo": "Jogador", "data_nascimento": "1990-11-05", "posicao": "Médio"},
        {"id": "j4", "nome": "André Costa", "contacto": "910000006", "password": b"andre123", "tipo": "Jogador", "data_nascimento": "2000-01-15", "posicao": "Guarda-Redes"}
    ]
    for u in users:
        # Standardize payload for the facade
        u["nome_emergencia"] = "Emergência"
        u["contacto_emergencia"] = "112"
        ln.registar_utilizador(u)
        UI.sub_user(f"Seeded: {u['nome']}")

    # --- Phase 3: Events (Calendário) ---
    UI.sys("Seeding Events...")
    # Training
    t_id = ln.criar_evento({
        "tipo": "Treino",
        "data_hora": "2026-04-17T20:00:00",
        "local": "Campo Principal"
    })
    
    # Games
    g1_id = ln.criar_evento({
        "tipo": "Jogo",
        "data_hora": "2026-04-20T15:00:00",
        "local": "Fora",
        "adversario": "GD Fundão"
    })
    
    g2_id = ln.criar_evento({
        "tipo": "Jogo",
        "data_hora": "2026-04-28T15:00:00",
        "local": "Estádio Municipal do Tortosendo",
        "adversario": "CF Tortosendo"
    })

    # --- Phase 4: Convocatórias & Respostas ---
    UI.sys("Seeding Convocatórias...")
    # Squad for Game 1
    squad_ids = ["u3", "j2", "j4"]
    ln.efetuar_convocatoria(g1_id, squad_ids)
    # Registering Responses
    ln.registar_resposta_convocatoria(g1_id, "u3", True)  # Tiago says Yes
    ln.registar_resposta_convocatoria(g1_id, "j2", False) # Bruno says No
    
    UI.sub_info(f"Convocatória issued for Game {g1_id}")

    # --- Phase 5: Logistics (Boleias) ---
    UI.sys("Seeding Logistics...")
    # Register the vehicle first
    viatura_id = "v1"
    ln.registar_viatura({
        "id": viatura_id,
        "modelo": "Clio Azul",
        "matricula": "AA-11-BB",
        "lugares_totais": 5,
        "proprietario_id": "u3"
    })
    UI.step("Vehicle registered")
    
    # Offer a ride for the Tortosendo game
    ln.disponibilizar_boleias({
        "partida": "2026-04-28T13:30:00",
        "viatura_id": viatura_id,
        "jogo_id": g2_id,
        "max_lugares": 2
    })
    UI.sub_sys("Boleia created for Game 2.")

    # --- Phase 6: Comunicados ---
    UI.sys("Seeding Comunicados...")
    coms = [
        {"titulo": "Inscrições na Associação", "corpo": "Prazo renovação: 30 de Abril."},
        {"titulo": "Treino de Quarta Alterado", "corpo": "Alterado para as 20:00."},
        {"titulo": "Parabéns pela Vitória!", "corpo": "Cozido domingo na sede."}
    ]
    for c in coms:
        ln.publicar_comunicado(c)
    
    UI.success("Database Seeding Complete!")
    UI.menu_exit()

if __name__ == "__main__":
    seed_database()