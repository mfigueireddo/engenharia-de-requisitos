// Tela 04 – Cardápio da unidade escolhida (público, RN-01). Se o SGL estiver
// fora do ar, mostra o último cardápio e o horário dele (RNF-03).
import { useMemo, useState } from "react";
import { api } from "../api";
import {
  Aviso, BarraSacola, Botao, Carregando, Cartao, EstadoVazio, FotoProduto, IconeBusca, IconeLoja, Preco, Tela,
} from "../componentes";
import { useSessao } from "../contextos/Sessao";
import { dataHora } from "../formatar";
import { ir } from "../navegacao";
import { useCarregar } from "../useCarregar";

const TODAS = "Todos";

export default function Cardapio() {
  const { unidadeId } = useSessao();
  if (!unidadeId) {
    return (
      <Tela titulo="Cardápio" semVoltar aba="cardapio">
        <EstadoVazio icone={<IconeLoja tamanho={40} />} titulo="Escolha uma unidade"
          texto="O cardápio e os preços variam de loja para loja."
          acao={<Botao onClick={() => ir({ tela: "inicio" })}>Ver unidades</Botao>} />
      </Tela>
    );
  }
  return <CardapioDaUnidade unidadeId={unidadeId} />;
}

function CardapioDaUnidade({ unidadeId }: { unidadeId: number }) {
  const { dados, erro, carregando, recarregar } = useCarregar(() => api.cardapio(unidadeId), [unidadeId]);
  const [busca, setBusca] = useState("");
  const [categoria, setCategoria] = useState(TODAS);

  const categorias = useMemo(
    () => [TODAS, ...new Set(dados?.produtos.map((p) => p.categoria) ?? [])],
    [dados],
  );
  const visiveis = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR");
    return (dados?.produtos ?? []).filter(
      (p) =>
        (categoria === TODAS || p.categoria === categoria) &&
        (!termo || `${p.nome} ${p.descricao}`.toLocaleLowerCase("pt-BR").includes(termo)),
    );
  }, [dados, busca, categoria]);

  const subtitulo = dados ? `${dados.unidade.nome} • cardápio vigente` : undefined;

  return (
    <Tela titulo="Cardápio" subtitulo={subtitulo} semVoltar aba="cardapio">
      {carregando && !dados ? <Carregando /> : null}
      {erro ? (
        <Aviso tom="erro" acao={<Botao variante="texto" onClick={recarregar}>Tentar de novo</Botao>}>{erro}</Aviso>
      ) : null}
      {dados?.sgl_indisponivel ? (
        <Aviso tom="aviso">
          Não conseguimos falar com a loja agora. Mostrando o cardápio de {dataHora(dados.cardapio_atualizado_em)}.
        </Aviso>
      ) : null}

      {dados ? (
        <>
          <label className="busca">
            <IconeBusca tamanho={18} />
            <input type="search" placeholder="Buscar no cardápio" value={busca} onChange={(e) => setBusca(e.target.value)} />
          </label>
          <div className="chips" role="tablist" aria-label="Categorias">
            {categorias.map((c) => (
              <button key={c} type="button" role="tab" aria-selected={c === categoria}
                className={`chip ${c === categoria ? "chip--ativo" : ""}`} onClick={() => setCategoria(c)}>
                {c}
              </button>
            ))}
          </div>
          {visiveis.length === 0 ? (
            <EstadoVazio titulo="Nada encontrado" texto="Tente outra busca ou categoria." />
          ) : (
            <div className="grade-produtos">
              {visiveis.map((p) => (
                <Cartao key={p.id} className="cartao-produto" aoClicar={() => ir({ tela: "item", produtoId: p.id })}>
                  <FotoProduto nome={p.nome} />
                  <strong className="cartao-produto__nome">{p.nome}</strong>
                  <Preco final={p.preco_final_centavos} cheio={p.preco_centavos} />
                </Cartao>
              ))}
            </div>
          )}
        </>
      ) : null}
      <BarraSacola />
    </Tela>
  );
}
