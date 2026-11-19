import { ReactNode } from "react";

/** Mensagem centralizada para listas vazias, "em breve" etc. */
export function EstadoVazio({ icone, titulo, texto, acao }: { icone?: ReactNode; titulo: string; texto?: ReactNode; acao?: ReactNode }) {
  return (
    <div className="vazio">
      {icone ? <div className="vazio__icone">{icone}</div> : null}
      <h2 className="vazio__titulo">{titulo}</h2>
      {texto ? <p className="vazio__texto">{texto}</p> : null}
      {acao ? <div className="vazio__acao">{acao}</div> : null}
    </div>
  );
}
