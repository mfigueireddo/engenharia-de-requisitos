import { ReactNode, useEffect } from "react";

type Props = { aberta: boolean; aoFechar: () => void; titulo: string; children: ReactNode };

/** Janela de confirmação que sobe de baixo, com fundo escurecido (tela 12).
 *  ERS 3.1: ações que não podem ser desfeitas pedem confirmação. */
export function Folha({ aberta, aoFechar, titulo, children }: Props) {
  useEffect(() => {
    if (!aberta) return;
    const esc = (e: KeyboardEvent) => e.key === "Escape" && aoFechar();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [aberta, aoFechar]);
  if (!aberta) return null;
  return (
    <div className="folha__fundo" onClick={aoFechar}>
      <div className="folha" role="dialog" aria-modal="true" aria-label={titulo} onClick={(e) => e.stopPropagation()}>
        <span className="folha__alca" aria-hidden />
        <h2 className="folha__titulo">{titulo}</h2>
        {children}
      </div>
    </div>
  );
}
