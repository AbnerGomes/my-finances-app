import os
import threading
from urllib.parse import urlparse
import psycopg2
from psycopg2.pool import ThreadedConnectionPool, PoolError

# Pegando a URL do banco via variável de ambiente
DATABASE_URL = os.environ['DATABASE_URL']

# (Opcional) URL fixa — apenas para testes locais
# DATABASE_URL = "postgres://usuario:senha@host:porta/database"

# ============================================================
# Pool de conexões — antes cada get_connection() abria uma conexão
# TCP/TLS nova do zero (psycopg2.connect direto), a cada chamada, em
# qualquer lugar do código. Páginas que fazem várias consultas na
# mesma requisição (despesas, receitas, extrato, configurações)
# ficavam visivelmente lentas (8-18s+, chegando a dar timeout) só
# com esse overhead de abrir conexão repetido várias vezes.
#
# Agora as conexões são reaproveitadas de um pool por processo (cada
# worker do gunicorn importa este módulo uma vez, então cada um tem o
# seu). O tamanho máximo é conservador de propósito — o Postgres do
# Render usado em produção tinha max_connections=100 numa checagem
# feita durante o diagnóstico, e isso precisa sobrar folga mesmo
# rodando vários workers ao mesmo tempo.
#
# Criado sob demanda (lazy) na primeira chamada, não na importação do
# módulo — se criasse na importação e o banco estivesse
# temporariamente fora do ar, o processo inteiro falharia ao subir,
# em vez de só a primeira requisição que precisasse do banco (mesmo
# comportamento de antes, que também só falhava por request).
# ============================================================
_POOL_MIN = int(os.environ.get('DB_POOL_MIN_CONN', '1'))
_POOL_MAX = int(os.environ.get('DB_POOL_MAX_CONN', '10'))

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:  # checagem dupla — evita duas threads criando dois pools
                _pool = ThreadedConnectionPool(_POOL_MIN, _POOL_MAX, DATABASE_URL)
    return _pool


class _PooledConnection:
    """Fina camada sobre uma conexão emprestada do pool: repassa tudo
    (cursor, commit, rollback, closed, etc.) pra conexão real — só
    troca o que `close()` faz. Em vez de fechar a conexão de verdade,
    devolve ela pro pool pra ser reaproveitada na próxima chamada.

    Idempotente de propósito: existem trechos no código (ex.:
    cadastrar_usuario/cadastrar_conjuge) que chamam close() duas
    vezes no mesmo caminho — um close() explícito dentro de um try,
    seguido do close() do finally, que roda de qualquer jeito. Com
    conexão "crua" isso não dava problema (fechar 2x é no-op). Já
    devolver a MESMA conexão pro pool duas vezes seria grave: o pool
    passaria a entregar essa conexão pra duas requisições diferentes
    ao mesmo tempo, corrompendo os dados de quem usasse por último. O
    flag _closed abaixo evita isso.
    """

    def __init__(self, conn, pool_ref):
        self._conn = conn
        self._pool = pool_ref
        self._closed = False

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            # se sobrou uma transação aberta sem commit/rollback
            # explícito (algum caminho de erro que não trata isso, ou
            # uma consulta simples que só fecha sem commitar), devolve
            # pro pool já limpa — senão o próximo request que pegar
            # essa mesma conexão herdaria uma transação pendente de
            # outro request
            if not self._conn.closed:
                self._conn.rollback()
        except Exception:
            pass
        finally:
            self._pool.putconn(self._conn)

    def __getattr__(self, nome):
        return getattr(self._conn, nome)


def get_connection():
    """Retorna uma conexão com o banco PostgreSQL — do pool sempre que
    possível. Mesmo contrato de antes (retorna None se não conseguir
    conectar de jeito nenhum, chamador já espera isso)."""
    try:
        conn = _get_pool().getconn()
        return _PooledConnection(conn, _get_pool())
    except PoolError as e:
        # pool sem nenhuma conexão livre no momento (pico de uso
        # concorrente) — em vez de falhar a requisição, abre uma
        # conexão avulsa só pra essa chamada, do jeito que o app
        # inteiro funcionava antes de existir pool. close() nela fecha
        # de verdade (não devolve a lugar nenhum, já que não veio de
        # lugar nenhum) — não precisa do wrapper acima.
        print("Pool de conexões esgotado, abrindo conexão avulsa:", e)
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as e2:
            print("Erro ao conectar ao banco (avulsa):", e2)
            return None
    except Exception as e:
        print("Erro ao conectar ao banco:", e)
        return None
