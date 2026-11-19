// Carrega dados da API com estados de carregando/erro, reutilizado pelas telas.
import { DependencyList, useCallback, useEffect, useState } from "react";

export function useCarregar<T>(buscar: () => Promise<T>, deps: DependencyList) {
  const [dados, setDados] = useState<T | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const recarregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      setDados(await buscar());
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setCarregando(false);
    }
  }, deps);

  useEffect(() => {
    recarregar();
  }, [recarregar]);

  return { dados, setDados, erro, carregando, recarregar };
}
