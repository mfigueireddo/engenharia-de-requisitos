import { InputHTMLAttributes, TextareaHTMLAttributes, useId } from "react";

type Comum = { rotulo: string; erro?: string | null; dica?: string };

/** Campo de texto com rótulo e erro logo abaixo (ERS 3.1: erro junto ao campo). */
export function Campo({ rotulo, erro, dica, ...resto }: Comum & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <div className="campo">
      <label htmlFor={id} className="campo__rotulo">{rotulo}</label>
      <input id={id} className={`campo__entrada ${erro ? "campo__entrada--erro" : ""}`}
        aria-invalid={!!erro} aria-describedby={erro ? `${id}-erro` : undefined} {...resto} />
      {erro ? <p id={`${id}-erro`} className="campo__erro">{erro}</p> : dica ? <p className="campo__dica">{dica}</p> : null}
    </div>
  );
}

export function CampoTexto({ rotulo, erro, dica, ...resto }: Comum & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const id = useId();
  return (
    <div className="campo">
      <label htmlFor={id} className="campo__rotulo">{rotulo}</label>
      <textarea id={id} className={`campo__entrada campo__entrada--area ${erro ? "campo__entrada--erro" : ""}`}
        aria-invalid={!!erro} {...resto} />
      {erro ? <p className="campo__erro">{erro}</p> : dica ? <p className="campo__dica">{dica}</p> : null}
    </div>
  );
}
