// Cliente da API REST do back-end. Toda comunicação com dados passa por aqui
// (ESTRUTURA.md, regra 4). Valores em centavos inteiros, como na API (RNF-23).

const CHAVE_TOKEN = "burguerja.token";

export function lerToken(): string | null {
  try {
    return localStorage.getItem(CHAVE_TOKEN);
  } catch {
    return null;
  }
}

export function salvarToken(token: string | null) {
  try {
    if (token) localStorage.setItem(CHAVE_TOKEN, token);
    else localStorage.removeItem(CHAVE_TOKEN);
  } catch {
    /* navegador sem armazenamento: a sessão dura só esta aba */
  }
}

/** Erro devolvido pela API, com a mensagem pronta para mostrar ao cliente. */
export class ErroApi extends Error {
  constructor(
    public status: number,
    mensagem: string,
    public motivo?: string,
  ) {
    super(mensagem);
  }
}

function mensagemDoErro(status: number, corpo: unknown): { mensagem: string; motivo?: string } {
  const detail = (corpo as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return { mensagem: detail };
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const d = detail as { mensagem?: string; motivo?: string };
    if (d.mensagem) return { mensagem: d.mensagem, motivo: d.motivo };
  }
  if (Array.isArray(detail)) return { mensagem: "Confira os dados informados." };
  if (status >= 500) return { mensagem: "O serviço está indisponível agora. Tente de novo em instantes." };
  return { mensagem: `Algo deu errado (erro ${status}).` };
}

/** Chamado quando a API responde 401 (sessão expirada): o app volta ao login. */
let aoExpirarSessao: () => void = () => {};
export function definirAoExpirarSessao(fn: () => void) {
  aoExpirarSessao = fn;
}

async function requisitar<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const token = lerToken();
  let resp: Response;
  try {
    resp = await fetch(`/api${caminho}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ErroApi(0, "Sem conexão com o servidor. Verifique sua internet.");
  }
  if (resp.status === 204) return undefined as T;
  const corpo = await resp.json().catch(() => null);
  if (!resp.ok) {
    if (resp.status === 401 && token) aoExpirarSessao();
    const { mensagem, motivo } = mensagemDoErro(resp.status, corpo);
    throw new ErroApi(resp.status, mensagem, motivo);
  }
  return corpo as T;
}

const json = (metodo: string, corpo?: unknown): RequestInit => ({
  method: metodo,
  body: corpo === undefined ? undefined : JSON.stringify(corpo),
});

// ---------------------------------------------------------------------------
// Tipos (espelham as respostas do back-end)
// ---------------------------------------------------------------------------

export type Cliente = { id: number; nome: string; email: string };
export type Sessao = { token: string; expira_em: string; cliente: Cliente };

export type Unidade = {
  id: number;
  nome: string;
  rua: string;
  numero: string;
  bairro: string;
  cidade: string;
  estado: string;
  cep: string;
  tem_drive_thru: boolean;
};

export type Componente = {
  produto_id: number;
  nome: string;
  quantidade: number;
  preco_unitario_centavos: number;
  desconto_unitario_centavos: number;
};

export type Produto = {
  id: number;
  nome: string;
  descricao: string;
  categoria: string;
  tipo: "SIMPLES" | "COMBO";
  preco_centavos: number;
  desconto_centavos: number;
  preco_final_centavos: number;
  componentes: Componente[];
};

export type Cardapio = {
  unidade: Unidade;
  produtos: Produto[];
  cardapio_atualizado_em: string | null;
  sgl_indisponivel: boolean;
};

export type ItemCarrinho = {
  id: number;
  produto_id: number;
  nome: string;
  tipo: "SIMPLES" | "COMBO";
  quantidade: number;
  observacao: string | null;
  preco_unitario_centavos: number;
  desconto_unitario_centavos: number;
  valor_final_centavos: number;
  componentes: Componente[];
};

export type Carrinho = {
  unidade: { id: number; nome: string } | null;
  itens: ItemCarrinho[];
  subtotal_centavos: number;
  avisos: string[];
  cardapio_atualizado_em: string | null;
  sgl_indisponivel: boolean;
};

export type Endereco = {
  id: number;
  rua: string;
  numero: string;
  complemento: string | null;
  bairro: string;
  cidade: string;
  estado: string;
  cep: string;
};

export type TipoAtendimento = "ENTREGA" | "RETIRADA" | "DRIVE_THRU";

export type Previa = {
  carrinho: Carrinho;
  tipos_atendimento_disponiveis: TipoAtendimento[];
  tipo_atendimento: TipoAtendimento;
  entrega: { endereco: Endereco; distancia_m: number; tempo_estimado_min: number } | null;
  subtotal_centavos: number;
  desconto_cupom_centavos: number;
  taxa_entrega_centavos: number;
  total_centavos: number;
};

export type Pedido = {
  id: number;
  status: string;
  unidade_id: number;
  tipo_atendimento: TipoAtendimento;
  entrega: { endereco: Omit<Endereco, "id">; distancia_m: number; tempo_estimado_min: number } | null;
  itens: { id: number; nome: string; quantidade: number; observacao: string | null; valor_final_centavos: number }[];
  subtotal_centavos: number;
  desconto_cupom_centavos: number;
  taxa_entrega_centavos: number;
  total_centavos: number;
  criado_em: string;
  notificacoes: { status: string; titulo: string; mensagem: string; criado_em: string }[];
};

// ---------------------------------------------------------------------------
// Rotas
// ---------------------------------------------------------------------------

export const api = {
  // Autenticação (infra mínima — sem UC na ERS)
  entrar: (email: string, senha: string) => requisitar<Sessao>("/auth/login", json("POST", { email, senha })),
  cadastrar: (nome: string, email: string, senha: string, aceite_termos: boolean) =>
    requisitar<Cliente>("/auth/cadastro", json("POST", { nome, email, senha, aceite_termos })),
  sair: () => requisitar<void>("/auth/logout", json("POST")),
  eu: () => requisitar<Cliente>("/clientes/me"),

  // Unidades e cardápio (públicas, RN-01)
  unidades: () => requisitar<Unidade[]>("/unidades"),
  cardapio: (unidadeId: number) => requisitar<Cardapio>(`/unidades/${unidadeId}/cardapio`),

  // Carrinho (UC29; adicionar e esvaziar são infra mínima)
  carrinho: () => requisitar<Carrinho>("/carrinho"),
  adicionarItem: (produto_id: number, quantidade: number, observacao: string | null) =>
    requisitar<Carrinho>("/carrinho/itens", json("POST", { produto_id, quantidade, observacao })),
  alterarItem: (itemId: number, mudanca: { quantidade?: number; observacao?: string | null }) =>
    requisitar<Carrinho>(`/carrinho/itens/${itemId}`, json("PATCH", mudanca)),
  removerItem: (itemId: number) => requisitar<Carrinho>(`/carrinho/itens/${itemId}`, json("DELETE")),
  esvaziarCarrinho: () => requisitar<Carrinho>("/carrinho", json("DELETE")),

  // Finalizar pedido (UC28)
  enderecos: () => requisitar<Endereco[]>("/enderecos"),
  previa: (tipo_atendimento: TipoAtendimento, endereco_id: number | null) =>
    requisitar<Previa>("/pedidos/previa", json("POST", { tipo_atendimento, endereco_id })),
  confirmarPedido: (tipo_atendimento: TipoAtendimento, endereco_id: number | null, total_centavos: number) =>
    requisitar<Pedido>("/pedidos", json("POST", { tipo_atendimento, endereco_id, total_centavos })),
};
