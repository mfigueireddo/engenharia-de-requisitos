// Tela 05 – Detalhe do item: quantidade, observação e "Adicionar à sacola"
// (UC27, infra mínima — sem UC na ERS). O valor mostrado é só uma prévia
// (RF-02); o servidor recalcula tudo (RF-13, RNF-14).
import { useState } from "react";
import { api, ErroApi } from "../api";
import {
  Aviso, Botao, CampoTexto, Carregando, EstadoVazio, Folha, FotoProduto, IconeVoltar, Preco, SeletorQuantidade, Selo,
} from "../componentes";
import { useCarrinho } from "../contextos/Carrinho";
import { useSessao } from "../contextos/Sessao";
import { reais } from "../formatar";
import { caminhoDe, ir, voltar } from "../navegacao";
import { useCarregar } from "../useCarregar";

const MAX_OBSERVACAO = 200;

export default function DetalheItem({ produtoId }: { produtoId: number }) {
  const { cliente, unidadeId } = useSessao();
  const { atualizar } = useCarrinho();
  const { dados, erro: erroCarga, carregando } = useCarregar(
    () => (unidadeId ? api.cardapio(unidadeId) : Promise.resolve(null)),
    [unidadeId],
  );
  const [quantidade, setQuantidade] = useState(1);
  const [observacao, setObservacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [outraUnidade, setOutraUnidade] = useState(false);

  const produto = dados?.produtos.find((p) => p.id === produtoId);
  const aoVoltar = () => voltar({ tela: "cardapio" });

  async function adicionar(esvaziarAntes = false) {
    if (!produto) return;
    if (!cliente) {  // RN-01: visitante vê o cardápio, mas precisa entrar para pedir
      ir({ tela: "entrar", depois: caminhoDe({ tela: "item", produtoId }).slice(1) });
      return;
    }
    setErro(null);
    setEnviando(true);
    try {
      if (esvaziarAntes) await api.esvaziarCarrinho();
      atualizar(await api.adicionarItem(produto.id, quantidade, observacao.trim() || null));
      ir({ tela: "cardapio" }, { substituir: true });
    } catch (e) {
      if (e instanceof ErroApi && e.status === 409 && e.message.includes("outra unidade")) setOutraUnidade(true);
      else setErro(e instanceof ErroApi ? e.message : "Não foi possível adicionar o item.");
    } finally {
      setEnviando(false);
    }
  }

  if (carregando) return <div className="tela"><Carregando /></div>;
  if (!produto) {
    return (
      <div className="tela">
        <main className="tela__conteudo">
          <EstadoVazio titulo="Item indisponível" texto={erroCarga ?? "Este item não está no cardápio desta unidade."}
            acao={<Botao onClick={() => ir({ tela: "cardapio" })}>Voltar ao cardápio</Botao>} />
        </main>
      </div>
    );
  }

  const temDesconto = produto.desconto_centavos > 0;
  return (
    <div className="tela tela--com-rodape">
      <div className="detalhe__foto">
        <button type="button" className="detalhe__voltar" aria-label="Voltar" onClick={aoVoltar}><IconeVoltar /></button>
        <FotoProduto nome={produto.nome} tamanho="lg" />
      </div>
      <main className="tela__conteudo pilha">
        <div>
          <h1 className="detalhe__nome">{produto.nome}</h1>
          {produto.descricao ? <p className="texto-suave">{produto.descricao}</p> : null}
          <div className="detalhe__preco">
            <Preco final={produto.preco_final_centavos} cheio={produto.preco_centavos} tamanho="lg" />
            {temDesconto ? <Selo tom="aviso">Promoção</Selo> : null}
          </div>
        </div>

        {produto.tipo === "COMBO" ? (
          <div>
            <h2 className="titulo-secao">Neste combo</h2>
            <ul className="lista-componentes">
              {produto.componentes.map((c) => (
                <li key={c.produto_id}>{c.quantidade}x {c.nome}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="linha-entre">
          <strong>Quantidade</strong>
          <SeletorQuantidade valor={quantidade} aoMudar={setQuantidade} />
        </div>
        <CampoTexto rotulo="Observação" placeholder="Ex.: sem cebola" rows={2} maxLength={MAX_OBSERVACAO}
          value={observacao} onChange={(e) => setObservacao(e.target.value)} />
        {erro ? <Aviso tom="erro">{erro}</Aviso> : null}
      </main>
      <div className="tela__rodape">
        <Botao largo carregando={enviando} onClick={() => adicionar()}>
          {cliente ? `Adicionar à sacola • ${reais(quantidade * produto.preco_final_centavos)}` : "Entrar para adicionar"}
        </Botao>
      </div>

      <Folha aberta={outraUnidade} aoFechar={() => setOutraUnidade(false)} titulo="Sua sacola é de outra unidade">
        <p className="texto-suave">
          Cada pedido é de uma única unidade. Para pedir em {dados?.unidade.nome}, os itens que estão na
          sua sacola serão removidos. Isso não pode ser desfeito.
        </p>
        <Botao largo carregando={enviando} onClick={() => { setOutraUnidade(false); adicionar(true); }}>
          Esvaziar sacola e adicionar
        </Botao>
        <Botao variante="texto" largo onClick={() => setOutraUnidade(false)}>Manter minha sacola</Botao>
      </Folha>
    </div>
  );
}
