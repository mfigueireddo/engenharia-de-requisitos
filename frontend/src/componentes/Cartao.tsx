import { HTMLAttributes, ReactNode } from "react";

type Props = HTMLAttributes<HTMLDivElement> & { children: ReactNode; aoClicar?: () => void; selecionado?: boolean };

/** Caixa branca com borda arredondada, usada em listas e resumos. Clicável se tiver `aoClicar`. */
export function Cartao({ children, aoClicar, selecionado, className = "", ...resto }: Props) {
  const classes = `cartao ${aoClicar ? "cartao--clicavel" : ""} ${selecionado ? "cartao--selecionado" : ""} ${className}`;
  if (aoClicar) {
    return (
      <div role="button" tabIndex={0} className={classes} onClick={aoClicar}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), aoClicar())} {...resto}>
        {children}
      </div>
    );
  }
  return <div className={classes} {...resto}>{children}</div>;
}
