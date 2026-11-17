-- Esquema do banco.
-- ESBOÇO-PROVISÓRIO: a tabela "recado" é só um teste de integração (AGENTS.md, seção 7):
-- remova quando as tabelas reais da ERS forem criadas.
CREATE TABLE IF NOT EXISTS recado (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    texto     TEXT    NOT NULL,
    criado_em TEXT    NOT NULL DEFAULT (datetime('now'))
);
