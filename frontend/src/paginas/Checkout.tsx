// Finalizar pedido – UC28. Sem wireframe próprio: segue o estilo das telas
// 03 (zona de entrega), 06 (resumo) e 08 (opções em cartão).
// - Passo 2: resumo do carrinho. Passo 3: opções de atendimento da unidade (RN-04).
// - Passos 4–7: entrega → endereço salvo → distância, taxa e tempo estimado (RNF-06).
// - A1: retirada/drive-thru sem endereço nem taxa. E1: carrinho vazio (RF-07).
// - E2: endereço fora do raio (RF-06): aviso junto ao endereço e não deixa confirmar.
// - Passos 8–9: total e confirmação; o servidor recalcula e exige o mesmo total (RNF-26).
// A2 (novo endereço) depende do UC33 e A3 (cupom) do UC30, ainda não implementados.
import { useEffect, useState } from "react";
import { api, Endereco, ErroApi, Previa, TipoAtendimento } from "../api";
import {
  Aviso, Botao, Carregando, Cartao, EstadoVazio, IconeSacola, OpcaoSelecao, ResumoValores, Selo, Tela,
} from "../componentes";
import { useCarrinho } from "../contextos/Carrinho";
import { distancia, enderecoCurto, NOME_ATENDIMENTO, reais } from "../formatar";
import { ir } from "../navegacao";
import { guardarPedido } from "./PedidoRecebido";

const DESCRICAO_ATENDIMENTO: Record<TipoAtendimento, string> = {
  ENTREGA: "Receba no endereço escolhido",
  RETIRADA: "Busque no balcão da unidade, sem taxa",
  DRIVE_THRU: "Retire sem sair do carro, sem taxa",
};

type Erro = { mensagem: string; motivo?: string };

export default function Checkout() {
  const { recarregar: recarregarCarrinho } = useCarrinho();
  const [base, setBase] = useState<Previa | null>(null);       // resumo + opções (passos 2–3)
  const [previa, setPrevia] = useState<Previa | null>(null);   // valores da escolha atual (passos 6–8)
  const [tipo, setTipo] = useState<TipoAtendimento | null>(null);
  const [enderecos, setEnderecos] = useState<Endereco[] | null>(null);
  const [enderecoId, setEnderecoId] = useState<number | null>(null);
  const [erroInicial, setErroInicial] = useState<Erro | null>(null);
  const [erroEscolha, setErroEscolha] = useState<Erro | null>(null);
  const [calculando, setCalculando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [avisoValores, setAvisoValores] = useState(false);

  // Passos 1–3: a retirada existe em toda unidade, então serve para obter o resumo e as opções.
  useEffect(() => {
    api.previa("RETIRADA", null).then(setBase).catch((e) =>
      setErroInicial(e instanceof ErroApi ? { mensagem: e.message, motivo: e.motivo } : { mensagem: String(e) }));
  }, []);

  async function calcular(t: TipoAtendimento, endereco: number | null) {
    setPrevia(null);
    setErroEscolha(null);
    if (t === "ENTREGA" && endereco === null) return;
    setCalculando(true);
    try {
      setPrevia(await api.previa(t, endereco));
    } catch (e) {
      setErroEscolha(e instanceof ErroApi ? { mensagem: e.message, motivo: e.motivo } : { mensagem: String(e) });
    } finally {
      setCalculando(false);
    }
  }

  function escolherTipo(t: TipoAtendimento) {
    setTipo(t);
    setAvisoValores(false);
    if (t === "ENTREGA" && enderecos === null) {
      api.enderecos().then(setEnderecos).catch(() => setEnderecos([]));
    }
    calcular(t, t === "ENTREGA" ? enderecoId : null);
  }

  function escolherEndereco(id: number) {
    setEnderecoId(id);
    setAvisoValores(false);
    calcular("ENTREGA", id);
  }

  async function confirmar() {
    if (!previa || !tipo) return;
    setConfirmando(true);
    setErroEscolha(null);
    try {
      const pedido = await api.confirmarPedido(tipo, tipo === "ENTREGA" ? enderecoId : null, previa.total_centavos);
      guardarPedido(pedido, previa.carrinho.unidade?.nome ?? "");
      await recarregarCarrinho().catch(() => null);
      ir({ tela: "pedido-recebido", pedidoId: pedido.id }, { substituir: true });
    } catch (e) {
      if (e instanceof ErroApi && e.motivo === "valores_mudaram") {
        setAvisoValores(true);  // RNF-26: mostra os valores novos antes de cobrar
        await calcular(tipo, tipo === "ENTREGA" ? enderecoId : null);
      } else {
        setErroEscolha(e instanceof ErroApi ? { mensagem: e.message, motivo: e.motivo } : { mensagem: String(e) });
      }
    } finally {
      setConfirmando(false);
    }
  }

  if (erroInicial) {
    const vazio = erroInicial.motivo === "carrinho_vazio";  // E1
    return (
      <Tela titulo="Finalizar pedido" aoVoltar={() => ir({ tela: "sacola" })}>
        {vazio ? (
          <EstadoVazio icone={<IconeSacola tamanho={40} />} titulo="Sua sacola está vazia"
            texto="Adicione itens do cardápio para finalizar um pedido."
            acao={<Botao onClick={() => ir({ tela: "cardapio" })}>Ver cardápio</Botao>} />
        ) : (
          <Aviso tom="erro">{erroInicial.mensagem}</Aviso>
        )}
      </Tela>
    );
  }
  if (!base) return <Tela titulo="Finalizar pedido"><Carregando /></Tela>;

  const carrinho = (previa ?? base).carrinho;
  const pronto = previa !== null && !calculando && previa.tipo_atendimento === tipo;
  const linhas = previa
    ? [
        { rotulo: "Subtotal", centavos: previa.subtotal_centavos },
        ...(previa.tipo_atendimento === "ENTREGA" ? [{ rotulo: "Taxa de entrega", centavos: previa.taxa_entrega_centavos }] : []),
        ...(previa.desconto_cupom_centavos > 0
          ? [{ rotulo: "Desconto (cupom)", centavos: previa.desconto_cupom_centavos, negativo: true }]
          : []),
        { rotulo: "Total", centavos: previa.total_centavos, destaque: true },
      ]
    : [{ rotulo: "Subtotal", centavos: base.subtotal_centavos }];

  return (
    <Tela titulo="Finalizar pedido" subtitulo={carrinho.unidade?.nome} aoVoltar={() => ir({ tela: "sacola" })}
      rodape={
        <Botao largo carregando={confirmando} disabled={!pronto} onClick={confirmar}>
          {pronto ? `Confirmar pedido • ${reais(previa.total_centavos)}` : "Confirmar pedido"}
        </Botao>
      }>
      {/* Passo 2: resumo */}
      <section>
        <h2 className="titulo-secao">Resumo</h2>
        <Cartao>
          <ul className="lista-resumo">
            {carrinho.itens.map((i) => (
              <li key={i.id}>
                <span>
                  {i.quantidade}x {i.nome}
                  {i.observacao ? <small className="texto-fraco"> • {i.observacao}</small> : null}
                </span>
                <span>{reais(i.valor_final_centavos)}</span>
              </li>
            ))}
          </ul>
        </Cartao>
        {carrinho.avisos.map((a) => <Aviso key={a} tom="aviso">{a}</Aviso>)}
      </section>

      {/* Passo 3: atendimento */}
      <section className="pilha">
        <h2 className="titulo-secao">Como você quer receber?</h2>
        {base.tipos_atendimento_disponiveis.map((t) => (
          <OpcaoSelecao key={t} nome="atendimento" selecionada={tipo === t} aoSelecionar={() => escolherTipo(t)}
            titulo={NOME_ATENDIMENTO[t]} descricao={DESCRICAO_ATENDIMENTO[t]} />
        ))}
      </section>

      {/* Passo 5: endereços salvos */}
      {tipo === "ENTREGA" ? (
        <section className="pilha">
          <h2 className="titulo-secao">Endereço de entrega</h2>
          {enderecos === null ? <Carregando texto="Buscando seus endereços…" /> : null}
          {enderecos?.length === 0 ? (
            <Aviso tom="info">
              Você ainda não tem endereços salvos, e o cadastro de endereços ainda não está disponível no app.
              Por enquanto, escolha retirada{base.tipos_atendimento_disponiveis.includes("DRIVE_THRU") ? " ou drive-thru" : ""}.
            </Aviso>
          ) : null}
          {enderecos?.map((e) => (
            <div key={e.id} className="pilha pilha--justa">
              <OpcaoSelecao nome="endereco" selecionada={enderecoId === e.id} aoSelecionar={() => escolherEndereco(e.id)}
                titulo={enderecoCurto(e)} descricao={`${e.bairro} • ${e.cidade} - ${e.estado} • CEP ${e.cep}`} />
              {enderecoId === e.id && erroEscolha ? <Aviso tom="erro">{erroEscolha.mensagem}</Aviso> : null}
              {enderecoId === e.id && previa?.entrega ? (
                <Aviso tom="sucesso">
                  Dentro da zona de entrega • {distancia(previa.entrega.distancia_m)} • Taxa: {reais(previa.taxa_entrega_centavos)}
                </Aviso>
              ) : null}
            </div>
          ))}
        </section>
      ) : null}

      {tipo !== "ENTREGA" && erroEscolha ? <Aviso tom="erro">{erroEscolha.mensagem}</Aviso> : null}

      {/* Passos 7–8: tempo estimado e total */}
      <section className="pilha">
        <h2 className="titulo-secao">Valores</h2>
        {avisoValores ? (
          <Aviso tom="aviso">Os preços mudaram desde que você abriu esta tela. Confira o novo total antes de confirmar.</Aviso>
        ) : null}
        {calculando ? <Carregando texto="Calculando…" /> : null}
        <Cartao>
          <ResumoValores linhas={linhas} />
        </Cartao>
        {previa?.entrega ? (
          <p className="linha-centro">
            <Selo tom="aviso">Tempo estimado: cerca de {previa.entrega.tempo_estimado_min} min</Selo>
          </p>
        ) : null}
        {previa?.entrega ? (
          <p className="texto-fraco">O tempo de entrega é uma estimativa e pode variar.</p>
        ) : null}
      </section>
    </Tela>
  );
}
