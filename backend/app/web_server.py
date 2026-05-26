from flask import Flask, request, jsonify
from flask_cors import CORS

from logic.beiroes_facade import BeiroesLNFacade
from utils.ui import UI
from utils.utils import roles_requiered
import os
from dotenv import load_dotenv
from datetime import datetime,timedelta

from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager
    )

load_dotenv()

JWT_CONFIG = {
    'jwt_secret':os.getenv("JWT_SECRET_KEY")
} 

class WebServer:
    def __init__(self, db_config: dict):
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.config["JWT_SECRET_KEY"] = JWT_CONFIG.get('jwt_secret')  # Em produção, usar variável de ambiente
        self.app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
        jwt = JWTManager(self.app)
        self.ln = BeiroesLNFacade(db_config)
        self._setup_routes()

    def _setup_routes(self):
        # --- Gestão de Utilizadores ---
        @self.app.route('/auth/login', methods=['POST'])
        def login():
            data = request.json
            contacto = data.get('contacto')
            password = data.get('password')
            user = self.ln.autenticar(contacto, password.encode())
            if user:
                role = type(user).__name__
                access_token = create_access_token(
                    identity=contacto,
                    additional_claims={"role":role}
                    )
                # return jsonify({"status": "success", "user_id": user.id}), 200
                return jsonify(access_token=access_token), 200
            
            return jsonify({"error": "Invalid credentials"}), 401

        @self.app.route('/jogadores/jogador', methods=['POST'])
        @roles_requiered('Presidente','Treinador','Jogador')
        def registar_jogador():
            # Force 'Jogador' type for this endpoint
            data = request.json
            data['tipo'] = 'Jogador' 
            self.ln.registar_utilizador(data)
            return jsonify({"message": "Jogador registado"}), 201

        @self.app.route('/jogadores/procurar', methods=['GET'])
        @roles_requiered("Treinador","Presidente",'Jogador')
        def procurar_jogador():
            user_id = request.args.get('id')
            user = self.ln.procurar_utilizador(user_id)
            
            if user:
                # Convert dataclass to dict and clean non-serializable fields
                data = user.__dict__.copy()
                
                # Remove the bytes field or decode it
                if 'password' in data:
                    # Option A: Just remove it (Best practice for APIs)
                    del data['password'] 
                    
                    # Option B: Convert to string if you really need it
                    # data['password'] = data['password'].hex() 

                # Dates also need string conversion if they aren't handled by your encoder[cite: 1]
                if 'data_nascimento' in data and data['data_nascimento']:
                    data['data_nascimento'] = data['data_nascimento'].isoformat()
                
                # Now it's safe to return[cite: 1]
                return jsonify(data), 200
                
            return jsonify({"error": "Not found"}), 404

        @self.app.route("/jogadores",methods=['GET'])
        @roles_requiered("Presidente","Treinador","Jogador")
        def listar_todos_utilizadores():
            """
            Retrieves all users from the database.
            """
            try:
                # 1. Fetch all user objects from the facade
                # The facade's 'utilizadores' is a DAO whose .values() returns all records
                utilizadores = self.ln.gestao.utilizadores.values() 
                
                output = []
                for user in utilizadores:
                    # 2. Use the built-in to_dict() method to handle bytes and dates
                    user_data = user.to_dict()
                    
                    # 3. Security: Remove the password field before sending to client
                    if 'password' in user_data:
                        del user_data['password']
                    
                    # 4. Add the specific type for clarity in the frontend
                    user_data['tipo'] = type(user).__name__
                    
                    output.append(user_data)

                return jsonify(output), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        

        # --- Calendário e Eventos ---
        @self.app.route('/eventos', methods=['POST'])
        @roles_requiered("Jogador","Presidente","Treinador")
        def criar_evento():
            try:
                evento_id = self.ln.criar_evento(request.json)
                return jsonify({"id": evento_id}), 201
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route('/comunicados', methods=['POST'])
        @roles_requiered("Presidente","Treinador")
        def publicar_comunicado():
            self.ln.publicar_comunicado(request.json)
            return jsonify({"message": "Comunicado publicado"}), 201

        @self.app.route('/comunicados', methods=['GET'])
        @roles_requiered("Jogador","Presidente","Treinador")
        def listar_comunicados():
            coms = self.ln.get_comunicados()
            return jsonify([c.__dict__ for c in coms]), 200

        # --- Operações Desportivas ---
        @self.app.route('/eventos/jogos/<id>/convocatoria', methods=['POST'])
        @roles_requiered("Treinador")
        def definir_convocatoria(id):
            lista_ids = request.json.get('jogadores', [])
            self.ln.efetuar_convocatoria(id, lista_ids)
            return jsonify({"message": "Convocatória atualizada"}), 200

        @self.app.route('/eventos/treinos/<id>/presencas', methods=['POST'])
        @roles_requiered("Treinador")
        def registar_presencas(id):
            self.ln.registar_presencas(id, request.json)
            return jsonify({"message": "Presenças registadas"}), 200
        
        @self.app.route('/eventos/jogos/<id>/resposta', methods=['POST'])
        @roles_requiered("Jogador")
        def registar_resposta(id):
            """
            Expects JSON: { "jogador_id": "j01", "resposta": true }
            """
            data = request.json
            jogador_id = data.get('jogador_id')
            resposta = data.get('resposta')
            
            try:
                self.ln.registar_resposta_convocatoria(id, jogador_id, resposta)
                return jsonify({"message": "Resposta registada com sucesso"}), 200
            except (ValueError, KeyError) as e:
                return jsonify({"error": str(e)}), 400
            

        @self.app.route('/eventos', methods=['GET'])
        @roles_requiered("Jogador","Treinador","Presidente")
        def listar_eventos():
            """
            GET /eventos?ano=2026&mes=5
            """
            try:
                ano = int(request.args.get('ano', datetime.now().year))
                mes = int(request.args.get('mes', datetime.now().month))
                
                eventos = self.ln.listar_eventos_por_mes(ano, mes)
                
                # Serialization helper to convert objects to dicts
                output = []
                for e in eventos:
                    e_dict = e.__dict__.copy()
                    e_dict['id'] = str(e.id)
                    e_dict['data_hora'] = e.data_hora.isoformat()
                    e_dict['tipo'] = type(e).__name__
                    
                    # Handle specific Jogo/Treino nested data if necessary
                    if hasattr(e, 'convocatoria'):
                        e_dict['id_convocatoria'] = str(e.convocatoria.uuid)
                    
                    output.append(e_dict)
                
                return jsonify(output), 200
            except ValueError:
                return jsonify({"error": "Invalid year or month format"}), 400

        # --- Logística (Boleias) ---
        @self.app.route('/boleias', methods=['GET'])
        @roles_requiered("Jogador", "Treinador", "Presidente")
        def get_boleias():
            id_jogo = request.args.get('jogo_id')

            if not id_jogo:
                boleias_list = self.ln.consultar_boleias()
                print(boleias_list)
            else:
                boleias_list = self.ln.consultar_boleias_de_jogo(id_jogo)

            # Convert domain models to JSON-serializable dictionaries
            cleaned_boleias = []
            for b in boleias_list:
                b_dict = b.__dict__.copy()
                b_dict['id'] = str(b.id)
                if b.partida:
                    b_dict['partida'] = b.partida.isoformat()
                
                # Serialize Game (Jogo)
                if b.jogo:
                    b_dict['jogo'] = b.jogo.__dict__.copy()
                    b_dict['jogo']['id'] = str(b.jogo.id)
                
                # Serialize Vehicle (Viatura) and scrub Owner password
                if b.viatura:
                    v_dict = b.viatura.to_dict() if hasattr(b.viatura, 'to_dict') else b.viatura.__dict__.copy()
                    if 'proprietario' in v_dict and v_dict['proprietario']:
                        owner = v_dict['proprietario']
                        owner_dict = owner.to_dict() if hasattr(owner, 'to_dict') else owner.__dict__.copy()
                        if 'password' in owner_dict:
                            del owner_dict['password']
                        if owner_dict.get('data_nascimento'):
                            owner_dict['data_nascimento'] = owner_dict['data_nascimento'].isoformat()
                        v_dict['proprietario'] = owner_dict
                    b_dict['viatura'] = v_dict

                # Serialize Passengers list and scrub passwords
                cleaned_passengers = []
                for passenger in b.passageiros:
                    p_dict = passenger.to_dict() if hasattr(passenger, 'to_dict') else passenger.__dict__.copy()
                    if 'password' in p_dict:
                        del p_dict['password']
                    cleaned_passengers.append(p_dict)
                b_dict['passageiros'] = cleaned_passengers

                cleaned_boleias.append(b_dict)

            return jsonify({"boleias": cleaned_boleias}), 200

        @self.app.route('/boleias', methods=['POST'])
        @roles_requiered("Jogador","Treinador","Presidente")
        def criar_boleia():
            boleia_id = self.ln.disponibilizar_boleias(request.json)
            return jsonify({"id": boleia_id}), 201

        @self.app.route('/boleias/<id>/reservar', methods=['POST'])
        @roles_requiered("Jogador","Treinador","Presidente")
        def reservar_boleia(id):
            user_id = request.json.get('user_id')
            user = self.ln.procurar_utilizador(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            try:
                self.ln.reservar_lugar(id, user)
                return jsonify({"message": "Reserva efetuada"}), 200
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route('/viaturas', methods=['GET'])
        @roles_requiered("Jogador", "Treinador", "Presidente")
        def get_viaturas():
            try:
                # Obter o dicionário de viaturas retornado pela lógica de negócio
                viaturas_dict = self.ln.get_viaturas()
                cleaned_viaturas = {}

                for v_id, viatura_obj in viaturas_dict.items():
                    # 1. Converter o objeto Viatura principal para dicionário
                    if hasattr(viatura_obj, 'to_dict'):
                        v_dict = viatura_obj.to_dict()
                    else:
                        v_dict = viatura_obj.__dict__.copy()

                    # 2. Tratar o objeto aninhado 'proprietario' (Utilizador)
                    proprietario_obj = v_dict.get('proprietario')
                    if proprietario_obj:
                        if hasattr(proprietario_obj, 'to_dict'):
                            owner_dict = proprietario_obj.to_dict()
                        else:
                            owner_dict = proprietario_obj.__dict__.copy()
                        
                        # Remover a password em bytes para evitar o erro de serialização JSON
                        if 'password' in owner_dict:
                            del owner_dict['password']
                        
                        # Garantir que datas de nascimento não partem o JSON (caso existam)
                        if owner_dict.get('data_nascimento') and hasattr(owner_dict['data_nascimento'], 'isoformat'):
                            owner_dict['data_nascimento'] = owner_dict['data_nascimento'].isoformat()
                        
                        v_dict['proprietario'] = owner_dict

                    cleaned_viaturas[v_id] = v_dict

                return jsonify(cleaned_viaturas), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route('/viaturas',methods=['POST'])
        @roles_requiered("Jogador","Treinador","Presidente")
        def registar_viatura():
            """
            Registers a vehicle.
            Expects JSON: {
                "id": "uuid-string",
                "modelo": "Renault Clio",
                "matricula": "AA-00-BB",
                "lugares_totais": 5,
                "proprietario_id": "user-id"
            }
            """
            data = request.json
            try:
                self.ln.registar_viatura(data)
                return jsonify({"message": "Viatura registada com sucesso"}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route('/viaturas', methods=['DELETE'])
        @roles_requiered("Jogador", "Presidente", "Treinador")
        def apagar_viatura():
            id_viatura = request.args.get('viatura')
            if not id_viatura:
                return jsonify({"error": "Parâmetro 'viatura' (ID) é obrigatório."}), 400
                
            try:
                self.ln.remover_viatura(id_viatura)
                return jsonify({"message": "Viatura e boleias associadas removidas com sucesso"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self, host='0.0.0.0', port=5000, debug=True):
        UI.success(f"Flask Web Server starting on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)