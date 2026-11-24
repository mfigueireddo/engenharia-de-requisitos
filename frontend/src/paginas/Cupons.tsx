// Tela 07 – Aplicar cupom: UC30 (Aplicar Cupom ao Pedido).
// - Passo 1: o cliente digita o código do cupom ou escolhe "Usar" em um dos cupons disponíveis.
// - Passos 2–5: o servidor valida (validade, limite de usos, subtotal mínimo) e devolve o desconto.
// - A1: trocar ou remover o cupom desfaz o desconto anterior.
// - E1 / E2: cupom não encontrado ou inválido mostra a mensagem de erro junto ao campo (ERS 3.1).
import { FormEvent, useEffect, useState } from "react";
import { api, CupomAplicado, CupomDisponivel, ErroApi } from "../api";
import { Aviso, Botao, Carregando, Cartao, Tela } from "../componentes";
import { dataCurta, reais } from "../formatar";
import { voltar } from "../navegacao";

const CHAVE_CUPOM = "burguerja.cupom";

export function lerCupomSelecionado(): string | null {
  try {
    return sessionStorage.getItem(CHAVE_CUPOM);
  } catch {
    return null;
  }
}

export function salvarCupomSelecionado(codigo: string | null) {
  try {
    if (codigo) sessionStorage.setItem(CHAVE_CUPOM, codigo.trim().toUpperCase());
    else sessionStorage.removeItem(CHAVE_CUPOM);
  } catch {
    /* navegador sem sessionStorage */
  }
}

function seloDoCupom(c: CupomDisponivel): string {
  if (c.percentual_desconto_centesimos > 0) {
    const pct = c.percentual_desconto_centesimos / 100;
    return `${pct.toLocaleString("pt-BR")}%`;
  }
  return "FRETE";
}

function resumoDoCupom(c: CupomDisponivel): string {
  const partes: string[] = [];
  if (c.descricao) partes.push(c.descricao);
  if (c.validade_fim) partes.push(`válido até ${dataCurta(c.validade_fim)}`);
  return partes.join(" • ");
}

function mensagemCupomAplicado(c: CupomAplicado): string {
  if (c.desconto_cupom_centavos > 0 && c.isenta_taxa_entrega) {
    return `Cupom aplicado! – ${reais(c.desconto_cupom_centavos)} e entrega grátis no seu pedido`;
  }
  if (c.desconto_cupom_centavos > 0) {
    return `Cupom aplicado! – ${reais(c.desconto_cupom_centavos)} no seu pedido`;
  }
  if (c.isenta_taxa_entrega) {
    return "Cupom aplicado! Entrega grátis no seu pedido";
  }
  return `Cupom ${c.codigo} aplicado!`;
}

export default function Cupons() {
  const [codigo, setCodigo] = useState<string>(() => lerCupomSelecionado() ?? "");
  const [cupons, setCupons] = useState<CupomDisponivel[] | null>(null);
  const [aplicado, setAplicado] = useState<CupomAplicado | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aplicando, setAplicando] = useState(false);

  useEffect(() => {
    api.cupons().then(setCupons).catch(() => setCupons([]));
    const salvo = lerCupomSelecionado();
    if (salvo) {
      validar(salvo, true);
    }
  }, []);

  async function validar(cod: string, silencioso = false) {
    const limpo = cod.trim().toUpperCase();
    if (!limpo) return;
    setCodigo(limpo);
    setAplicando(true);
    setErro(null);
    try {
      const res = await api.aplicarCupom(limpo);
      setAplicado(res);
      salvarCupomSelecionado(res.codigo);
    } catch (e) {
      setAplicado(null);
      salvarCupomSelecionado(null);
      if (!silencioso) {
        setErro(e instanceof ErroApi ? e.message : "Não foi possível aplicar o cupom.");
      }
    } finally {
      setAplicando(false);
    }
  }

  function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    validar(codigo);
  }

  function remover() {
    setAplicado(null);
    setErro(null);
    setCodigo("");
    salvarCupomSelecionado(null);
  }

  const disponiveis = cupons?.filter((c) => c.disponivel) ?? [];

  return (
    <Tela
      titulo="Cupons"
      aoVoltar={() => voltar({ tela: "checkout" })}
      rodape={
        <Botao largo onClick={() => voltar({ tela: "checkout" })}>
          {aplicado ? `Continuar com ${aplicado.codigo}` : "Voltar ao pedido"}
        </Botao>
      }
    >
      {/* Passo 1: digitar código do cupom */}
      <form className="pilha" onSubmit={aoSubmeter}>
        <div className="campo">
          <label htmlFor="campo-cupom" className="campo__rotulo">Código do cupom</label>
          <div className="cupom-entrada">
            <input
              id="campo-cupom"
              className={`campo__entrada ${erro ? "campo__entrada--erro" : ""}`}
              value={codigo}
              placeholder="Ex.: BEMVINDO10"
              onChange={(e) => setCodigo(e.target.value.toUpperCase())}
            />
            <Botao type="submit" carregando={aplicando} disabled={!codigo.trim()}>
              Aplicar
            </Botao>
          </div>
        </div>

        {/* Passo 5: confirmação visual ou mensagem de erro (E1/E2) */}
        {aplicado ? (
          <Aviso
            tom="sucesso"
            acao={
              <Botao variante="texto" onClick={remover}>
                Remover
              </Botao>
            }
          >
            {mensagemCupomAplicado(aplicado)}
          </Aviso>
        ) : null}

        {erro ? <Aviso tom="erro">{erro}</Aviso> : null}
      </form>

      {/* Lista de cupons disponíveis do cliente (wireframe 07) */}
      <section className="pilha">
        <h2 className="titulo-secao">Cupons disponíveis</h2>
        {cupons === null ? <Carregando texto="Buscando seus cupons…" /> : null}
        {cupons !== null && disponiveis.length === 0 ? (
          <p className="texto-suave">Você não tem cupons disponíveis no momento.</p>
        ) : null}
        {disponiveis.map((c) => {
          const ativo = aplicado?.codigo === c.codigo;
          return (
            <Cartao key={c.id} className={`cartao-cupom ${ativo ? "cartao--selecionado" : ""}`}>
              <div className="cartao-cupom__selo">{seloDoCupom(c)}</div>
              <div className="cartao-cupom__meio">
                <strong className="cartao-cupom__codigo">{c.codigo}</strong>
                <span className="cartao-cupom__descricao">{resumoDoCupom(c)}</span>
              </div>
              {ativo ? (
                <Botao variante="texto" onClick={remover}>
                  Remover
                </Botao>
              ) : (
                <Botao variante="texto" disabled={aplicando} onClick={() => validar(c.codigo)}>
                  Usar
                </Botao>
              )}
            </Cartao>
          );
        })}
      </section>
    </Tela>
  );
}
