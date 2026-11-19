import { useCarrinho } from "../contextos/Carrinho";
import { reais } from "../formatar";
import { ir } from "../navegacao";
import { IconeSacola } from "./Icones";

/** Atalho flutuante para a sacola, mostrado quando há itens (Início e Cardápio). */
export function BarraSacola() {
  const { carrinho, totalItens } = useCarrinho();
  if (!carrinho || totalItens === 0) return null;
  return (
    <button type="button" className="barra-sacola" onClick={() => ir({ tela: "sacola" })}>
      <span className="barra-sacola__qtd"><IconeSacola tamanho={18} /> {totalItens}</span>
      <span>Ver sacola</span>
      <strong>{reais(carrinho.subtotal_centavos)}</strong>
    </button>
  );
}
