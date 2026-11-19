import { ReactNode } from "react";
import { BarraNavegacao, Aba } from "./BarraNavegacao";
import { IconeVoltar } from "./Icones";
import { voltar } from "../navegacao";

type Props = {
  /** Título com seta de voltar (telas 03, 05–12). */
  titulo?: string;
  aoVoltar?: () => void;
  /** Telas das abas (04, 13, 14): título grande, sem seta de voltar. */
  semVoltar?: boolean;
  subtitulo?: ReactNode;
  /** Cabeçalho livre (ex.: faixa vermelha da tela 02). Substitui o título. */
  cabecalho?: ReactNode;
  /** Aba ativa: mostra a barra inferior com as 4 abas (ERS 3.1). */
  aba?: Aba;
  /** Rodapé fixo, acima da barra (ex.: botão "Finalizar pedido"). */
  rodape?: ReactNode;
  fundo?: "branco" | "cinza";
  children: ReactNode;
};

/** Moldura de toda tela do app: cabeçalho, conteúdo rolável, rodapé e abas. */
export function Tela({ titulo, aoVoltar, semVoltar, subtitulo, cabecalho, aba, rodape, fundo = "branco", children }: Props) {
  return (
    <div className={`tela tela--${fundo} ${aba ? "tela--com-abas" : ""} ${rodape ? "tela--com-rodape" : ""}`}>
      {cabecalho ??
        (titulo ? (
          <header className={`tela__cabecalho ${semVoltar ? "tela__cabecalho--aba" : ""}`}>
            {semVoltar ? null : (
              <button type="button" className="tela__voltar" aria-label="Voltar" onClick={aoVoltar ?? (() => voltar())}>
                <IconeVoltar />
              </button>
            )}
            <div>
              <h1 className="tela__titulo">{titulo}</h1>
              {subtitulo ? <p className="tela__subtitulo">{subtitulo}</p> : null}
            </div>
          </header>
        ) : null)}
      <main className="tela__conteudo">{children}</main>
      {rodape ? <div className="tela__rodape">{rodape}</div> : null}
      {aba ? <BarraNavegacao ativa={aba} /> : null}
    </div>
  );
}
