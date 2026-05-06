from flask import Flask, request, jsonify
from flask_cors import CORS

from logic.beiroes_facade import BeiroesLNFacade
from utils.ui import UI
import os
from datetime import datetime

class WebServer:
    def __init__(self, db_config: dict):
        self.app = Flask(__name__)
        CORS(self.app)
        self.ln = BeiroesLNFacade(db_config)
        self._setup_routes()

    def _setup_routes(self):
        # --- Gestão de Utilizadores ---
        @self.app.route('/auth/login', methods=['POST'])
        def login():
            data = request.json
            user = self.ln.autenticar(data.get('contacto'), data.get('password').encode())
            if user:
                return jsonify({"status": "success", "user_id": user.id}), 200
            return jsonify({"error": "Invalid credentials"}), 401

        @self.app.route('/jogadores/jogador', methods=['POST'])
        def registar_jogador():
            # Force 'Jogador' type for this endpoint
            data = request.json
            data['tipo'] = 'Jogador' 
            self.ln.registar_utilizador(data)
            return jsonify({"message": "Jogador registado"}), 201

        @self.app.route('/jogadores/procurar', methods=['GET'])
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

        # --- Calendário e Eventos ---
        @self.app.route('/eventos', methods=['POST'])
        def criar_evento():
            try:
                evento_id = self.ln.criar_evento(request.json)
                return jsonify({"id": evento_id}), 201
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route('/comunicados', methods=['POST'])
        def publicar_comunicado():
            self.ln.publicar_comunicado(request.json)
            return jsonify({"message": "Comunicado publicado"}), 201

        @self.app.route('/comunicados', methods=['GET'])
        def listar_comunicados():
            coms = self.ln.get_comunicados()
            return jsonify([c.__dict__ for c in coms]), 200

        # --- Operações Desportivas ---
        @self.app.route('/eventos/jogos/<id>/convocatoria', methods=['POST'])
        def definir_convocatoria(id):
            lista_ids = request.json.get('jogadores', [])
            self.ln.efetuar_convocatoria(id, lista_ids)
            return jsonify({"message": "Convocatória atualizada"}), 200

        @self.app.route('/eventos/treinos/<id>/presencas', methods=['POST'])
        def registar_presencas(id):
            self.ln.registar_presencas(id, request.json)
            return jsonify({"message": "Presenças registadas"}), 200
        
        @self.app.route('/eventos/jogos/<id>/resposta', methods=['POST'])
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
        @self.app.route('/boleias',methods=['GET'])
        def get_boleias():
            id_jogo = request.args.get('jogo_id')

            if not id_jogo:
                return jsonify(self.ln.consultar_boleias()),200

            return jsonify({"boleias":self.ln.consultar_boleias_de_jogo(id_jogo)}),200

        @self.app.route('/boleias', methods=['POST'])
        def criar_boleia():
            boleia_id = self.ln.disponibilizar_boleias(request.json)
            return jsonify({"id": boleia_id}), 201

        @self.app.route('/boleias/<id>/reservar', methods=['POST'])
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
        def get_viaturas():
            try:
                # 1. Fetch the raw dictionary of Viaturas from the facade
                raw_viaturas = self.ln.get_viaturas()
                
                # 2. Process each vehicle to ensure it is JSON-serializable
                cleaned_viaturas = {}
                for v_id, viatura in raw_viaturas.items():
                    # Convert the dataclass to a dictionary
                    v_dict = viatura.to_dict() if hasattr(viatura, 'to_dict') else viatura.__dict__.copy()
                    
                    # 3. Specifically clean the owner (proprietario) inside the Viatura
                    if 'proprietario' in v_dict and v_dict['proprietario']:
                        owner = v_dict['proprietario']
                        # If owner is an object, convert to dict; if already dict, copy it
                        owner_dict = owner.to_dict() if hasattr(owner, 'to_dict') else owner.__dict__.copy()
                        
                        # Remove sensitive bytes field from the owner
                        if 'password' in owner_dict:
                            del owner_dict['password']
                        
                        # Ensure dates are strings
                        if owner_dict.get('data_nascimento'):
                            owner_dict['data_nascimento'] = owner_dict['data_nascimento'].isoformat()
                        
                        v_dict['proprietario'] = owner_dict

                    cleaned_viaturas[v_id] = v_dict

                return jsonify(cleaned_viaturas), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route('/viaturas',methods=['POST'])
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


    def run(self, host='0.0.0.0', port=5000, debug=True):
        UI.success(f"Flask Web Server starting on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)