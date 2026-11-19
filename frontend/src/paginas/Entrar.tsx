// Tela 01 – Login (infra mínima — sem UC na ERS). "Esqueci minha senha" está
// fora do escopo (decisão Q7). Erro junto ao campo (ERS 3.1).
import { FormEvent, useState } from "react";
import { ErroApi } from "../api";
import { Botao, Campo, Logo } from "../componentes";
import { useSessao } from "../contextos/Sessao";
import { ir, lerRota } from "../navegacao";

export default function Entrar({ depois }: { depois?: string }) {
  const { entrar } = useSessao();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(ev: FormEvent) {
    ev.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await entrar(email, senha);
      if (depois) ir(lerRota(`#${depois}`), { substituir: true });
      else ir({ tela: "inicio" }, { substituir: true });
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : "Não foi possível entrar.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="tela tela--branco">
      <main className="tela__conteudo pagina-acesso">
        <Logo />
        <h1 className="pagina-acesso__titulo">Bem-vindo ao BurguerJá</h1>
        <p className="pagina-acesso__subtitulo">Entre para fazer seu pedido</p>
        <form onSubmit={enviar} className="pilha" noValidate>
          <Campo rotulo="E-mail" type="email" autoComplete="email" inputMode="email" value={email}
            onChange={(e) => setEmail(e.target.value)} placeholder="voce@email.com" required />
          <Campo rotulo="Senha" type="password" autoComplete="current-password" value={senha}
            onChange={(e) => setSenha(e.target.value)} erro={erro} required />
          <Botao type="submit" largo carregando={enviando} disabled={!email || !senha}>Entrar</Botao>
        </form>
        <Botao variante="texto" largo onClick={() => ir({ tela: "inicio" })}>Ver o cardápio sem entrar</Botao>
        <p className="pagina-acesso__rodape">
          Não tem conta? <a href="#/cadastro" className="link">Criar conta</a>
        </p>
      </main>
    </div>
  );
}
