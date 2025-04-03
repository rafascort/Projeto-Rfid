import sqlite3

def read_users_db():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT cartao_id, nome FROM users")
        users = cursor.fetchall()
        conn.close()
        
        if users:
            print("Cartões cadastrados:")
            for cartao_id, nome in users:
                print(f"ID: {cartao_id} | Nome: {nome}")
        else:
            print("Nenhum cartão cadastrado.")
    except Exception as e:
        print(f"Erro ao ler o banco de dados: {e}")

if __name__ == "__main__":
    read_users_db()
