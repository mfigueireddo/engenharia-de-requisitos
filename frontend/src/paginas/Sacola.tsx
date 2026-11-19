// Tela 06 – Sacola: UC29 (Gerenciar Itens do Carrinho).
// - Passos 1–3: o servidor recalcula cada item com os preços vigentes (RF-13).
// - Passo 4–6: alterar a quantidade; A1: zerar remove o item (RF-12).
// - A2: editar a observação, sem mudar o valor.
// - E1: carrinho vazio, com opção de voltar ao cardápio.
// - E2: item fora do cardápio — o servidor retira e manda um aviso.
// - E3: SGL fora do ar — mostra o horário do último cardápio (RNF-03).
// O cupom (UC30) entra nesta tela quando for implementado.
import { useState } from "react";
import { api, Carrinho, ErroApi, ItemCarrinho } from "../api";
import {
  Aviso, Botao, Carregando, Cartao, EstadoVazio, Folha, FotoProduto, IconeSacola, ResumoValores, SeletorQuantidade, Tela,
} from "../componentes";
import { useCarrinho } from "../contextos/Carrinho";
import { dataHora, reais } from "../formatar";
import { ir } from "../navegacao";
import { useCarregar } from "../useCarregar";

export default function Sacola() {
  const { atualizar } = useCarrinho();
  // Ao abrir a sacola, busca de novo para recalcular com o cardápio vigente (passo 2).
  const { dados: carrinho, setDados, erro: erroCarga, carregando, recarregar } = useCarregar(api.carrinho, []);
  const [ocupado, setOcupado] = useState<number | "todos" | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [confirmarEsvaziar, setConfirmarEsvaziar] = useState(false);

  async function executar(alvo: number | "todos", acao: () => Promise<Carrinho>) {
    setOcupado(alvo);
    setErro(null);
    try {
      const novo = await acao();
      setDados(novo);
      atualizar(novo);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : "Não foi possível atualizar a sacola.");
    } finally {
      setOcupado(null);
    }
  }

  if (carregando && !carrinho) return <Tela titulo="Sua sacola"><Carregando /></Tela>;
  if (erroCarga && !carrinho) {
    return (
      <Tela titulo="Sua sacola">
        <Aviso tom="erro" acao={<Botao variante="texto" onClick={recarregar}>Tentar de novo</Botao>}>{erroCarga}</Aviso>
      </Tela>
    );
  }
  if (!carrinho) return null;

  const avisos = (
    <>
      {carrinho.avisos.map((a) => <Aviso key={a} tom="aviso">{a}</Aviso>)}
      {carrinho.sgl_indisponivel ? (
        <Aviso tom="aviso">
          Não conseguimos atualizar os preços com a loja agora. Valores do cardápio de{" "}
          {dataHora(carrinho.cardapio_atualizado_em)}.
        </Aviso>
      ) : null}
      {erro ? <Aviso tom="erro">{erro}</Aviso> : null}
    </>
  );

  if (carrinho.itens.length === 0) {  // E1
    return (
      <Tela titulo="Sua sacola" aoVoltar={() => ir({ tela: "cardapio" })}>
        {avisos}
        <EstadoVazio icone={<IconeSacola tamanho={40} />} titulo="Sua sacola está vazia"
          texto="Escolha seus lanches no cardápio para começar o pedido."
          acao={<Botao onClick={() => ir({ tela: "cardapio" })}>Ver cardápio</Botao>} />
      </Tela>
    );
  }

  return (
    <Tela titulo="Sua sacola" subtitulo={carrinho.unidade?.nome}
      rodape={<Botao largo disabled={ocupado !== null} onClick={() => ir({ tela: "checkout" })}>Finalizar pedido</Botao>}>
      {avisos}
      <div className="pilha">
        {carrinho.itens.map((item) => (
          <LinhaItem key={item.id} item={item} ocupado={ocupado === item.id || ocupado === "todos"}
            aoMudarQuantidade={(q) =>
              executar(item.id, () => (q === 0 ? api.removerItem(item.id) : api.alterarItem(item.id, { quantidade: q })))}
            aoSalvarObservacao={(obs) => executar(item.id, () => api.alterarItem(item.id, { observacao: obs }))} />
        ))}
      </div>

      <Cartao>
        <ResumoValores linhas={[{ rotulo: "Subtotal", centavos: carrinho.subtotal_centavos, destaque: true }]} />
        <p className="texto-fraco">Taxa de entrega e total são calculados ao finalizar o pedido.</p>
      </Cartao>

      <Botao variante="texto" largo onClick={() => setConfirmarEsvaziar(true)}>Esvaziar sacola</Botao>
      <Folha aberta={confirmarEsvaziar} aoFechar={() => setConfirmarEsvaziar(false)} titulo="Esvaziar a sacola?">
        <p className="texto-suave">Todos os itens serão removidos. Isso não pode ser desfeito.</p>
        <Botao largo carregando={ocupado === "todos"}
          onClick={async () => { await executar("todos", api.esvaziarCarrinho); setConfirmarEsvaziar(false); }}>
          Esvaziar sacola
        </Botao>
        <Botao variante="texto" largo onClick={() => setConfirmarEsvaziar(false)}>Voltar</Botao>
      </Folha>
    </Tela>
  );
}

type PropsLinha = {
  item: ItemCarrinho;
  ocupado: boolean;
  aoMudarQuantidade: (q: number) => void;
  aoSalvarObservacao: (obs: string | null) => void;
};

function LinhaItem({ item, ocupado, aoMudarQuantidade, aoSalvarObservacao }: PropsLinha) {
  const [editando, setEditando] = useState(false);
  const [texto, setTexto] = useState(item.observacao ?? "");

  function salvar() {
    setEditando(false);
    const novo = texto.trim() || null;
    if (novo !== item.observacao) aoSalvarObservacao(novo);
  }

  return (
    <Cartao className={`item-sacola ${ocupado ? "item-sacola--ocupado" : ""}`}>
      <FotoProduto nome={item.nome} tamanho="sm" />
      <div className="item-sacola__meio">
        <strong>{item.nome}</strong>
        {item.componentes.length ? (
          <span className="texto-fraco">{item.componentes.map((c) => `${c.quantidade}x ${c.nome}`).join(", ")}</span>
        ) : null}
        {editando ? (
          <div className="item-sacola__obs-edicao">
            <input autoFocus className="campo__entrada campo__entrada--sm" value={texto} maxLength={200}
              placeholder="Ex.: sem cebola" aria-label={`Observação de ${item.nome}`}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") salvar(); if (e.key === "Escape") setEditando(false); }} />
            <Botao variante="texto" onClick={salvar}>Salvar</Botao>
          </div>
        ) : (
          <button type="button" className="item-sacola__obs" onClick={() => { setTexto(item.observacao ?? ""); setEditando(true); }}>
            {item.observacao ? `Obs.: ${item.observacao}` : "+ Adicionar observação"}
          </button>
        )}
        <SeletorQuantidade valor={item.quantidade} minimo={0} tamanho="sm" desabilitado={ocupado}
          aoMudar={aoMudarQuantidade} />
      </div>
      <strong className="item-sacola__valor">{reais(item.valor_final_centavos)}</strong>
    </Cartao>
  );
}
