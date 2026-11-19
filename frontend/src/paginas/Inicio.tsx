// Tela 02 – Início / Unidades. A ERS não pede distância/horário na lista de
// unidades nem o SGL simulado os envia: mostramos endereço e drive-thru (RN-04).
import { api } from "../api";
import { Aviso, BarraSacola, Botao, Carregando, Cartao, IconeLoja, Selo, Tela } from "../componentes";
import { useCarrinho } from "../contextos/Carrinho";
import { useSessao } from "../contextos/Sessao";
import { ir } from "../navegacao";
import { useCarregar } from "../useCarregar";

export default function Inicio() {
  const { cliente, unidadeId, escolherUnidade } = useSessao();
  const { carrinho } = useCarrinho();
  const { dados: unidades, erro, carregando, recarregar } = useCarregar(api.unidades, []);
  const unidadeDaSacola = carrinho?.itens.length ? carrinho.unidade?.id : undefined;

  const cabecalho = (
    <header className="cabecalho-marca">
      <p className="cabecalho-marca__sobre">{cliente ? "Que bom te ver por aqui" : "Peça pelo app"}</p>
      <h1 className="cabecalho-marca__titulo">{cliente ? `Olá, ${cliente.nome.split(" ")[0]}!` : "Olá!"}</h1>
      {!cliente ? (
        <a href="#/entrar" className="cabecalho-marca__link">Entrar ou criar conta</a>
      ) : null}
    </header>
  );

  return (
    <Tela cabecalho={cabecalho} aba="inicio" fundo="cinza">
      <div className="banner">
        <p className="banner__sobre">BURGUERJÁ</p>
        <p className="banner__titulo">Entrega, retirada ou drive-thru</p>
        <p className="banner__texto">Escolha uma unidade para ver o cardápio do dia.</p>
      </div>

      <h2 className="titulo-secao">Unidades</h2>
      {carregando ? <Carregando /> : null}
      {erro ? (
        <Aviso tom="erro" acao={<Botao variante="texto" onClick={recarregar}>Tentar de novo</Botao>}>{erro}</Aviso>
      ) : null}
      <div className="pilha">
        {unidades?.map((u) => (
          <Cartao key={u.id} selecionado={u.id === unidadeId}
            aoClicar={() => { escolherUnidade(u.id); ir({ tela: "cardapio" }); }}>
            <div className="linha-unidade">
              <div className="linha-unidade__icone"><IconeLoja /></div>
              <div className="linha-unidade__texto">
                <strong>{u.nome}</strong>
                <span className="texto-suave">{u.rua}, {u.numero} • {u.bairro}</span>
                <span className="linha-unidade__selos">
                  {u.tem_drive_thru ? <Selo tom="aviso">Drive-thru</Selo> : null}
                  {u.id === unidadeDaSacola ? <Selo tom="sucesso">Sua sacola</Selo> : null}
                </span>
              </div>
            </div>
          </Cartao>
        ))}
      </div>
      <BarraSacola />
    </Tela>
  );
}
