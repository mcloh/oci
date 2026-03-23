# ADW 26AI — Compartilhamento de Modelo ONNX entre Schemas

## 🎯 Objetivo

Permitir que um schema (`APP_SCHEMA`) utilize um modelo ONNX (`MY_ONNX_MODEL`) pertencente a outro schema (`SRC_SCHEMA`) no Autonomous Data Warehouse (ADW 26AI), incluindo integração com Select AI.

---

## 📌 Pré-requisitos

* Modelo ONNX já carregado no `SRC_SCHEMA`
* Acesso como `ADMIN`
* Usuário consumidor (`APP_SCHEMA`) criado

---

## 1️⃣ Validar modelo no schema de origem

Conecte como `SRC_SCHEMA`:

```sql
SELECT model_name, algorithm, mining_function
FROM user_mining_models
WHERE model_name = 'MY_ONNX_MODEL';
```

---

## 2️⃣ Grants básicos (executar como ADMIN)

```sql
GRANT CREATE SESSION TO APP_SCHEMA;
GRANT DWROLE TO APP_SCHEMA;

GRANT EXECUTE ON DBMS_CLOUD TO APP_SCHEMA;
GRANT EXECUTE ON DBMS_CLOUD_AI TO APP_SCHEMA;
```

### (Opcional) Diretório para operações com arquivos

```sql
GRANT READ, WRITE ON DIRECTORY DATA_PUMP_DIR TO APP_SCHEMA;
```

---

## 3️⃣ Habilitar acesso a dados para Select AI (ADMIN)

```sql
BEGIN
  DBMS_CLOUD_AI.ENABLE_DATA_ACCESS();
END;
/
```

---

## 4️⃣ Grant no modelo ONNX (acesso entre schemas)

Conecte como `SRC_SCHEMA`:

```sql
GRANT SELECT MINING MODEL ON MY_ONNX_MODEL TO APP_SCHEMA;
```

### Alternativa (mais ampla)

```sql
GRANT SELECT ANY MINING MODEL TO APP_SCHEMA;
```

---

## 5️⃣ Observação sobre "alias"

* ❌ Não é necessário criar alias ou synonym
* ✅ Use nome qualificado do modelo:

```
SRC_SCHEMA.MY_ONNX_MODEL
```

---

## 6️⃣ Criar credential (APP_SCHEMA)

```sql
BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => 'GENAI_CRED',
    user_ocid       => '<user_ocid>',
    tenancy_ocid    => '<tenancy_ocid>',
    private_key     => '<private_key>',
    fingerprint     => '<fingerprint>'
  );
END;
/
```

---

## 7️⃣ Criar profile do Select AI

### 🔹 Apenas embedding (modelo interno)

```sql
BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
    profile_name => 'EMBEDDING_PROFILE',
    attributes   => '{
      "provider": "database",
      "embedding_model": "SRC_SCHEMA.MY_ONNX_MODEL"
    }'
  );
END;
/
```

---

### 🔹 LLM externo + embedding ONNX

```sql
BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
    profile_name => 'OCI_GENAI',
    attributes   => '{
      "provider": "oci",
      "model": "meta.llama-3.3-70b-instruct",
      "credential_name": "GENAI_CRED",
      "embedding_model": "database: SRC_SCHEMA.MY_ONNX_MODEL"
    }'
  );
END;
/
```

---

## 8️⃣ Ativar profile

```sql
EXEC DBMS_CLOUD_AI.SET_PROFILE('OCI_GENAI');
```

---

## 9️⃣ Teste do modelo

```sql
SELECT VECTOR_EMBEDDING(
  SRC_SCHEMA.MY_ONNX_MODEL 
  USING 'texto de teste' AS data
)
FROM dual;
```

---

## ✅ Resumo rápido

| Etapa | Ação                              |
| ----- | --------------------------------- |
| 1     | Validar modelo no SRC_SCHEMA      |
| 2     | Grants DBMS_CLOUD / DBMS_CLOUD_AI |
| 3     | ENABLE_DATA_ACCESS (opcional)     |
| 4     | GRANT SELECT MINING MODEL         |
| 5     | Usar nome qualificado (sem alias) |
| 6     | Criar credential                  |
| 7     | Criar profile                     |
| 8     | Ativar profile                    |
| 9     | Testar uso                        |

---

## ⚠️ Observações importantes

* O privilégio correto é **SELECT MINING MODEL**
* `CREATE MINING MODEL` só é necessário para criação de modelos
* Sempre usar **nome qualificado (schema.model)** em cenários cross-schema
* `SELECT ANY MINING MODEL` deve ser evitado em produção (princípio do menor privilégio)

---
