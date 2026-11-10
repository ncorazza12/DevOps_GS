from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="CitizenTech - Ocorrências Urbanas", version="1.0.0")


class OcorrenciaIn(BaseModel):
    titulo: str = Field(min_length=3, max_length=100)
    descricao: str = Field(min_length=3, max_length=500)
    categoria: str = Field(default="outros", max_length=50)


class Ocorrencia(OcorrenciaIn):
    id: int
    status: str = "aberta"


_db: dict[int, Ocorrencia] = {}
_next_id = 1


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ocorrencias")
def listar():
    return list(_db.values())


@app.get("/ocorrencias/{ocorrencia_id}")
def obter(ocorrencia_id: int):
    if ocorrencia_id not in _db:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    return _db[ocorrencia_id]


@app.post("/ocorrencias", status_code=200)
def criar(payload: OcorrenciaIn):
    global _next_id
    nova = Ocorrencia(id=_next_id, **payload.model_dump())
    _db[_next_id] = nova
    _next_id += 1
    return nova
