from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_criar_e_listar_ocorrencia():
    r = client.post("/ocorrencias", json={
        "titulo": "Buraco na rua", "descricao": "Buraco grande na Av. Paulista",
        "categoria": "via"})
    assert r.status_code == 201
    novo_id = r.json()["id"]

    lista = client.get("/ocorrencias")
    assert lista.status_code == 200
    assert any(o["id"] == novo_id for o in lista.json())


def test_ocorrencia_inexistente():
    assert client.get("/ocorrencias/99999").status_code == 404


def test_validacao_titulo_curto():
    r = client.post("/ocorrencias", json={"titulo": "ab", "descricao": "xyz"})
    assert r.status_code == 422
