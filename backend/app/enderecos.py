from pathlib import Path

ARQUIVO = Path(__file__).parent / "enderecos.txt"
# Novos nomes de campos conforme o protótipo
CAMPOS_OBRIGATORIOS = ["cep", "rua", "numero", "bairro", "cidade"]

def _ler_linhas() -> list[dict]:
    if not ARQUIVO.exists():
        ARQUIVO.write_text("", encoding="utf-8")
        return []
    enderecos = []
    for linha in ARQUIVO.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha: continue
        partes = linha.split("|")
        if len(partes) != 7: continue
        enderecos.append({
            "id": int(partes[0]), "cep": partes[1], "rua": partes[2],
            "numero": partes[3], "complemento": partes[4], "bairro": partes[5], "cidade": partes[6]
        })
    return enderecos

def _escrever_linhas(enderecos: list[dict]) -> None:
    linhas = [f"{e['id']}|{e['cep']}|{e['rua']}|{e['numero']}|{e['complemento']}|{e['bairro']}|{e['cidade']}" for e in enderecos]
    ARQUIVO.write_text("\n".join(linhas) + ("\n" if linhas else ""), encoding="utf-8")

def _proximo_id(enderecos: list[dict]) -> int:
    return max((e["id"] for e in enderecos), default=0) + 1

def _validar(dados: dict) -> dict:
    limpos = {}
    for campo in CAMPOS_OBRIGATORIOS + ["complemento"]:
        valor = str(dados.get(campo) or "").strip()
        limpos[campo] = valor.replace("|", "-")

    for campo in CAMPOS_OBRIGATORIOS:
        if not limpos[campo]:
            raise ValueError(f"Campo obrigatório vazio: {campo}")

    digitos_cep = "".join(filter(str.isdigit, limpos["cep"]))
    if len(digitos_cep) != 8:
        raise ValueError("CEP deve ter 8 dígitos.")
    limpos["cep"] = f"{digitos_cep[:5]}-{digitos_cep[5:]}"

    return limpos

def listar() -> list[dict]: return _ler_linhas()

def criar(dados: dict) -> dict:
    enderecos = _ler_linhas()
    novo = _validar(dados)
    novo["id"] = _proximo_id(enderecos)
    enderecos.append(novo)
    _escrever_linhas(enderecos)
    return novo

def editar(endereco_id: int, dados: dict) -> dict:
    enderecos = _ler_linhas()
    for i, e in enumerate(enderecos):
        if e["id"] == endereco_id:
            atualizado = _validar(dados)
            atualizado["id"] = endereco_id
            enderecos[i] = atualizado
            _escrever_linhas(enderecos)
            return atualizado
    raise LookupError("Endereço não encontrado.")

def remover(endereco_id: int) -> None:
    enderecos = _ler_linhas()
    novos = [e for e in enderecos if e["id"] != endereco_id]
    if len(novos) == len(enderecos): raise LookupError("Endereço não encontrado.")
    _escrever_linhas(novos)
