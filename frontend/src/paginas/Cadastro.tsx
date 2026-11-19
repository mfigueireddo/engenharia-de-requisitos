// Criar conta (sem wireframe; infra mínima — sem UC na ERS).
// RNF-08 / RNF-25: o cadastro só segue com o aceite dos termos e da política de privacidade.
import { FormEvent, useState } from "react";
import { api, ErroApi } from "../api";
import { Aviso, Botao, Campo, Tela } from "../componentes";
import { useSessao } from "../contextos/Sessao";
import { ir } from "../navegacao";

export default function Cadastro() {
  const { entrar } = useSessao();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [aceite, setAceite] = useState(false);
  const [erro, setErro] = useState<{ campo: "email" | "geral"; texto: string } | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(ev: FormEvent) {
    ev.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.cadastrar(nome, email, senha, aceite);
      await entrar(email, senha);
      ir({ tela: "inicio" }, { substituir: true });
    } catch (e) {
      const texto = e instanceof ErroApi ? e.message : "Não foi possível criar a conta.";
      setErro({ campo: e instanceof ErroApi && e.status === 409 ? "email" : "geral", texto });
    } finally {
      setEnviando(false);
    }
  }

  const completo = nome.trim() && email.trim() && senha && aceite;

  return (
    <Tela titulo="Criar conta" aoVoltar={() => ir({ tela: "entrar" })}>
      <form onSubmit={enviar} className="pilha" noValidate>
        <Campo rotulo="Nome" autoComplete="name" value={nome} onChange={(e) => setNome(e.target.value)} maxLength={100} />
        <Campo rotulo="E-mail" type="email" autoComplete="email" inputMode="email" value={email}
          onChange={(e) => setEmail(e.target.value)} erro={erro?.campo === "email" ? erro.texto : null} />
        <Campo rotulo="Senha" type="password" autoComplete="new-password" value={senha}
          onChange={(e) => setSenha(e.target.value)} maxLength={72} />
        <label className="caixa-marcar">
          <input type="checkbox" checked={aceite} onChange={(e) => setAceite(e.target.checked)} />
          <span>Li e aceito os termos de uso e a política de privacidade.</span>
        </label>
        {erro?.campo === "geral" ? <Aviso tom="erro">{erro.texto}</Aviso> : null}
        <p className="texto-fraco">O botão só é habilitado quando todos os campos estão preenchidos.</p>
        <Botao type="submit" largo carregando={enviando} disabled={!completo}>Criar conta</Botao>
      </form>
    </Tela>
  );
}
