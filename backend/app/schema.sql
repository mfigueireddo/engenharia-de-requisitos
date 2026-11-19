-- Esquema do banco.

-- ---------------------------------------------------------------------------
-- Clientes e sessões — infra mínima, sem UC na ERS (decisão Q1, Q6).
-- RNF-09: só o hash bcrypt da senha. RNF-10: bloqueio após 5 erros.
-- RNF-25: aceite dos termos registrado no cadastro.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cliente (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                    TEXT    NOT NULL CHECK (length(trim(nome)) > 0),
    email                   TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    senha_hash              TEXT    NOT NULL,
    termos_aceitos_em       TEXT    NOT NULL,
    tentativas_login_falhas INTEGER NOT NULL DEFAULT 0 CHECK (tentativas_login_falhas >= 0),
    bloqueado_ate           TEXT,
    criado_em               TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Token opaco: só o hash SHA-256 fica no banco (decisão Q6).
CREATE TABLE IF NOT EXISTS sessao (
    token_hash TEXT    PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
    criado_em  TEXT    NOT NULL,
    expira_em  TEXT    NOT NULL
);

-- ---------------------------------------------------------------------------
-- Unidades e cardápio: cópia (cache) do que vem do SGL (decisão Q2).
-- Produtos que saem do cardápio ficam com vigente = 0, não são apagados (RNF-22).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS unidade (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sgl                      TEXT    NOT NULL UNIQUE,
    nome                        TEXT    NOT NULL,
    rua                         TEXT    NOT NULL,
    numero                      TEXT    NOT NULL,
    bairro                      TEXT    NOT NULL,
    cidade                      TEXT    NOT NULL,
    estado                      TEXT    NOT NULL,
    cep                         TEXT    NOT NULL,
    latitude                    REAL    NOT NULL,  -- RF-06 (UC28)
    longitude                   REAL    NOT NULL,  -- RF-06 (UC28)
    raio_max_entrega_m          INTEGER NOT NULL CHECK (raio_max_entrega_m >= 0),           -- RF-06, RN-04
    fator_taxa_entrega_centavos INTEGER NOT NULL CHECK (fator_taxa_entrega_centavos >= 0),  -- RN-05
    tem_drive_thru              INTEGER NOT NULL CHECK (tem_drive_thru IN (0, 1)),          -- RN-04
    cardapio_atualizado_em      TEXT                                                        -- UC29 E3, RNF-03
);

-- Combo não tem preço próprio: vale a soma dos componentes (RF-11).
CREATE TABLE IF NOT EXISTS produto (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    unidade_id        INTEGER NOT NULL REFERENCES unidade(id),
    id_sgl            TEXT    NOT NULL,
    nome              TEXT    NOT NULL,
    descricao         TEXT    NOT NULL DEFAULT '',
    categoria         TEXT    NOT NULL,
    tipo              TEXT    NOT NULL CHECK (tipo IN ('SIMPLES', 'COMBO')),
    preco_centavos    INTEGER,
    desconto_centavos INTEGER,
    vigente           INTEGER NOT NULL DEFAULT 1 CHECK (vigente IN (0, 1)),
    UNIQUE (unidade_id, id_sgl),
    CHECK (
        (tipo = 'COMBO' AND preco_centavos IS NULL AND desconto_centavos IS NULL)
        OR (tipo = 'SIMPLES' AND preco_centavos >= 0
            AND desconto_centavos BETWEEN 0 AND preco_centavos)  -- RF-10
    )
);

CREATE TABLE IF NOT EXISTS combo_componente (
    combo_id   INTEGER NOT NULL REFERENCES produto(id),
    produto_id INTEGER NOT NULL REFERENCES produto(id),
    quantidade INTEGER NOT NULL CHECK (quantidade >= 1),
    PRIMARY KEY (combo_id, produto_id)
);

-- ---------------------------------------------------------------------------
-- Carrinho (RF-08): um por cliente, ligado a uma unidade (RN-03).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carrinho (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id    INTEGER NOT NULL UNIQUE REFERENCES cliente(id) ON DELETE CASCADE,
    unidade_id    INTEGER NOT NULL REFERENCES unidade(id),
    atualizado_em TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- Endereços salvos (UC33). Aqui só a tabela, usada pelo UC28; cadastrar, editar
-- e remover ficam para o UC33 (outro integrante).
-- RF-29: só "complemento" é opcional. RF-32: excluir a conta exclui os endereços.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS endereco (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id  INTEGER NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
    rua         TEXT    NOT NULL CHECK (length(trim(rua)) > 0),
    numero      TEXT    NOT NULL CHECK (length(trim(numero)) > 0),
    complemento TEXT,
    bairro      TEXT    NOT NULL CHECK (length(trim(bairro)) > 0),
    cidade      TEXT    NOT NULL CHECK (length(trim(cidade)) > 0),
    estado      TEXT    NOT NULL CHECK (length(trim(estado)) > 0),
    cep         TEXT    NOT NULL CHECK (length(trim(cep)) > 0)
);

-- ---------------------------------------------------------------------------
-- Pedido (UC28). Pagamento, envio ao SGL e acompanhamento ficam para os UCs
-- seguintes. O endereço é uma CÓPIA (RF-05, RF-31), não uma FK para endereco.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedido (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id              INTEGER NOT NULL REFERENCES cliente(id),
    unidade_id              INTEGER NOT NULL REFERENCES unidade(id),  -- RF-01
    status                  TEXT    NOT NULL CHECK (status IN (
                                'RECEBIDO', 'PAGO', 'EM_PREPARO', 'PRONTO',
                                'SAIU_PARA_ENTREGA', 'ENTREGUE', 'CANCELADO')),  -- RF-21
    tipo_atendimento        TEXT    NOT NULL CHECK (tipo_atendimento IN ('ENTREGA', 'RETIRADA', 'DRIVE_THRU')),
    entrega_rua             TEXT,
    entrega_numero          TEXT,
    entrega_complemento     TEXT,
    entrega_bairro          TEXT,
    entrega_cidade          TEXT,
    entrega_estado          TEXT,
    entrega_cep             TEXT,
    distancia_m             INTEGER CHECK (distancia_m >= 0),
    tempo_estimado_min      INTEGER CHECK (tempo_estimado_min > 0),
    subtotal_centavos       INTEGER NOT NULL CHECK (subtotal_centavos >= 0),
    taxa_entrega_centavos   INTEGER NOT NULL DEFAULT 0 CHECK (taxa_entrega_centavos >= 0),
    desconto_cupom_centavos INTEGER NOT NULL DEFAULT 0 CHECK (desconto_cupom_centavos >= 0),  -- UC30 (outro integrante)
    total_centavos          INTEGER NOT NULL,
    criado_em               TEXT    NOT NULL DEFAULT (datetime('now')),
    -- UC28 passo 8: total = itens − cupom + taxa.
    CHECK (total_centavos = subtotal_centavos - desconto_cupom_centavos + taxa_entrega_centavos),
    -- RF-04: endereço e tempo estimado se, e somente se, for entrega.
    CHECK ((tipo_atendimento = 'ENTREGA') = (
        entrega_rua IS NOT NULL AND entrega_numero IS NOT NULL AND entrega_bairro IS NOT NULL
        AND entrega_cidade IS NOT NULL AND entrega_estado IS NOT NULL AND entrega_cep IS NOT NULL
        AND tempo_estimado_min IS NOT NULL AND distancia_m IS NOT NULL)),
    CHECK (tipo_atendimento = 'ENTREGA' OR (
        entrega_rua IS NULL AND entrega_numero IS NULL AND entrega_complemento IS NULL
        AND entrega_bairro IS NULL AND entrega_cidade IS NULL AND entrega_estado IS NULL
        AND entrega_cep IS NULL AND tempo_estimado_min IS NULL AND distancia_m IS NULL)),
    -- RN-05: retirada e drive-thru não têm taxa de entrega.
    CHECK (tipo_atendimento = 'ENTREGA' OR taxa_entrega_centavos = 0)
);

-- Linha do tempo do pedido (RF-20, RF-22). O UC28 registra só a primeira
-- notificação, "RECEBIDO" (passo 11); o resto é do UC31. Nunca apagada (RNF-22).
CREATE TABLE IF NOT EXISTS notificacao (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedido(id),
    status    TEXT    NOT NULL CHECK (status IN (
                  'RECEBIDO', 'PAGO', 'EM_PREPARO', 'PRONTO',
                  'SAIU_PARA_ENTREGA', 'ENTREGUE', 'CANCELADO')),
    titulo    TEXT    NOT NULL,
    mensagem  TEXT    NOT NULL,
    criado_em TEXT    NOT NULL
);

-- Item de carrinho OU de pedido, nunca os dois (RF-09, RNF-21).
-- No carrinho os valores são sempre recalculados (RF-13); no pedido ficam
-- congelados (RF-03, RN-06).
CREATE TABLE IF NOT EXISTS item (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    carrinho_id                INTEGER REFERENCES carrinho(id) ON DELETE CASCADE,
    pedido_id                  INTEGER REFERENCES pedido(id),
    produto_id                 INTEGER NOT NULL REFERENCES produto(id),
    quantidade                 INTEGER NOT NULL CHECK (quantidade >= 1),  -- RF-12
    observacao                 TEXT,
    preco_unitario_centavos    INTEGER,
    desconto_unitario_centavos INTEGER,
    valor_final_centavos       INTEGER,
    CHECK ((carrinho_id IS NULL) <> (pedido_id IS NULL)),  -- RF-09 (XOR)
    CHECK (pedido_id IS NULL OR (preco_unitario_centavos IS NOT NULL
           AND desconto_unitario_centavos IS NOT NULL AND valor_final_centavos IS NOT NULL))
);

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
