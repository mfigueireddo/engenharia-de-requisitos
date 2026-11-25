// Tela 13 — histórico de pedidos (UC31, passos 1–3; RF-19 e RN-02).
import { api, PedidoResumo } from "../api";
import { Aviso, Botao, Carregando, Cartao, EstadoVazio, IconePedidos, Selo, Tela } from "../componentes";
import { dataHora, NOME_ATENDIMENTO } from "../formatar";
import { ir } from "../navegacao";
import { useCarregar } from "../useCarregar";

export const STATUS_PEDIDO: Record<PedidoResumo["status"], { nome: string; tom: "sucesso" | "erro" | "aviso" | "neutro" }> = {
  RECEBIDO: { nome: "Recebido", tom: "aviso" },
  PAGO: { nome: "Pago", tom: "sucesso" },
  EM_PREPARO: { nome: "Em preparo", tom: "aviso" },
  PRONTO: { nome: "Pronto", tom: "sucesso" },
  SAIU_PARA_ENTREGA: { nome: "Saiu para entrega", tom: "sucesso" },
  ENTREGUE: { nome: "Entregue", tom: "sucesso" },
  CANCELADO: { nome: "Cancelado", tom: "erro" },
};

function CartaoPedido({ pedido }: { pedido: PedidoResumo }) {
  const status = STATUS_PEDIDO[pedido.status];
  return (
    <Cartao aoClicar={() => ir({ tela: "pedido", pedidoId: pedido.id })}>
      <div className="pedido-lista__cabecalho">
        <div>
          <strong>Pedido #{pedido.id}</strong>
          <p className="texto-suave">{dataHora(pedido.criado_em)}</p>
        </div>
        <Selo tom={status.tom}>{status.nome}</Selo>
      </div>
      <p className="pedido-lista__unidade">{pedido.unidade.nome}</p>
      <p className="texto-suave">{NOME_ATENDIMENTO[pedido.tipo_atendimento]}</p>
      <p className="texto-fraco">Atualizado {dataHora(pedido.atualizado_em)}</p>
    </Cartao>
  );
}
export default function Pedidos() {
  const { dados: pedidos, erro, carregando, recarregar } = useCarregar(api.pedidos, []);

  return (
    <Tela titulo="Meus pedidos" semVoltar aba="pedidos">
      {carregando ? <Carregando /> : null}
      {erro ? <Aviso tom="erro" acao={<Botao variante="texto" onClick={recarregar}>Tentar de novo</Botao>}>{erro}</Aviso> : null}
      {!carregando && !erro && pedidos?.length === 0 ? (
        <EstadoVazio
          icone={<IconePedidos tamanho={40} />}
          titulo="Você ainda não fez pedidos"
          texto="Quando você confirmar um pedido, ele aparecerá aqui para acompanhamento."
          acao={<Botao onClick={() => ir({ tela: "cardapio" })}>Ver cardápio</Botao>}
        />
      ) : null}
      <div className="pilha">
        {pedidos?.map((pedido) => <CartaoPedido key={pedido.id} pedido={pedido} />)}
      </div>
    </Tela>
  );
}
