-- Esquema do banco, alinhado ao projeto relacional do grupo
-- (docs/srs/Projeto_Relacional_de_Tabelas.drawio, Apêndice B.3 da ERS).
--
-- Diferenças em relação ao diagrama, decididas pelo grupo ou exigidas pela ERS:
-- - Dinheiro em centavos inteiros (INTEGER, sufixo _centavos), não DECIMAL (RNF-23).
-- - Status "SAIU_PARA_ENTREGA" (RF-21), não "EM_ROTA".
-- - ENUM e BOOLEAN não existem no SQLite: CHECK (... IN ...) e INTEGER 0/1.
-- - Colunas a mais, marcadas "extra" abaixo, que o diagrama não tem mas a ERS ou
--   uma decisão do grupo exigem (sessão, bloqueio de login, cache do SGL...).
-- - Tabelas de pagamento, cartão salvo e fidelidade ainda não existem:
--   entram com os casos de uso delas (decisão do grupo em 2026-11-19).
-- - CUPOM_PROMOCIONAL (UC30): percentual_desconto DECIMAL(5,2) virou
--   percentual_desconto_centesimos INTEGER (1000 = 10,00%), para as contas de
--   dinheiro não usarem float (RNF-23); as datas de validade são texto
--   AAAA-MM-DD no horário de Brasília (RNF-24).
--
-- ON DELETE segue o diagrama: CASCADE em composições, heranças e associativas;
-- RESTRICT (padrão) nas demais FKs.

-- ===========================================================================
-- USUÁRIOS
-- ===========================================================================
-- RNF-09: só o hash bcrypt da senha. RNF-10: bloqueio após 5 erros.
-- telefone e notificacoes_habilitadas: estão no diagrama, mas não na ERS;
-- ficam opcionais e o cadastro ainda não os pede (decisão de 2026-11-19).
CREATE TABLE IF NOT EXISTS cliente (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                     TEXT    NOT NULL CHECK (length(trim(nome)) > 0),
    email                    TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    telefone                 TEXT,
    notificacoes_habilitadas INTEGER CHECK (notificacoes_habilitadas IN (0, 1)),
    senha_hash               TEXT    NOT NULL,
    data_cadastro            TEXT    NOT NULL DEFAULT (datetime('now')),
    termos_aceitos_em        TEXT    NOT NULL,                                       -- extra: RNF-25
    tentativas_login_falhas  INTEGER NOT NULL DEFAULT 0 CHECK (tentativas_login_falhas >= 0),  -- extra: RNF-10
    bloqueado_ate            TEXT                                                    -- extra: RNF-10
);

-- Extra (decisão Q6): token opaco de sessão; só o hash SHA-256 fica no banco.
CREATE TABLE IF NOT EXISTS sessao (
    token_hash TEXT    PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
    criado_em  TEXT    NOT NULL,
    expira_em  TEXT    NOT NULL
);

-- ===========================================================================
-- UNIDADE e CARDÁPIO: cópia (cache) do que vem do SGL (decisão Q2).
-- ===========================================================================
-- telefone_contato e horario_funcionamento: no diagrama, mas fora da ERS (Q5);
-- ficam opcionais.
CREATE TABLE IF NOT EXISTS unidade (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sgl                      TEXT    NOT NULL UNIQUE,                               -- extra: Q2
    nome                        TEXT    NOT NULL,
    telefone_contato            TEXT,
    horario_funcionamento       TEXT,
    aceita_drive_thru           INTEGER NOT NULL CHECK (aceita_drive_thru IN (0, 1)),  -- RN-04
    distancia_maxima_km         REAL    NOT NULL CHECK (distancia_maxima_km >= 0),     -- RF-06, RN-04
    fator_taxa_entrega_centavos INTEGER NOT NULL CHECK (fator_taxa_entrega_centavos >= 0),  -- RN-05 (centavos por km)
    latitude                    REAL    NOT NULL,                                      -- extra: RF-06
    longitude                   REAL    NOT NULL,                                      -- extra: RF-06
    cardapio_atualizado_em      TEXT                                                   -- extra: UC29 E3, RNF-03
);

CREATE TABLE IF NOT EXISTS endereco_unidade (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    unidade_id  INTEGER NOT NULL UNIQUE REFERENCES unidade(id) ON DELETE CASCADE,
    logradouro  TEXT    NOT NULL,
    numero      TEXT    NOT NULL,
    complemento TEXT,
    bairro      TEXT    NOT NULL,
    cidade      TEXT    NOT NULL,
    estado      TEXT    NOT NULL,
    cep         TEXT    NOT NULL
);

-- Um cardápio por unidade. CARDAPIO_ITEM diz quais itens ele tem HOJE: item que
-- sai do cardápio perde a ligação, mas ITEM_CARDAPIO fica (RNF-22: pedidos
-- antigos continuam apontando para ele).
CREATE TABLE IF NOT EXISTS cardapio (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    unidade_id INTEGER NOT NULL UNIQUE REFERENCES unidade(id) ON DELETE CASCADE
);

-- Item é da rede, não da unidade: o mesmo id_sgl é o mesmo item (e o mesmo
-- preço) em todas as unidades que o oferecem.
CREATE TABLE IF NOT EXISTS item_cardapio (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sgl    TEXT    NOT NULL UNIQUE,         -- extra: Q2
    nome      TEXT    NOT NULL,
    descricao TEXT    NOT NULL DEFAULT '',
    categoria TEXT    NOT NULL                 -- extra: filtro do cardápio (wireframe 03)
);

CREATE TABLE IF NOT EXISTS cardapio_item (
    cardapio_id      INTEGER NOT NULL REFERENCES cardapio(id) ON DELETE CASCADE,
    item_cardapio_id INTEGER NOT NULL REFERENCES item_cardapio(id),
    PRIMARY KEY (cardapio_id, item_cardapio_id)
);

-- Herança Table-Per-Type: cada ITEM_CARDAPIO está em ITEM_SIMPLES ou em COMBO.
CREATE TABLE IF NOT EXISTS item_simples (
    item_cardapio_id        INTEGER PRIMARY KEY REFERENCES item_cardapio(id) ON DELETE CASCADE,
    preco_centavos          INTEGER NOT NULL CHECK (preco_centavos >= 0),
    desconto_item_centavos  INTEGER NOT NULL DEFAULT 0
                            CHECK (desconto_item_centavos BETWEEN 0 AND preco_centavos)  -- RF-10
);

-- Combo não tem preço próprio: vale a soma dos componentes (RF-11).
CREATE TABLE IF NOT EXISTS combo (
    item_cardapio_id INTEGER PRIMARY KEY REFERENCES item_cardapio(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS item_no_combo (
    combo_id        INTEGER NOT NULL REFERENCES combo(item_cardapio_id) ON DELETE CASCADE,
    item_simples_id INTEGER NOT NULL REFERENCES item_simples(item_cardapio_id),
    quantidade      INTEGER NOT NULL CHECK (quantidade >= 1),
    PRIMARY KEY (combo_id, item_simples_id)
);

-- Trigger do diagrama: cada ITEM_CARDAPIO em exatamente uma subtabela.
CREATE TRIGGER IF NOT EXISTS item_simples_nao_e_combo
BEFORE INSERT ON item_simples
WHEN EXISTS (SELECT 1 FROM combo WHERE item_cardapio_id = NEW.item_cardapio_id)
BEGIN
    SELECT RAISE(ABORT, 'item do cardápio já é combo');
END;

CREATE TRIGGER IF NOT EXISTS combo_nao_e_item_simples
BEFORE INSERT ON combo
WHEN EXISTS (SELECT 1 FROM item_simples WHERE item_cardapio_id = NEW.item_cardapio_id)
BEGIN
    SELECT RAISE(ABORT, 'item do cardápio já é item simples');
END;

-- Trigger do diagrama: todo combo tem 2 ou mais itens. Conferido quando o combo
-- entra num cardápio (antes disso, os componentes ainda estão sendo gravados).
CREATE TRIGGER IF NOT EXISTS combo_com_dois_itens
BEFORE INSERT ON cardapio_item
WHEN EXISTS (SELECT 1 FROM combo WHERE item_cardapio_id = NEW.item_cardapio_id)
     AND (SELECT COUNT(*) FROM item_no_combo WHERE combo_id = NEW.item_cardapio_id) < 2
BEGIN
    SELECT RAISE(ABORT, 'combo precisa de 2 ou mais itens');
END;

CREATE TRIGGER IF NOT EXISTS item_cardapio_tem_subtipo
BEFORE INSERT ON cardapio_item
WHEN NOT EXISTS (SELECT 1 FROM item_simples WHERE item_cardapio_id = NEW.item_cardapio_id)
     AND NOT EXISTS (SELECT 1 FROM combo WHERE item_cardapio_id = NEW.item_cardapio_id)
BEGIN
    SELECT RAISE(ABORT, 'item do cardápio sem tipo (simples ou combo)');
END;

-- ===========================================================================
-- ENDEREÇOS DO CLIENTE (UC33). Só "complemento" é opcional (RF-29).
-- RF-32: excluir a conta exclui os endereços.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS endereco_cliente (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id  INTEGER NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
    logradouro  TEXT    NOT NULL CHECK (length(trim(logradouro)) > 0),
    numero      TEXT    NOT NULL CHECK (length(trim(numero)) > 0),
    complemento TEXT,
    bairro      TEXT    NOT NULL CHECK (length(trim(bairro)) > 0),
    cidade      TEXT    NOT NULL CHECK (length(trim(cidade)) > 0),
    estado      TEXT    NOT NULL CHECK (length(trim(estado)) > 0),
    cep         TEXT    NOT NULL CHECK (length(trim(cep)) > 0)
);

-- ===========================================================================
-- CARRINHO (RF-08): um por cliente, ligado a uma unidade (RN-03).
-- ===========================================================================
CREATE TABLE IF NOT EXISTS carrinho (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id    INTEGER NOT NULL UNIQUE REFERENCES cliente(id) ON DELETE CASCADE,
    unidade_id    INTEGER NOT NULL REFERENCES unidade(id),
    atualizado_em TEXT    NOT NULL DEFAULT (datetime('now'))   -- extra
);

-- ===========================================================================
-- PEDIDO (UC28). Pagamento e fidelidade entram com os UCs deles.
-- Totais não são colunas: subtotal = soma de ITEM_PEDIDO.valor_final;
-- total = subtotal − cupom (USO_CUPOM.valor_descontado) + taxa (UC28 passo 8).
-- Cupom que isenta a taxa grava taxa_entrega_centavos = 0 (UC30 passo 4).
-- ===========================================================================
CREATE TABLE IF NOT EXISTS pedido (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id            INTEGER NOT NULL REFERENCES cliente(id),
    unidade_id            INTEGER NOT NULL REFERENCES unidade(id),  -- RF-01
    data_hora             TEXT    NOT NULL,
    modalidade            TEXT    NOT NULL CHECK (modalidade IN ('ENTREGA', 'RETIRADA', 'DRIVE_THRU')),
    status                TEXT    NOT NULL CHECK (status IN (
                              'RECEBIDO', 'PAGO', 'EM_PREPARO', 'PRONTO',
                              'SAIU_PARA_ENTREGA', 'ENTREGUE', 'CANCELADO')),  -- RF-21
    taxa_entrega_centavos INTEGER NOT NULL DEFAULT 0 CHECK (taxa_entrega_centavos >= 0),
    previsao_entrega      TEXT,
    -- Diagrama / RF-04: previsão de entrega se, e somente se, for entrega.
    CHECK ((modalidade = 'ENTREGA') = (previsao_entrega IS NOT NULL)),
    -- RN-05: retirada e drive-thru não têm taxa de entrega.
    CHECK (modalidade = 'ENTREGA' OR taxa_entrega_centavos = 0)
);

-- Cópia do endereço no momento do pedido (RF-05, RF-31), não FK para
-- endereco_cliente. Existe se, e somente se, a modalidade for ENTREGA: o
-- trigger barra endereço em pedido sem entrega; o "somente se" é garantido
-- pelo checkout, que grava pedido e endereço na mesma transação.
CREATE TABLE IF NOT EXISTS endereco_pedido (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id   INTEGER NOT NULL UNIQUE REFERENCES pedido(id) ON DELETE CASCADE,
    logradouro  TEXT    NOT NULL,
    numero      TEXT    NOT NULL,
    complemento TEXT,
    bairro      TEXT    NOT NULL,
    cidade      TEXT    NOT NULL,
    estado      TEXT    NOT NULL,
    cep         TEXT    NOT NULL
);

CREATE TRIGGER IF NOT EXISTS endereco_pedido_so_em_entrega
BEFORE INSERT ON endereco_pedido
WHEN (SELECT modalidade FROM pedido WHERE id = NEW.pedido_id) <> 'ENTREGA'
BEGIN
    SELECT RAISE(ABORT, 'endereço de entrega só em pedido com modalidade ENTREGA');
END;

-- Item de carrinho OU de pedido, nunca os dois (RF-09, RNF-21).
-- No carrinho os valores são recalculados com o preço atual a cada leitura
-- (RF-13); quando pedido_id é preenchido ficam congelados (RF-03, RN-06).
-- Combo: preço e desconto = soma dos itens de ITEM_NO_COMBO (RF-11).
CREATE TABLE IF NOT EXISTS item_pedido (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    carrinho_id                INTEGER REFERENCES carrinho(id) ON DELETE CASCADE,
    pedido_id                  INTEGER REFERENCES pedido(id) ON DELETE CASCADE,
    item_cardapio_id           INTEGER NOT NULL REFERENCES item_cardapio(id),
    quantidade                 INTEGER NOT NULL CHECK (quantidade > 0),  -- RF-12
    preco_unitario_centavos    INTEGER NOT NULL,
    desconto_unitario_centavos INTEGER NOT NULL,
    valor_final_centavos       INTEGER NOT NULL,
    observacao                 TEXT,
    CHECK ((carrinho_id IS NULL) <> (pedido_id IS NULL)),  -- RF-09 (XOR)
    CHECK (desconto_unitario_centavos BETWEEN 0 AND preco_unitario_centavos),  -- RF-10
    CHECK (valor_final_centavos
           = quantidade * (preco_unitario_centavos - desconto_unitario_centavos))  -- RF-02
);

-- Trigger do diagrama: item de pedido não muda depois de congelado (RF-03, RN-06).
CREATE TRIGGER IF NOT EXISTS item_pedido_congelado
BEFORE UPDATE ON item_pedido
WHEN OLD.pedido_id IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'item de pedido não pode ser alterado (RF-03)');
END;

-- ===========================================================================
-- PÓS-VENDA: linha do tempo do pedido (RF-20, RF-22). Nunca apagada (RNF-22).
-- ===========================================================================
CREATE TABLE IF NOT EXISTS notificacao (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    status    TEXT    NOT NULL CHECK (status IN (
                  'RECEBIDO', 'PAGO', 'EM_PREPARO', 'PRONTO',
                  'SAIU_PARA_ENTREGA', 'ENTREGUE', 'CANCELADO')),
    data_hora TEXT    NOT NULL,
    titulo    TEXT    NOT NULL,
    mensagem  TEXT    NOT NULL
);

-- Trigger do diagrama: PEDIDO.status = status da notificação mais recente,
-- na mesma transação.
CREATE TRIGGER IF NOT EXISTS pedido_status_da_notificacao
AFTER INSERT ON notificacao
BEGIN
    UPDATE pedido SET status = NEW.status WHERE id = NEW.pedido_id;
END;

-- RNF-22: pedidos e notificações nunca são apagados fisicamente.
CREATE TRIGGER IF NOT EXISTS pedido_nunca_apagado
BEFORE DELETE ON pedido
BEGIN
    SELECT RAISE(ABORT, 'pedido não pode ser apagado (RNF-22)');
END;

CREATE TRIGGER IF NOT EXISTS notificacao_nunca_apagada
BEFORE DELETE ON notificacao
BEGIN
    SELECT RAISE(ABORT, 'notificação não pode ser apagada (RNF-22)');
END;

-- ===========================================================================
-- CUPONS PROMOCIONAIS (UC30, RF-14 a RF-18, RN-07).
-- ===========================================================================
-- Cada cupom pertence a um único cliente (RF-15: UNIQUE(cliente_id, codigo)).
-- percentual_desconto_centesimos: 1000 = 10,00% (inteiro, sem float, RNF-23).
-- valor_maximo_desconto_centavos: teto opcional em centavos (NULL = sem teto).
CREATE TABLE IF NOT EXISTS cupom_promocional (
    id                             INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id                     INTEGER NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
    codigo                         TEXT    NOT NULL COLLATE NOCASE CHECK (length(trim(codigo)) > 0),
    descricao                      TEXT    NOT NULL DEFAULT '',
    percentual_desconto_centesimos INTEGER NOT NULL DEFAULT 0
                                   CHECK (percentual_desconto_centesimos BETWEEN 0 AND 10000),
    valor_maximo_desconto_centavos INTEGER CHECK (valor_maximo_desconto_centavos IS NULL
                                                  OR valor_maximo_desconto_centavos >= 0),
    isenta_taxa_entrega            INTEGER NOT NULL DEFAULT 0 CHECK (isenta_taxa_entrega IN (0, 1)),
    valor_minimo_pedido_centavos   INTEGER NOT NULL DEFAULT 0 CHECK (valor_minimo_pedido_centavos >= 0),
    validade_inicio                TEXT    NOT NULL,
    validade_fim                   TEXT    NOT NULL,
    limite_usos                    INTEGER NOT NULL CHECK (limite_usos >= 1),
    UNIQUE (cliente_id, codigo),                                                  -- RF-15
    CHECK (validade_inicio <= validade_fim),
    CHECK (percentual_desconto_centesimos > 0 OR isenta_taxa_entrega = 1)
);

-- Registro do uso do cupom quando o pedido é confirmado (UC30 passo 6, RF-17).
-- No máximo um cupom por pedido (RF-14: pedido_id UNIQUE).
-- Nunca apagado fisicamente (RNF-22).
CREATE TABLE IF NOT EXISTS uso_cupom (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id                 INTEGER NOT NULL UNIQUE REFERENCES pedido(id) ON DELETE CASCADE,  -- RF-14
    cupom_id                  INTEGER NOT NULL REFERENCES cupom_promocional(id),
    valor_descontado_centavos INTEGER NOT NULL CHECK (valor_descontado_centavos >= 0)
);

-- Trigger: o cupom usado num pedido deve pertencer ao mesmo cliente do pedido (RF-15, RN-02, RNF-13)
-- e o número de usos em pedidos não cancelados não pode passar de limite_usos (RF-16, RF-17, RN-07).
CREATE TRIGGER IF NOT EXISTS uso_cupom_valido
BEFORE INSERT ON uso_cupom
BEGIN
    SELECT CASE
        WHEN (SELECT cliente_id FROM cupom_promocional WHERE id = NEW.cupom_id)
             <> (SELECT cliente_id FROM pedido WHERE id = NEW.pedido_id)
        THEN RAISE(ABORT, 'cupom não pertence ao cliente do pedido (RF-15)')
        WHEN (
            SELECT COUNT(*)
              FROM uso_cupom u
              JOIN pedido p ON p.id = u.pedido_id
             WHERE u.cupom_id = NEW.cupom_id
               AND p.status <> 'CANCELADO'
        ) >= (SELECT limite_usos FROM cupom_promocional WHERE id = NEW.cupom_id)
        THEN RAISE(ABORT, 'limite de usos do cupom atingido (RF-16)')
    END;
END;

-- RNF-22: usos de cupom nunca são apagados fisicamente.
CREATE TRIGGER IF NOT EXISTS uso_cupom_nunca_apagado
BEFORE DELETE ON uso_cupom
BEGIN
    SELECT RAISE(ABORT, 'uso de cupom não pode ser apagado (RNF-22)');
END;
