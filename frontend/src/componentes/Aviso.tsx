import { ReactNode } from "react";
import { IconeAlerta, IconeCheck, IconeInfo, IconeX } from "./Icones";

const ICONES = { sucesso: IconeCheck, erro: IconeX, aviso: IconeAlerta, info: IconeInfo };

/** Faixa de retorno contextual (ex.: "Fora da zona de entrega desta unidade", telas 03 e 07). */
export function Aviso({ tom, children, acao }: { tom: keyof typeof ICONES; children: ReactNode; acao?: ReactNode }) {
  const Icone = ICONES[tom];
  return (
    <div className={`aviso aviso--${tom}`} role={tom === "erro" ? "alert" : "status"}>
      <span className="aviso__icone"><Icone tamanho={16} /></span>
      <div className="aviso__texto">{children}</div>
      {acao ? <div className="aviso__acao">{acao}</div> : null}
    </div>
  );
}
