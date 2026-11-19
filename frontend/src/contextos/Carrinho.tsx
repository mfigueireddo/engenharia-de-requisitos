// Carrinho do cliente logado (UC29). Toda alteração devolve o carrinho já
// recalculado pelo servidor (RF-13, RNF-14); aqui só guardamos essa resposta.
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, Carrinho } from "../api";
import { useSessao } from "./Sessao";

type ValorCarrinho = {
  carrinho: Carrinho | null;
  /** Quantidade total de unidades na sacola (para o selo da barra). */
  totalItens: number;
  recarregar: () => Promise<Carrinho | null>;
  /** Guarda um carrinho devolvido por qualquer rota de /api/carrinho. */
  atualizar: (c: Carrinho) => void;
};

const ContextoCarrinho = createContext<ValorCarrinho | null>(null);

export function ProvedorCarrinho({ children }: { children: ReactNode }) {
  const { cliente } = useSessao();
  const [carrinho, setCarrinho] = useState<Carrinho | null>(null);

  const recarregar = useCallback(async () => {
    if (!cliente) {
      setCarrinho(null);
      return null;
    }
    const c = await api.carrinho();
    setCarrinho(c);
    return c;
  }, [cliente]);

  useEffect(() => {
    recarregar().catch(() => setCarrinho(null));
  }, [recarregar]);

  const valor = useMemo(
    () => ({
      carrinho,
      totalItens: carrinho?.itens.reduce((s, i) => s + i.quantidade, 0) ?? 0,
      recarregar,
      atualizar: setCarrinho,
    }),
    [carrinho, recarregar],
  );
  return <ContextoCarrinho.Provider value={valor}>{children}</ContextoCarrinho.Provider>;
}

export function useCarrinho(): ValorCarrinho {
  const v = useContext(ContextoCarrinho);
  if (!v) throw new Error("useCarrinho fora do ProvedorCarrinho");
  return v;
}
