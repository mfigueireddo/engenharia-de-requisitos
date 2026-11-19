import { ButtonHTMLAttributes, ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  /** primario = vermelho cheio; contorno = borda vermelha; texto = só o texto. */
  variante?: "primario" | "contorno" | "texto";
  largo?: boolean;
  carregando?: boolean;
  children: ReactNode;
};

export function Botao({ variante = "primario", largo, carregando, disabled, className = "", children, ...resto }: Props) {
  return (
    <button
      type="button"
      className={`botao botao--${variante} ${largo ? "botao--largo" : ""} ${className}`}
      disabled={disabled || carregando}
      aria-busy={carregando || undefined}
      {...resto}
    >
      {carregando ? <span className="botao__giro" aria-hidden /> : null}
      <span>{children}</span>
    </button>
  );
}
