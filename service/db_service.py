import os 
from urllib.parse import urlparse
import psycopg2

# Pegando a URL do banco via variável de ambiente
# DATABASE_URL = "postgresql://abner:J9a3Yfa4Oziu2VTWjhoHG6W6p6s1VdrD@dpg-cvqi6815pdvs73ae110g-a.oregon-postgres.render.com/fin_db_l8qs"
DATABASE_URL = "postgresql://abner:ofthekingthepowerthemendandthebesterdthekingthefarythesmain@node228283-abner-pg.ce.br.saveincloud.net.br:11032/my_fin_db"

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
