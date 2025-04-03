import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import os
import time

leitorRfid = SimpleMFRC522()

def connect_db():
    return sqlite3.connect('users.db', timeout=10)

def create_table():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                cartao_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL
            )
        """)
        conn.commit()

def cadastrar_cartao():
    try:
        os.system("clear")
        print("📌 Aproxime o cartão RFID para cadastro...")
        tag, _ = leitorRfid.read()
        tag = str(tag)

        nome = input("📝 Digite o nome do usuário: ").strip()
        if not nome:
            print("⚠ Nome inválido! Tente novamente.")
            return
        
        with connect_db() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT nome FROM users WHERE cartao_id = ?", (tag,))
            existing = cursor.fetchone()

            if existing:
                print(f"⚠ O cartão já está cadastrado para {existing[0]}.")
            else:
                cursor.execute("INSERT INTO users (cartao_id, nome) VALUES (?, ?)", (tag, nome))
                conn.commit()
                print(f"✅ Cartão {tag} cadastrado com sucesso para {nome}!")

        time.sleep(2)
    except KeyboardInterrupt:
        print("\n⏹ Cadastro interrompido.")
    finally:
        GPIO.cleanup()

create_table()

try:
    while True:
        os.system("clear")
        print("\n===================================================")
        print("🆕 Cadastro de Cartões RFID")
        print("===================================================\n")
        print("🔹 Pressione 1 para cadastrar um novo cartão")
        print("🔹 Pressione Q para sair")

        escolha = input("🟢 Escolha uma opção: ")
        if escolha == "1":
            cadastrar_cartao()
        elif escolha.lower() == "q":
            print("⏹ Saindo...")
            break
        else:
            print("⚠ Opção inválida. Tente novamente.")
            time.sleep(1)
finally:
    GPIO.cleanup()
