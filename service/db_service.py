import os 
from urllib.parse import urlparse
import psycopg2

# Pegando a URL do banco via variável de ambiente
DATABASE_URL = os.environ['DATABASE_URL'] 

# (Opcional) URL fixa — apenas para testes locais
# DATABASE_URL = "postgres://usuario:senha@host:porta/database"

def get_connection():
    """Retorna uma conexão com o banco PostgreSQL."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print("Erro ao conectar ao banco:", e)
        return None
