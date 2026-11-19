// Fim do UC28 (passo 11): pedido criado com status "RECEBIDO". No estilo da
// tela 10. O pagamento (tela 08) ainda não existe no back-end, então esta tela
// avisa que ele vem depois (decisão do humano nesta sessão).
import { Pedido } from "../api";
import { Aviso, Botao, Cartao, IconeCheck, ResumoValores, Selo } from "../componentes";
import { enderecoCurto, NOME_ATENDIMENTO, reais } from "../formatar";
import { ir } from "../navegacao";

type Guardado = { pedido: Pedido; unidade: string };
const chave = (id: number) => `burguerja.pedido.${id}`;

/** A API ainda não tem "ver pedido" (UC31); guardamos a resposta da confirmação nesta aba. */
export function guardarPedido(pedido: Pedido, unidade: string) {
  try {
    sessionStorage.setItem(chave(pedido.id), JSON.stringify({ pedido, unidade }));
  } catch {
    /* sem armazenamento: a tela mostra só o número */
  }
}

function lerPedido(id: number): Guardado | null {
  try {
    const t = sessionStorage.getItem(chave(id));
    return t ? (JSON.parse(t) as Guardado) : null;
  } catch {
    return null;
  }
}

export default function PedidoRecebido({ pedidoId }: { pedidoId: number }) {
  const guardado = lerPedido(pedidoId);
  const p = guardado?.pedido;

  return (
    <div className="tela tela--branco tela--com-rodape">
      <main className="tela__conteudo pagina-sucesso">
        <div className="pagina-sucesso__icone"><IconeCheck tamanho={48} /></div>
        <h1 className="pagina-sucesso__titulo">Pedido recebido!</h1>
        <p className="texto-suave">Pedido #{pedidoId}{guardado?.unidade ? ` • ${guardado.unidade}` : ""}</p>
        {p ? (
          <Selo tom="aviso">
            {p.entrega ? `Tempo estimado: cerca de ${p.entrega.tempo_estimado_min} min` : NOME_ATENDIMENTO[p.tipo_atendimento]}
          </Selo>
        ) : null}

        {p ? (
          <Cartao className="pagina-sucesso__resumo">
            <ul className="lista-resumo">
              {p.itens.map((i) => (
                <li key={i.id}><span>{i.quantidade}x {i.nome}</span><span>{reais(i.valor_final_centavos)}</span></li>
              ))}
            </ul>
            <ResumoValores linhas={[
              ...(p.taxa_entrega_centavos ? [{ rotulo: "Taxa de entrega", centavos: p.taxa_entrega_centavos }] : []),
              ...(p.desconto_cupom_centavos ? [{ rotulo: "Desconto (cupom)", centavos: p.desconto_cupom_centavos, negativo: true }] : []),
              { rotulo: "Total", centavos: p.total_centavos, destaque: true },
            ]} />
            {p.entrega ? <p className="texto-fraco">Entrega em {enderecoCurto(p.entrega.endereco)}</p> : null}
          </Cartao>
        ) : null}

        <Aviso tom="info">
          Próximo passo: o pagamento (Pix, cartão ou pontos). Essa etapa ainda está em desenvolvimento no app.
        </Aviso>
      </main>
      <div className="tela__rodape">
        <Botao largo onClick={() => ir({ tela: "inicio" }, { substituir: true })}>Voltar ao início</Botao>
      </div>
    </div>
  );
}
