from data.utilizador_dao import UtilizadorDAO
from logic.ss_gestao.utilizador import Utilizador,Jogador,Presidente,Treinador
from datetime import date


if __name__ == "__main__":
    # 1. Configuration
    config = {
        "host": "localhost",
        "database": "caderno_quim",
        "user": "beiroes_admin",
        "password": "%2*j5p5BRp5kQ%",
        "port": 5432
    }

    try:
        dao = UtilizadorDAO(config)
        dao.clear() # Start fresh
        print("--- Database Cleared ---")

        # 2. Create sample data
        j1 = Jogador(
            id="j01", nome="Cristiano", contacto="911", password=b"hash123",
            ativo=True, data_nascimento=date(1985, 2, 5),
            nome_emergencia="Maria", contacto_emergencia="922",
            posicao="Avançado"
        )

        t1 = Treinador(
            id="t01", nome="Mourinho", contacto="933", password=b"specialone",
            ativo=True, data_nascimento=date(1963, 1, 26),
            nome_emergencia="Tami", contacto_emergencia="944",
            licenca=date(2025, 12, 31)
        )

        # 3. Test Put (Insert)
        dao["j01"] = j1
        dao["t01"] = t1
        print(f"Inserted: {len(dao)} users.")

        # 4. Test Get
        user = dao.get("j01")
        print(f"Retrieved User: {user.nome} (Type: {type(user).__name__}, Position: {user.posicao})")

        # 5. Test Membership and Iteration
        print(f"Contains 't01'? {'t01' in dao}")
        
        print("Listing all keys in database:")
        for user_id in dao:
            print(f" - {user_id}")

        # 6. Test Remove
        del dao["j01"]
        print(f"Removed j01. New size: {len(dao)}")

    except Exception as e:
        print(f"Error during test: {e}")