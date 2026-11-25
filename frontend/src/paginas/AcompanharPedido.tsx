// Tela 11 — detalhe e linha do tempo do pedido (UC31, passos 3–8).
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ErroApi, Pedido } from "../api";
import { Aviso, Carregando, Cartao, ResumoValores, Selo, Tela } from "../componentes";
import { dataHora, enderecoCurto, NOME_ATENDIMENTO, reais } from "../formatar";
import { voltar } from "../navegacao";
import { STATUS_PEDIDO } from "./Pedidos";

export default function AcompanharPedido({ pedidoId }: { pedidoId: number }) {
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [desconectado, setDesconectado] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<number | null>(null);
  const ativoRef = useRef(false);

  const carregar = useCallback(async () => {
    try {
      setPedido(await api.pedido(pedidoId));
      setErro(null);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : String(e));
    } finally {
      setCarregando(false);
    }
  }, [pedidoId]);

  const conectar = useCallback(() => {
    if (!ativoRef.current) return;
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (socketRef.current) socketRef.current.close();
    const socket = api.conectarPedido(pedidoId);
    socketRef.current = socket;
    socket.onopen = () => setDesconectado(false);
    socket.onmessage = (event) => {
      const mensagem = JSON.parse(event.data) as { tipo?: string; avisar?: boolean };
      if (mensagem.tipo === "status_atualizado" && mensagem.avisar && "Notification" in window && Notification.permission === "granted") {
        new Notification("Atualização do pedido", { body: "Seu pedido teve o status atualizado." });
      }
      void carregar();
    };
    socket.onerror = () => setDesconectado(true);
    socket.onclose = () => {
      if (!ativoRef.current) return;
      setDesconectado(true);
      timerRef.current = window.setTimeout(conectar, 2000);
    };
  }, [carregar, pedidoId]);

  useEffect(() => {
    ativoRef.current = true;
    void carregar();
    conectar();
    const aoVoltarOnline = () => { void carregar(); conectar(); };
    window.addEventListener("online", aoVoltarOnline);
    return () => {
      ativoRef.current = false;
      window.removeEventListener("online", aoVoltarOnline);
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      socketRef.current?.close();
    };
  }, [carregar, conectar]);

  if (carregando) return <Tela titulo={`Pedido #${pedidoId}`}><Carregando /></Tela>;
  if (erro || !pedido) {
    return <Tela titulo="Pedido" aoVoltar={voltar}><Aviso tom="erro">{erro ?? "Pedido não encontrado."}</Aviso></Tela>;
  }

  const status = STATUS_PEDIDO[pedido.status];
  return (
    <Tela titulo={`Pedido #${pedido.id}`} subtitulo={pedido.unidade.nome} aoVoltar={voltar}>
      {desconectado ? <Aviso tom="aviso">Sem conexão em tempo real. Mostrando o último status recebido; tentando reconectar…</Aviso> : null}
      <div className="pedido-detalhe__status">
        <Selo tom={status.tom}>{status.nome}</Selo>
        <span className="texto-suave">Atualizado {dataHora(pedido.atualizado_em)}</span>
      </div>

      <Cartao>
        <h2 className="titulo-secao">Resumo do pedido</h2>
        <ul className="lista-resumo">
          {pedido.itens.map((item) => (
            <li key={item.id}><span>{item.quantidade}x {item.nome}</span><span>{reais(item.valor_final_centavos)}</span></li>
          ))}
        </ul>
        <ResumoValores linhas={[
          ...(pedido.tipo_atendimento === "ENTREGA" ? [{ rotulo: "Taxa de entrega", centavos: pedido.taxa_entrega_centavos }] : []),
          ...(pedido.desconto_cupom_centavos ? [{ rotulo: "Desconto do cupom", centavos: pedido.desconto_cupom_centavos, negativo: true }] : []),
          { rotulo: "Total", centavos: pedido.total_centavos, destaque: true },
        ]} />
        <p className="texto-suave">{NOME_ATENDIMENTO[pedido.tipo_atendimento]}</p>
        {pedido.entrega ? (
          <div className="pedido-detalhe__entrega">
            <strong>Entrega</strong>
            <span>{enderecoCurto(pedido.entrega.endereco)}</span>
            <span className="texto-suave">Tempo estimado: cerca de {pedido.entrega.tempo_estimado_min} min</span>
          </div>
        ) : null}
      </Cartao>

      <section className="pedido-detalhe__timeline" aria-label="Linha do tempo do pedido">
        <h2 className="titulo-secao">Linha do tempo</h2>
        {pedido.notificacoes.map((notificacao, indice) => (
          <div className={`pedido-detalhe__evento ${indice === pedido.notificacoes.length - 1 ? "pedido-detalhe__evento--atual" : ""}`} key={`${notificacao.criado_em}-${notificacao.status}`}>
            <div className="pedido-detalhe__ponto" />
            <div>
              <div className="linha-entre"><strong>{notificacao.titulo}</strong><span className="texto-fraco">{dataHora(notificacao.criado_em)}</span></div>
              <p className="texto-suave">{notificacao.mensagem}</p>
              <Selo tom={STATUS_PEDIDO[notificacao.status as Pedido["status"]]?.tom ?? "neutro"}>{STATUS_PEDIDO[notificacao.status as Pedido["status"]]?.nome ?? notificacao.status}</Selo>
            </div>
          </div>
        ))}
      </section>
    </Tela>
  );
}
