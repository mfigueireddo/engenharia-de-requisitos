import { ReactNode } from "react";

/** Etiqueta em pílula: "Aberta", "Promoção", "Tempo estimado: 30–40 min"... */
export function Selo({ tom = "neutro", children }: { tom?: "sucesso" | "erro" | "aviso" | "neutro"; children: ReactNode }) {
  return <span className={`selo selo--${tom}`}>{children}</span>;
}
