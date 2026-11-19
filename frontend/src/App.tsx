// Escolhe a tela pela rota (#/...). Telas que precisam de login (RN-01) mandam
// o visitante para "Entrar" e voltam para onde ele estava.
import { useEffect } from "react";
import { Carregando } from "./componentes";
import { ProvedorCarrinho } from "./contextos/Carrinho";
import { ProvedorSessao, useSessao } from "./contextos/Sessao";
import { caminhoDe, ir, Rota, useRota } from "./navegacao";
import Cadastro from "./paginas/Cadastro";
import Cardapio from "./paginas/Cardapio";
import Checkout from "./paginas/Checkout";
import DetalheItem from "./paginas/DetalheItem";
import EmBreve from "./paginas/EmBreve";
import Entrar from "./paginas/Entrar";
import Inicio from "./paginas/Inicio";
import PedidoRecebido from "./paginas/PedidoRecebido";
import Sacola from "./paginas/Sacola";

const EXIGEM_LOGIN: Rota["tela"][] = ["sacola", "checkout", "pedido-recebido"];

function Telas() {
  const rota = useRota();
  const { cliente, carregando } = useSessao();
  const bloqueada = EXIGEM_LOGIN.includes(rota.tela) && !cliente;

  useEffect(() => {
    if (!carregando && bloqueada) ir({ tela: "entrar", depois: caminhoDe(rota).slice(1) }, { substituir: true });
  }, [carregando, bloqueada, rota]);

  if (carregando || bloqueada) return <div className="tela"><Carregando /></div>;

  switch (rota.tela) {
    case "entrar":
      return <Entrar depois={rota.depois} />;
    case "cadastro":
      return <Cadastro />;
    case "cardapio":
      return <Cardapio />;
    case "item":
      return <DetalheItem key={rota.produtoId} produtoId={rota.produtoId} />;
    case "sacola":
      return <Sacola />;
    case "checkout":
      return <Checkout />;
    case "pedido-recebido":
      return <PedidoRecebido pedidoId={rota.pedidoId} />;
    case "pedidos":
    case "fidelidade":
      return <EmBreve aba={rota.tela} />;
    default:
      return <Inicio />;
  }
}

export default function App() {
  return (
    <ProvedorSessao>
      <ProvedorCarrinho>
        <div className="app">
          <Telas />
        </div>
      </ProvedorCarrinho>
    </ProvedorSessao>
  );
}
