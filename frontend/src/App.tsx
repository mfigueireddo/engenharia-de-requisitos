// Página de teste de integração front-end ↔ API ↔ banco.
// Remover quando as telas reais (ERS, seção 3.1) começarem a ser implementadas.
import { FormEvent, useEffect, useState } from "react";
import { api, Recado } from "./api";

export default function App() {
  const [status, setStatus] = useState("verificando…");
  const [recados, setRecados] = useState<Recado[]>([]);
  const [texto, setTexto] = useState("");
  const [erro, setErro] = useState("");

  async function carregar() {
    try {
      setStatus((await api.health()).status);
      setRecados(await api.listarRecados());
      setErro("");
    } catch (e) {
      setStatus("fora do ar");
      setErro(String(e));
    }
  }

  useEffect(() => {
    carregar();
  }, []);

  async function enviar(ev: FormEvent) {
    ev.preventDefault();
    if (!texto.trim()) return;
    try {
      await api.criarRecado(texto.trim());
      setTexto("");
      await carregar();
    } catch (e) {
      setErro(String(e));
    }
  }

  return (
    <main className="pagina">
      <h1>BurguerJá</h1>
      <p className="subtitulo">Teste de integração: front-end → API → banco</p>

      <p className={`status ${status === "ok" ? "ok" : "falha"}`}>API: {status}</p>

      <form onSubmit={enviar} className="form">
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escreva um recado"
          maxLength={200}
        />
        <button type="submit">Salvar</button>
      </form>
      {erro && <p className="erro">{erro}</p>}

      <ul className="lista">
        {recados.map((r) => (
          <li key={r.id}>
            <span>{r.texto}</span>
            <small>{r.criado_em}</small>
          </li>
        ))}
        {recados.length === 0 && <li className="vazio">Nenhum recado salvo ainda.</li>}
      </ul>
    </main>
  );
}
