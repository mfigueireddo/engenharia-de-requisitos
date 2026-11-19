import { ir } from "../navegacao";
import { IconeCardapio, IconeFidelidade, IconeInicio, IconePedidos } from "./Icones";

export type Aba = "inicio" | "cardapio" | "pedidos" | "fidelidade";

const ABAS = [
  { id: "inicio", rotulo: "Início", Icone: IconeInicio },
  { id: "cardapio", rotulo: "Cardápio", Icone: IconeCardapio },
  { id: "pedidos", rotulo: "Pedidos", Icone: IconePedidos },
  { id: "fidelidade", rotulo: "Fidelidade", Icone: IconeFidelidade },
] as const;

/** Barra inferior com as quatro abas comuns a todas as telas (ERS 3.1). */
export function BarraNavegacao({ ativa }: { ativa: Aba }) {
  return (
    <nav className="barra-nav" aria-label="Navegação principal">
      {ABAS.map(({ id, rotulo, Icone }) => (
        <button key={id} type="button" aria-current={id === ativa ? "page" : undefined}
          className={`barra-nav__aba ${id === ativa ? "barra-nav__aba--ativa" : ""}`}
          onClick={() => ir({ tela: id })}>
          <span className="barra-nav__icone"><Icone tamanho={20} /></span>
          {rotulo}
        </button>
      ))}
    </nav>
  );
}
