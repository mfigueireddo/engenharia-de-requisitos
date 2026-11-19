// Ícones em SVG (traço herda a cor do texto: currentColor).
type P = { tamanho?: number };
const base = (t = 24) => ({
  width: t, height: t, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
  strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true,
});

export const IconeVoltar = ({ tamanho }: P) => <svg {...base(tamanho)}><path d="M15 18l-6-6 6-6" /></svg>;
export const IconeInicio = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M3 10.5L12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" /></svg>
);
export const IconeCardapio = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M4 11h16M5 11a7 7 0 0 1 14 0M4 15h16M5 15v1a3 3 0 0 0 3 3h8a3 3 0 0 0 3-3v-1" /></svg>
);
export const IconePedidos = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6" /></svg>
);
export const IconeFidelidade = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg>
);
export const IconeSacola = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M5 8h14l-1 13H6zM9 8V6a3 3 0 0 1 6 0v2" /></svg>
);
export const IconeLixeira = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></svg>
);
export const IconeCheck = ({ tamanho }: P) => <svg {...base(tamanho)}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>;
export const IconeX = ({ tamanho }: P) => <svg {...base(tamanho)}><path d="M6 6l12 12M18 6L6 18" /></svg>;
export const IconeAlerta = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M12 4l9 16H3zM12 10v4M12 17.5v.01" /></svg>
);
export const IconeInfo = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.5v.01" /></svg>
);
export const IconeBusca = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></svg>
);
export const IconeLoja = ({ tamanho }: P) => (
  <svg {...base(tamanho)}><path d="M4 9l1.5-5h13L20 9M4 9v11h16V9M4 9h16M10 20v-5h4v5" /></svg>
);
