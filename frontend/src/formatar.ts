// Formatação para a interface em português do Brasil (ERS 2.4).

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

/** 2490 → "R$ 24,90". Os valores chegam da API em centavos inteiros (RNF-23). */
export function reais(centavos: number): string {
  return moeda.format(centavos / 100).replace(/ /g, " ");
}

/** "2026-11-19T14:05:00+00:00" → "19/11 às 11:05" (hora local). */
export function dataHora(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const data = d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  const hora = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${data} às ${hora}`;
}

/** 1234 → "1,2 km"; 800 → "800 m". */
export function distancia(metros: number): string {
  if (metros < 1000) return `${metros} m`;
  return `${(metros / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} km`;
}

export function enderecoCurto(e: { rua: string; numero: string; complemento?: string | null }): string {
  return `${e.rua}, ${e.numero}${e.complemento ? ` – ${e.complemento}` : ""}`;
}

export const NOME_ATENDIMENTO = {
  ENTREGA: "Entrega",
  RETIRADA: "Retirada no balcão",
  DRIVE_THRU: "Drive-thru",
} as const;
