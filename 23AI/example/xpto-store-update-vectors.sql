-- Atualizar vetor_descricao em xpto_produtos
UPDATE xpto_store.xpto_produtos
SET vetor_descricao = VECTOR_EMBEDDING(
  ALL_MINILM_L12_V2 USING nome || ' - ' || descricao AS DATA
)
WHERE vetor_descricao IS NULL;

-- Atualizar vetor_nome_descricao em xpto_categorias
UPDATE xpto_store.xpto_categorias
SET vetor_nome_descricao = VECTOR_EMBEDDING(
  ALL_MINILM_L12_V2 USING nome || ' - ' || descricao AS DATA
)
WHERE vetor_nome_descricao IS NULL;

-- Atualizar vetor_nome_email em xpto_clientes
UPDATE xpto_store.xpto_clientes
SET vetor_nome_email = VECTOR_EMBEDDING(
  ALL_MINILM_L12_V2 USING nome || ' ' || email || ' ' || uf AS DATA
)
WHERE vetor_nome_email IS NULL;

-- Criar índices vetoriais
CREATE INDEX idx_vetor_descricao
  ON xpto_store.xpto_produtos (vetor_descricao)
  INDEXTYPE IS VECTOR;

CREATE INDEX idx_vetor_nome_descricao
  ON xpto_store.xpto_categorias (vetor_nome_descricao)
  INDEXTYPE IS VECTOR;

CREATE INDEX idx_vetor_nome_email
  ON xpto_store.xpto_clientes (vetor_nome_email)
  INDEXTYPE IS VECTOR;
