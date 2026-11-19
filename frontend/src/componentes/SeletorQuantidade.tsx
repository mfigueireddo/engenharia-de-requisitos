import { IconeLixeira } from "./Icones";

type Props = {
  valor: number;
  aoMudar: (novo: number) => void;
  /** Valor mínimo: 1 no detalhe do item; 0 na sacola, onde zerar remove (RF-12). */
  minimo?: number;
  maximo?: number;
  tamanho?: "md" | "sm";
  desabilitado?: boolean;
};

/** Botões − e + com o número no meio (telas 05 e 06). */
export function SeletorQuantidade({ valor, aoMudar, minimo = 1, maximo = 99, tamanho = "md", desabilitado }: Props) {
  const vaiRemover = minimo === 0 && valor === 1;
  return (
    <div className={`seletor seletor--${tamanho}`}>
      <button type="button" className="seletor__botao" disabled={desabilitado || valor <= minimo}
        aria-label={vaiRemover ? "Remover item" : "Diminuir quantidade"} onClick={() => aoMudar(valor - 1)}>
        {vaiRemover ? <IconeLixeira tamanho={14} /> : "−"}
      </button>
      <span className="seletor__valor" aria-live="polite">{valor}</span>
      <button type="button" className="seletor__botao" disabled={desabilitado || valor >= maximo}
        aria-label="Aumentar quantidade" onClick={() => aoMudar(valor + 1)}>
        +
      </button>
    </div>
  );
}
