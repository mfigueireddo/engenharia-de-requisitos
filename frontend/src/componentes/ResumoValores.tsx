import { reais } from "../formatar";

export type LinhaValor = { rotulo: string; centavos: number; negativo?: boolean; destaque?: boolean };

/** Quadro "Subtotal / Taxa de entrega / Desconto / Total" (telas 06 e 08). */
export function ResumoValores({ linhas }: { linhas: LinhaValor[] }) {
  return (
    <dl className="resumo">
      {linhas.map((l) => (
        <div key={l.rotulo} className={`resumo__linha ${l.destaque ? "resumo__linha--total" : ""}`}>
          <dt>{l.rotulo}</dt>
          <dd>{l.negativo && l.centavos > 0 ? `– ${reais(l.centavos)}` : reais(l.centavos)}</dd>
        </div>
      ))}
    </dl>
  );
}
