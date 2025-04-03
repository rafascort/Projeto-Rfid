import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
import time
import os
import sqlite3
from datetime import datetime

leitorRfid = SimpleMFRC522()

def connect_db():
    return sqlite3.connect('users.db', timeout=10)

def create_tables():
    with connect_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                cartao_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL
            )
        """)

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

def definir_tipo_operacao(cartao_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tipo_operacao FROM registros WHERE cartao_id = ?
            ORDER BY data_horario DESC LIMIT 1
        """, (cartao_id,))
        last_record = cursor.fetchone()
    
    return "saida" if last_record and last_record[0] == "entrada" else "entrada"

def send_post_request(tipo_operacao, data_horario, cartao_id, nome):
    data = {
        'tipo_operacao': tipo_operacao,
        'data_horario': data_horario,
        'cartao_id': cartao_id,
        'nome': nome
    }
    print(f"📡 Enviando dados: {data}")

    try:
        response = requests.post('http://localhost:5000/entradas-saidas', json=data)
        if response.status_code == 201:
            print("✅ Dados enviados com sucesso!")
        else:
            print(f"❌ Erro ao enviar dados: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

def ler_cartao():
    try:
        os.system("clear")
        print("📟 Aguardando leitura da tag...")
        tag, _ = leitorRfid.read()
        tag = str(tag)

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM users WHERE cartao_id = ?", (tag,))
            row = cursor.fetchone()

        if row:
            nome = row[0]
            tipo_operacao = definir_tipo_operacao(tag)
        else:
            nome = "Desconhecido"
            tipo_operacao = "acesso negado"

        data_horario = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🆔 ID: {tag} | Nome: {nome} | Tipo: {tipo_operacao}")

        send_post_request(tipo_operacao, data_horario, tag, nome)

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO registros (cartao_id, nome, tipo_operacao, data_horario)
                VALUES (?, ?, ?, ?)
            """, (tag, nome, tipo_operacao, data_horario))
            conn.commit()

        time.sleep(2)
    except KeyboardInterrupt:
        print("⏹ Programa interrompido.")

create_tables()

try:
    while True:
        os.system("clear")
        print("\n===================================================")
        print("🎫 Sistema de Registro de Entradas e Saídas")
        print("===================================================\n")
        print("🔹 Pressione 1 para registrar entrada/saída")
        print("🔹 Pressione Q para sair")

        escolha_usuario = input("🟢 Escolha uma opção: ")
        if escolha_usuario == "1":
            ler_cartao()
        elif escolha_usuario.lower() == "q":
            print("⏹ Saindo do programa...")
            break
        else:
            print("⚠ Opção inválida. Digite novamente.")
            time.sleep(1)
finally:
    GPIO.cleanup()
