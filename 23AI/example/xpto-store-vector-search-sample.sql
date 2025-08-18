-- Return an aggregation from a Natural Language string 
WITH produto_similar as (
  SELECT
    p.id_produto,
    p.nome,
    p.descricao,
    COSINE_DISTANCE(
      p.vetor_descricao,
      VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING 'qual é o total de vendas das colheitadeiras?' AS DATA)
    ) AS distance
  FROM xpto_store.xpto_produtos p
  WHERE p.vetor_descricao IS NOT NULL
  ORDER BY distance ASC
  FETCH FIRST 1 ROWS ONLY
) 
SELECT
  ps.nome AS nome_produto,
  ps.descricao AS descricao,
  SUM(vendas.quantidade) AS total_unidades_vendidas,
  SUM(vendas.valor_total) AS valor_total_vendido
FROM
  produto_similar ps
JOIN
  xpto_store.xpto_vendas vendas ON vendas.id_produto = ps.id_produto
GROUP BY
  ps.nome, ps.descricao
