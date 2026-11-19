"""A conexão da requisição pode ser usada em outra thread (infraestrutura, sem UC na ERS).

No uvicorn, o FastAPI abre a conexão (dependência `seguranca.conexao`) numa
thread e executa a rota em outra. Antes da correção em `db.conectar`, isso dava
ProgrammingError e, em seguida, "database is locked" para as outras requisições.
"""

import threading

from app import seguranca


def test_conexao_da_requisicao_funciona_em_outra_thread(client):
    dependencia = seguranca.conexao()
    conn = next(dependencia)  # aberta nesta thread
    erros: list[Exception] = []

    def rota():
        try:
            conn.execute("INSERT INTO cliente (nome, email, senha_hash, termos_aceitos_em) "
                         "VALUES ('X', 'x@exemplo.com', 'h', '2026-01-01T00:00:00+00:00')")
        except Exception as e:  # noqa: BLE001
            erros.append(e)

    t = threading.Thread(target=rota)
    t.start()
    t.join()
    next(dependencia, None)  # commit e fechamento, como no fim da requisição
    assert erros == []
    assert client.get("/api/health").status_code == 200
