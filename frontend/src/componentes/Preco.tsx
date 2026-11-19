import { reais } from "../formatar";

/** Preço final em destaque e, se houver desconto, o preço cheio riscado (telas 04 e 05). */
export function Preco({ final, cheio, tamanho = "md" }: { final: number; cheio?: number; tamanho?: "md" | "lg" }) {
  return (
    <span className={`preco preco--${tamanho}`}>
      <strong className="preco__final">{reais(final)}</strong>
      {cheio !== undefined && cheio > final ? <s className="preco__cheio">{reais(cheio)}</s> : null}
    </span>
  );
}
