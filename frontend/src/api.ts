// Cliente da API REST do back-end. Toda comunicação com dados passa por aqui.

// ESBOÇO-PROVISÓRIO: Recado e as funções de recados saem na 1ª funcionalidade real (AGENTS.md, seção 7).
export type Recado = { id: number; texto: string; criado_em: string };

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`/api${caminho}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) throw new Error(`Erro ${resp.status} em ${caminho}`);
  return resp.json() as Promise<T>;
}

export const api = {
  health: () => requisitar<{ status: string }>("/health"),
  listarRecados: () => requisitar<Recado[]>("/recados"),
  criarRecado: (texto: string) =>
    requisitar<Recado>("/recados", { method: "POST", body: JSON.stringify({ texto }) }),
};
