// Abas "Pedidos" (tela 13, UC31) e "Fidelidade" (tela 14) ainda sem back-end:
// aparecem na barra (ERS 3.1) com aviso de "em breve" (decisão do humano nesta sessão).
import { Aba, EstadoVazio, IconeFidelidade, IconePedidos, Tela } from "../componentes";

const TEXTOS = {
  pedidos: { titulo: "Meus pedidos", Icone: IconePedidos, texto: "Em breve você vai acompanhar seus pedidos e ver o histórico aqui." },
  fidelidade: { titulo: "Fidelidade", Icone: IconeFidelidade, texto: "Em breve você vai ver seu saldo de pontos e os lotes que vão expirar aqui." },
} as const;

export default function EmBreve({ aba }: { aba: Extract<Aba, "pedidos" | "fidelidade"> }) {
  const { titulo, Icone, texto } = TEXTOS[aba];
  return (
    <Tela titulo={titulo} semVoltar aba={aba}>
      <EstadoVazio icone={<Icone tamanho={40} />} titulo="Em breve" texto={texto} />
    </Tela>
  );
}
