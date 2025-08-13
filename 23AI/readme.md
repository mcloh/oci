# Instalação de Modelo ONNX no Oracle Autonomous Database 23AI

Este script PL/SQL realiza a instalação de um modelo ONNX de embeddings no Oracle Autonomous Database 23AI, utilizando os recursos nativos da OCI e do pacote `DBMS_VECTOR`.

## 🧩 Objetivo

Carregar o modelo `all-MiniLM-L12-v2.onnx` a partir de um bucket no Oracle Object Storage e registrá-lo no banco para uso com `DBMS_VECTOR.EMBED_TEXT`.

---

## 📁 Pré-Requisitos

- Bucket no Oracle Object Storage com o modelo `.onnx` disponível publicamente **ou** configurado com uma `credential_name`.
- Privilégios para usar os pacotes:
  - `DBMS_CLOUD`
  - `DBMS_VECTOR`
  - `DBMS_DATA_MINING` (para drop do modelo)
- Permissão de escrita no diretório `DATA_PUMP_DIR`.

---

## 📜 Script PL/SQL

```plsql
DECLARE 
    ONNX_MOD_FILE VARCHAR2(100) := 'all_MiniLM_L12_v2.onnx';
    MODNAME VARCHAR2(500);
    LOCATION_URI VARCHAR2(300) := 'https://path/to/the/folder/where/the/model/file/is/available/';

BEGIN
    DBMS_OUTPUT.PUT_LINE('ONNX model file name in Object Storage is: '||ONNX_MOD_FILE); 

    -- Define o nome do modelo com base no nome do arquivo
    SELECT UPPER(REGEXP_SUBSTR(ONNX_MOD_FILE, '[^.]+')) INTO MODNAME FROM dual;
    DBMS_OUTPUT.PUT_LINE('Model will be loaded and saved with name: '||MODNAME);

    -- Drop do modelo anterior, se existir
    BEGIN DBMS_DATA_MINING.DROP_MODEL(model_name => MODNAME);
    EXCEPTION WHEN OTHERS THEN NULL; END;

    -- Download do modelo do Object Storage para o banco
    DBMS_CLOUD.GET_OBJECT(                            
        credential_name => NULL,
        directory_name => 'DATA_PUMP_DIR',
        object_uri => LOCATION_URI || ONNX_MOD_FILE);

    -- Registro do modelo no banco
    DBMS_VECTOR.LOAD_ONNX_MODEL(
        directory => 'DATA_PUMP_DIR',
        file_name => ONNX_MOD_FILE,
        model_name => MODNAME);

    DBMS_OUTPUT.PUT_LINE('New model successfully loaded with name: '||MODNAME);
END;
```

---

## ✅ Pós-Instalação

### Validar se o modelo foi carregado:
```sql
SELECT model_name, model_type, created_on 
FROM all_models 
WHERE model_name = 'ALL_MINILM_L12_V2';
```

### Gerar Embedding de um texto:
```sql
SELECT DBMS_VECTOR.EMBED_TEXT(
         'ALL_MINILM_L12_V2', 
         'Exemplo de texto para embedding'
       ) AS emb 
FROM dual;
```

---

## 📌 Observações

- O nome do modelo será sempre o nome do arquivo em maiúsculas, sem a extensão.
- A função `EMBED_TEXT` exige que o modelo seja do tipo embedding ONNX com entrada de string.
- Sessões que usam `DBMS_VECTOR` devem garantir que o modelo foi carregado previamente no ambiente.

---
