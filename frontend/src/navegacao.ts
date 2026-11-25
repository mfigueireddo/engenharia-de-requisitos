// Navegação simples pelo "#" da URL (sem dependência extra): #/cardapio, #/item/12 ...
// Recarregar a página mantém a tela, e o botão "voltar" do navegador funciona.
import { useEffect, useState } from "react";

export type Rota =
  | { tela: "inicio" }
  | { tela: "entrar"; depois?: string }
  | { tela: "cadastro" }
  | { tela: "cardapio" }
  | { tela: "item"; produtoId: number }
  | { tela: "sacola" }
  | { tela: "cupons" }
  | { tela: "checkout" }
  | { tela: "pedido-recebido"; pedidoId: number }
  | { tela: "pedido"; pedidoId: number }
  | { tela: "pedidos" }
  | { tela: "fidelidade" };

export function lerRota(hash: string = window.location.hash): Rota {
  const [caminho, busca = ""] = hash.replace(/^#/, "").split("?");
  const partes = caminho.split("/").filter(Boolean);
  const params = new URLSearchParams(busca);
  switch (partes[0]) {
    case "entrar":
      return { tela: "entrar", depois: params.get("depois") ?? undefined };
    case "cadastro":
      return { tela: "cadastro" };
    case "cardapio":
      return { tela: "cardapio" };
    case "item":
      return Number(partes[1]) ? { tela: "item", produtoId: Number(partes[1]) } : { tela: "cardapio" };
    case "sacola":
      return { tela: "sacola" };
    case "cupons":
      return { tela: "cupons" };
    case "checkout":
      return { tela: "checkout" };
    case "pedido-recebido":
      return { tela: "pedido-recebido", pedidoId: Number(partes[1]) };
    case "pedido":
      return Number(partes[1]) ? { tela: "pedido", pedidoId: Number(partes[1]) } : { tela: "pedidos" };
    case "pedidos":
      return { tela: "pedidos" };
    case "fidelidade":
      return { tela: "fidelidade" };
    default:
      return { tela: "inicio" };
  }
}

export function caminhoDe(rota: Rota): string {
  switch (rota.tela) {
    case "inicio":
      return "#/";
    case "entrar":
      return rota.depois ? `#/entrar?depois=${encodeURIComponent(rota.depois)}` : "#/entrar";
    case "item":
      return `#/item/${rota.produtoId}`;
    case "pedido-recebido":
      return `#/pedido-recebido/${rota.pedidoId}`;
    case "pedido":
      return `#/pedido/${rota.pedidoId}`;
    default:
      return `#/${rota.tela}`;
  }
}

export function ir(rota: Rota, opcoes: { substituir?: boolean } = {}) {
  const destino = caminhoDe(rota);
  if (opcoes.substituir) window.location.replace(destino);
  else window.location.hash = destino;
}

/** Volta à tela anterior; se não houver histórico, vai para `alternativa`. */
export function voltar(alternativa: Rota = { tela: "inicio" }) {
  if (window.history.length > 1) window.history.back();
  else ir(alternativa, { substituir: true });
}

export function useRota(): Rota {
  const [rota, setRota] = useState<Rota>(() => lerRota());
  useEffect(() => {
    const atualizar = () => {
      setRota(lerRota());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", atualizar);
    return () => window.removeEventListener("hashchange", atualizar);
  }, []);
  return rota;
}
