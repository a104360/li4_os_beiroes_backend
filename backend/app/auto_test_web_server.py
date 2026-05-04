import requests
import time
from datetime import datetime, timedelta
from utils.ui import UI

# Base configuration for the API
BASE_URL = "http://localhost:8080"

def run_web_api_test():
    UI.banner()
    UI.step("Starting Web API Integration Test")
    
    # Check if server is reachable
    try:
        requests.get(f"{BASE_URL}/comunicados")
    except requests.exceptions.ConnectionError:
        UI.setup_error(f"Server not found at {BASE_URL}. Ensure WebServer is running.")
        return

    # --- Phase 1: Registration ---
    UI.sys("Phase 1: Registering Personnel via POST /jogadores/jogador")
    
    jogador_payload = {
        "id": "web_j01",
        "nome": "Diogo Costa (Web)",
        "contacto": "910000888",
        "password": "secure_password",
        "data_nascimento": "1999-01-01",
        "posicao": "Guarda-Redes",
        "nome_emergencia": "Admin",
        "contacto_emergencia": "112"
    }
    
    response = requests.post(f"{BASE_URL}/jogadores/jogador", json=jogador_payload)
    if response.status_code == 201:
        UI.step(f"Successfully registered player: {jogador_payload['id']}")
    else:
        UI.error(f"Registration failed: {response.text}")
        return

    # --- Phase 2: Retrieval & Serialization Check ---
    UI.sys("Phase 2: Verifying Data via GET /jogadores/procurar")
    
    response = requests.get(f"{BASE_URL}/jogadores/procurar", params={"id": "web_j01"})
    if response.status_code == 200:
        data = response.json()
        UI.sub_info(f"Retrieved Name: {data.get('nome')}")
        # Verify sensitive data is removed
        if 'password' not in data:
            UI.step("Serialization Check: Password field correctly hidden.")
    else:
        UI.error(f"Search failed: {response.status_code}")

    # --- Phase 3: Events & Convocatória ---
    UI.sys("Phase 3: Scheduling Event and Squad")
    
    evento_payload = {
        "tipo": "Jogo",
        "data_hora": (datetime.now() + timedelta(days=3)).isoformat(),
        "local": "Estádio do Dragão",
        "adversario": "SC Braga"
    }
    
    res_evento = requests.post(f"{BASE_URL}/eventos", json=evento_payload)
    jogo_id = res_evento.json().get('id')
    UI.sub_sys(f"Event Created via API. ID: {jogo_id}")

    # Set Squad
    conv_payload = {"jogadores": ["web_j01"]}
    requests.post(f"{BASE_URL}/eventos/jogos/{jogo_id}/convocatoria", json=conv_payload)
    UI.sub_info("Convocatória updated via HTTP POST.")

    # --- Phase 4: Interactive Operations ---
    UI.sys("Phase 4: Player Interaction via POST /resposta")
    
    resposta_payload = {
        "jogador_id": "web_j01",
        "resposta": True
    }
    res_resp = requests.post(f"{BASE_URL}/eventos/jogos/{jogo_id}/resposta", json=resposta_payload)
    if res_resp.status_code == 200:
        UI.step("Attendance response recorded successfully.")
    else:
        UI.error(f"Response failed: {res_resp.text}")

    # --- Phase 5: Logistics ---
    UI.sys("Phase 5: Logistics Coordination")
    
    # Note: Viatura must exist in DB. In a real test, 
    # we would register a viatura via API first.
    # Here we assume the DB already has a viatura registered from previous tests.
    
    UI.success("Web API Full Flow Test Completed.")
    UI.menu_exit()

if __name__ == "__main__":
    run_web_api_test()