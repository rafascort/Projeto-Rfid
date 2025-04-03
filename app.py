from flask import Flask, request, jsonify
import sqlite3
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

class AsyncConn:
    def __init__(self, id: str, channel_name: str) -> None:
        config = PNConfiguration()
        config.subscribe_key = 'sub-c-d164b3c1-6812-4226-b6ca-dac8d61b0892'
        config.publish_key = 'pub-c-bf44c010-1a75-4672-b5ce-43bce6c33454'
        config.user_id = id
        config.enable_subscribe = True
        config.daemon = True

        self.pubnub = PubNub(config)
        self.channel_name = channel_name
        print(f"Configurando conexão com o canal '{self.channel_name}'...")

        subscription = self.pubnub.channel(self.channel_name).subscription()
        subscription.subscribe()

    def publish(self, data: dict):
        try:
            print("📡 Enviando mensagem para o PubNub...")
            self.pubnub.publish().channel(self.channel_name).message(data).sync()
        except Exception as e:
            print(f"❌ Erro ao publicar no PubNub: {e}")

app = Flask(__name__)
pubnub = AsyncConn("FlaskApp", "flask_channel")

def connect_db(db_name):
    return sqlite3.connect(db_name, timeout=5)

def create_tables():
    with connect_db('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                tipo_operacao TEXT NOT NULL,
                data_horario TEXT NOT NULL
            )
        """)
        conn.commit()

    with connect_db('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                cartao_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL
            )
        """)
        conn.commit()

create_tables()

def publish_to_pubnub(data):
    pubnub.publish(data)

@app.route('/entradas-saidas', methods=['POST', 'GET'])
def entradas_saidas():
    try:
        if request.method == "POST":
            tipo_operacao = request.json.get('tipo_operacao')
            data_horario = request.json.get('data_horario')
            cartao_id = request.json.get('cartao_id')
            nome = request.json.get('nome')

            print(f"📥 Recebido: Tipo={tipo_operacao}, Data={data_horario}, Cartão ID={cartao_id}, Nome={nome}")

            if None in (tipo_operacao, data_horario, cartao_id, nome):
                return jsonify({"error": "Dados insuficientes fornecidos"}), 400

            if tipo_operacao == "acesso negado":
                nome = "Desconhecido"

            with connect_db('data.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO registros (tipo_operacao, data_horario, cartao_id, nome)
                    VALUES (?, ?, ?, ?)
                ''', (tipo_operacao, data_horario, cartao_id, nome))
                conn.commit()

            try:
                publish_to_pubnub({"tipo_operacao": tipo_operacao, "data_horario": data_horario, "cartao_id": cartao_id, "nome": nome})
            except Exception as e:
                print(f"❌ Erro ao enviar dados para o PubNub: {e}")

            return jsonify({
                "message": "✅ Dados adicionados com sucesso",
                "tipo_operacao": tipo_operacao,
                "data_horario": data_horario,
                "cartao_id": cartao_id,
                "nome": nome
            }), 201

        elif request.method == "GET":
            with connect_db('data.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT tipo_operacao, data_horario, cartao_id, nome FROM registros')
                rows = cursor.fetchall()

            values = [{"tipo_operacao": row[0], "data_horario": row[1], "cartao_id": row[2], "nome": row[3]} for row in rows]

            return jsonify(values), 200

    except Exception as e:
        print(f"❌ Erro no servidor: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
