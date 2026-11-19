import { ReactNode } from "react";

type Props = {
  nome: string;
  selecionada: boolean;
  aoSelecionar: () => void;
  titulo: ReactNode;
  descricao?: ReactNode;
  lateral?: ReactNode;
  desabilitada?: boolean;
};

/** Opção de rádio em formato de cartão (tela 08: "Pix / Cartão de crédito"). */
export function OpcaoSelecao({ nome, selecionada, aoSelecionar, titulo, descricao, lateral, desabilitada }: Props) {
  return (
    <label className={`opcao ${selecionada ? "opcao--selecionada" : ""} ${desabilitada ? "opcao--desabilitada" : ""}`}>
      <input type="radio" name={nome} checked={selecionada} disabled={desabilitada}
        onChange={aoSelecionar} className="opcao__radio" />
      <span className="opcao__marca" aria-hidden />
      <span className="opcao__texto">
        <span className="opcao__titulo">{titulo}</span>
        {descricao ? <span className="opcao__descricao">{descricao}</span> : null}
      </span>
      {lateral ? <span className="opcao__lateral">{lateral}</span> : null}
    </label>
  );
}
