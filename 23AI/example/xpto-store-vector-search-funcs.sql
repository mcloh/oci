-- Vector Search Function for CLIENTES
CREATE OR REPLACE FUNCTION xpto_store.search_clientes_vetoriais(
    termo_busca VARCHAR2,
    n_resultados NUMBER DEFAULT 5
) RETURN SYS_REFCURSOR
IS
    resultado SYS_REFCURSOR;
BEGIN
    OPEN resultado FOR
        SELECT
            id_cliente as DOCID,
            nome as BODY,
            COSINE_DISTANCE(
                vetor_nome_email,
                VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING termo_busca AS DATA)
            ) AS SCORE
        FROM
            xpto_store.xpto_clientes
        WHERE
            vetor_nome_email IS NOT NULL
        ORDER BY
            SCORE
        FETCH FIRST n_resultados ROWS ONLY;
    RETURN resultado;
END;

-- Vector Search Function for PRODUTOS
CREATE OR REPLACE FUNCTION xpto_store.search_produtos_vetoriais(
    termo_busca VARCHAR2,
    n_resultados NUMBER DEFAULT 5
) RETURN SYS_REFCURSOR
IS
    resultado SYS_REFCURSOR;
BEGIN
    OPEN resultado FOR
        SELECT
            id_produto as DOCID,
            nome as BODY,
            COSINE_DISTANCE(
                vetor_descricao,
                VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING termo_busca AS DATA)
            ) AS SCORE
        FROM
            xpto_store.xpto_produtos
        WHERE
            vetor_descricao IS NOT NULL
        ORDER BY
            SCORE
        FETCH FIRST n_resultados ROWS ONLY;
    RETURN resultado;
END;

-- Vector Search Function for CATEGORIAS
CREATE OR REPLACE FUNCTION xpto_store.search_categorias_vetoriais(
    termo_busca VARCHAR2,
    n_resultados NUMBER DEFAULT 5
) 
RETURN SYS_REFCURSOR
IS
    resultado SYS_REFCURSOR;
BEGIN
    OPEN resultado FOR
        SELECT
            id_categoria as DOCID,
            nome as BODY,
            COSINE_DISTANCE(
                vetor_nome_descricao,
                VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING termo_busca AS DATA)
            ) AS SCORE
        FROM
            xpto_store.xpto_categorias
        WHERE
            vetor_nome_descricao IS NOT NULL
        ORDER BY
            SCORE
        FETCH FIRST n_resultados ROWS ONLY;
    RETURN resultado;
END;
