// Cliente logado e unidade escolhida, disponíveis para todas as telas.
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, Cliente, definirAoExpirarSessao, lerToken, salvarToken } from "../api";

const CHAVE_UNIDADE = "burguerja.unidade";

type ValorSessao = {
  cliente: Cliente | null;
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
  /** Unidade cujo cardápio o cliente está vendo (Início → Cardápio). */
  unidadeId: number | null;
  escolherUnidade: (id: number | null) => void;
};

const ContextoSessao = createContext<ValorSessao | null>(null);

function lerUnidade(): number | null {
  try {
    const v = Number(localStorage.getItem(CHAVE_UNIDADE));
    return v || null;
  } catch {
    return null;
  }
}

export function ProvedorSessao({ children }: { children: ReactNode }) {
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [unidadeId, setUnidadeId] = useState<number | null>(lerUnidade);

  useEffect(() => {
    definirAoExpirarSessao(() => {
      salvarToken(null);
      setCliente(null);
    });
    if (!lerToken()) {
      setCarregando(false);
      return;
    }
    api
      .eu()
      .then(setCliente)
      .catch(() => salvarToken(null))
      .finally(() => setCarregando(false));
  }, []);

  const entrar = useCallback(async (email: string, senha: string) => {
    const sessao = await api.entrar(email, senha);
    salvarToken(sessao.token);
    setCliente(sessao.cliente);
  }, []);

  const sair = useCallback(async () => {
    try {
      await api.sair();
    } catch {
      /* mesmo se a API falhar, o token sai deste navegador */
    }
    salvarToken(null);
    setCliente(null);
  }, []);

  const escolherUnidade = useCallback((id: number | null) => {
    setUnidadeId(id);
    try {
      if (id) localStorage.setItem(CHAVE_UNIDADE, String(id));
      else localStorage.removeItem(CHAVE_UNIDADE);
    } catch {
      /* sem armazenamento: vale só nesta aba */
    }
  }, []);

  const valor = useMemo(
    () => ({ cliente, carregando, entrar, sair, unidadeId, escolherUnidade }),
    [cliente, carregando, entrar, sair, unidadeId, escolherUnidade],
  );
  return <ContextoSessao.Provider value={valor}>{children}</ContextoSessao.Provider>;
}

export function useSessao(): ValorSessao {
  const v = useContext(ContextoSessao);
  if (!v) throw new Error("useSessao fora do ProvedorSessao");
  return v;
}
