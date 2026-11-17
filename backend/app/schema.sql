-- Esquema do banco. Tabela "recado" é só um teste de integração:
-- remova quando as tabelas reais da ERS forem criadas.
CREATE TABLE IF NOT EXISTS recado (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    texto     TEXT    NOT NULL,
    criado_em TEXT    NOT NULL DEFAULT (datetime('now'))
);
