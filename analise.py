import pandas as pd
import requests
import sqlite3

# URLs da API
API_URL = "http://localhost:5000/entradas-saidas"

# Função para buscar os registros de acesso da API
def get_logs():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao acessar API: {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return []

# Função para buscar a lista de colaboradores do banco de dados
def get_users():
    try:
        conn = sqlite3.connect("users.db")
        df_users = pd.read_sql_query("SELECT cartao_id, nome FROM users", conn)
        conn.close()
        return df_users
    except Exception as e:
        print(f"Erro ao acessar users.db: {e}")
        return pd.DataFrame(columns=["cartao_id", "nome"])

# Carregar os dados em DataFrames
logs = get_logs()
df_logs = pd.DataFrame(logs)
df_users = get_users()

# Converter data_horario para datetime
df_logs["data_horario"] = pd.to_datetime(df_logs["data_horario"])

# ================================
# 📊 Análise de acessos por dia
# ================================
def acessos_por_dia(data):
    df_dia = df_logs[df_logs["data_horario"].dt.date == pd.to_datetime(data).date()]
    entradas = df_dia[df_dia["tipo_operacao"] == "entrada"].shape[0]
    saidas = df_dia[df_dia["tipo_operacao"] == "saida"].shape[0]

    print(f"📅 Data: {data}")
    print(f"✅ Entradas: {entradas}")
    print(f"🚪 Saídas: {saidas}")

# ================================
# ⏳ Tempo dentro da sala por colaborador
# ================================
def tempo_na_sala():
    for _, row in df_users.iterrows():
        colaborador = row["nome"]
        df_user = df_logs[df_logs["nome"] == colaborador].sort_values("data_horario")
        total_tempo = pd.Timedelta(0)

        entrada_time = None
        for _, log in df_user.iterrows():
            if log["tipo_operacao"] == "entrada":
                entrada_time = log["data_horario"]
            elif log["tipo_operacao"] == "saida" and entrada_time:
                total_tempo += log["data_horario"] - entrada_time
                entrada_time = None

        print(f"⏳ {colaborador} permaneceu na sala por: {total_tempo}")

# Exemplo de uso
if __name__ == "__main__":
    acessos_por_dia("2025-04-03")  # Insira a data desejada
    tempo_na_sala()  # Analisa todos os colaboradores
