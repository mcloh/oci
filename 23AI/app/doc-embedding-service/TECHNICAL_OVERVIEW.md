# Document Embedding Service - Visão Técnica

## Arquitetura

### Visão Geral

O **Document Embedding Service** é uma aplicação web RESTful desenvolvida em Python que implementa um pipeline completo de processamento de documentos para sistemas de **Retrieval-Augmented Generation (RAG)**. A aplicação processa documentos em múltiplos formatos, extrai texto, divide em chunks semânticos, gera embeddings vetoriais e armazena tudo em um banco de dados Oracle Autonomous Database (ADW) 23AI com suporte nativo a vetores.

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Web Server                        │
│                    (app.py - Port 8000)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐   ┌──────────────┐
│ Auth Module  │    │ Document         │   │  Embedding   │
│  (auth.py)   │    │  Processor       │   │   Service    │
│              │    │ (document_       │   │ (embedding_  │
│ - OCI Signer │    │  processor.py)   │   │  service.py) │
│ - HTTP Auth  │    │                  │   │              │
│   (API Key)  │    │ - PDF Extract    │   │ - Sentence   │
│              │    │ - Word Extract   │   │   Transform. │
│              │    │ - OCR (Tess.)    │   │ - Batch      │
│              │    │ - Chunking       │   │   Encoding   │
└──────────────┘    └──────────────────┘   └──────────────┘
                              │                     │
                              └──────────┬──────────┘
                                         ▼
                              ┌──────────────────┐
                              │  Database Layer  │
                              │  (database.py)   │
                              │                  │
                              │ - Connection Mgr │
                              │ - Schema Init    │
                              │ - CRUD Ops       │
                              │ - Vector Search  │
                              └──────────────────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │  Oracle ADW 23AI │
                              │                  │
                              │ - DOCUMENTS      │
                              │ - DOCUMENT_CHUNKS│
                              │ - Vector Index   │
                              └──────────────────┘
```

## Módulos Detalhados

### 1. auth.py - Módulo de Autenticação

**Responsabilidades:**
- Gerenciar autenticação OCI via Signer
- Validar credenciais HTTP (X-API-Key e Bearer Token)
- Carregar configuração de arquivo externo
- Suportar modo de teste (sem OCI real)

**Classes:**
- `OCIAuthManager`: Gerencia autenticação OCI
- `HTTPAuthManager`: Gerencia autenticação HTTP

**Padrões de Segurança:**
- Comparação de strings usando `hmac.compare_digest` (timing-attack safe)
- Suporte a múltiplos métodos de autenticação HTTP
- Modo debug configurável para troubleshooting

**Exemplo de Uso:**
```python
from auth import initialize_auth

oci_auth, http_auth = initialize_auth(
    config_file="/path/to/credentials.conf",
    api_key="your-api-key",
    test_mode=False
)

# Middleware Flask
@app.before_request
def authenticate():
    http_auth.check_api_key()
```

### 2. document_processor.py - Processamento de Documentos

**Responsabilidades:**
- Extrair texto de PDF (nativo e escaneado)
- Extrair texto de Word (.docx)
- Realizar OCR em imagens
- Dividir texto em chunks com sobreposição
- Calcular hash de conteúdo

**Formatos Suportados:**
- **PDF**: PyPDF2 para texto nativo, pdf2image + Tesseract para escaneados
- **Word**: python-docx para .docx
- **Imagens**: PIL + Tesseract OCR (PNG, JPG, TIFF)

**Algoritmo de Chunking:**
1. Define tamanho do chunk (padrão: 500 caracteres)
2. Define sobreposição (padrão: 50 caracteres)
3. Tenta quebrar em limites naturais (ponto, nova linha, espaço)
4. Mantém contexto entre chunks via sobreposição

**Configuração:**
```python
processor = DocumentProcessor(
    chunk_size=500,      # Tamanho do chunk
    chunk_overlap=50     # Sobreposição
)

result = processor.process_document(
    content=file_bytes,
    filename="document.pdf",
    mime_type="application/pdf"
)
# result = {
#     'text': "...",
#     'chunks': [...],
#     'content_hash': "sha256...",
#     'text_length': 12345,
#     'chunks_count': 25
# }
```

### 3. embedding_service.py - Geração de Embeddings

**Responsabilidades:**
- Carregar modelo Sentence Transformers
- Gerar embeddings para texto único ou batch
- Calcular similaridade de cosseno
- Buscar embeddings similares

**Modelo Padrão:**
- `sentence-transformers/all-MiniLM-L6-v2`
- Dimensão: 384
- Multilíngue (suporta português e inglês)
- Rápido e eficiente

**Modelos Alternativos:**
```python
# Modelo maior e mais preciso
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # 768 dim

# Modelo multilíngue otimizado
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2  # 384 dim

# Modelo específico para português
EMBEDDING_MODEL=neuralmind/bert-base-portuguese-cased  # 768 dim
```

**Performance:**
- Batch processing para eficiência
- Normalização automática de vetores
- Cache de modelo em memória

**Exemplo de Uso:**
```python
from embedding_service import EmbeddingService

service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Encoding único
embedding = service.encode_text("Este é um texto de exemplo")

# Encoding batch
embeddings = service.encode_batch(["texto 1", "texto 2", "texto 3"])

# Busca similar
results = service.find_similar(query_embedding, all_embeddings, top_k=5)
```

### 4. database.py - Camada de Banco de Dados

**Responsabilidades:**
- Gerenciar conexão com ADW 23AI
- Criar schema automaticamente
- Operações CRUD para documentos e chunks
- Busca vetorial usando índice nativo

**Schema do Banco de Dados:**

#### Tabela DOCUMENTS
```sql
CREATE TABLE DOCUMENTS (
    id VARCHAR2(36) PRIMARY KEY,           -- UUID
    filename VARCHAR2(500) NOT NULL,       -- Nome do arquivo
    file_type VARCHAR2(50) NOT NULL,       -- MIME type
    file_size NUMBER NOT NULL,             -- Tamanho em bytes
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR2(64),             -- SHA-256
    metadata CLOB,                         -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Tabela DOCUMENT_CHUNKS
```sql
CREATE TABLE DOCUMENT_CHUNKS (
    id VARCHAR2(36) PRIMARY KEY,           -- UUID
    document_id VARCHAR2(36) NOT NULL,     -- FK para DOCUMENTS
    chunk_index NUMBER NOT NULL,           -- Índice do chunk
    chunk_text CLOB NOT NULL,              -- Texto do chunk
    chunk_size NUMBER NOT NULL,            -- Tamanho do chunk
    embedding VECTOR(384, FLOAT32),        -- Vetor de embedding
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_document FOREIGN KEY (document_id) 
        REFERENCES DOCUMENTS(id) ON DELETE CASCADE
)
```

#### Índices
```sql
-- Índice para busca por documento
CREATE INDEX idx_chunks_document ON DOCUMENT_CHUNKS(document_id);

-- Índice vetorial para busca semântica (Oracle 23AI)
CREATE VECTOR INDEX idx_chunks_embedding 
    ON DOCUMENT_CHUNKS(embedding) 
    ORGANIZATION NEIGHBOR PARTITIONS
    WITH DISTANCE COSINE;
```

**Busca Vetorial:**
```sql
-- Busca usando VECTOR_DISTANCE
SELECT c.id, c.chunk_text, d.filename,
       VECTOR_DISTANCE(c.embedding, TO_VECTOR(:query_embedding), COSINE) as distance
FROM DOCUMENT_CHUNKS c
JOIN DOCUMENTS d ON c.document_id = d.id
ORDER BY distance
FETCH FIRST :top_k ROWS ONLY
```

**Tipo VECTOR do Oracle 23AI:**
- Suporte nativo a vetores de alta dimensão
- Índices otimizados para busca de vizinhos mais próximos
- Funções de distância: COSINE, EUCLIDEAN, DOT
- Performance superior a soluções baseadas em BLOB

### 5. app.py - Aplicação Flask

**Endpoints:**

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/` ou `/health` | Health check | Não |
| POST | `/api/v1/documents/upload` | Upload de documento | Sim |
| GET | `/api/v1/documents` | Lista documentos | Sim |
| GET | `/api/v1/documents/{id}` | Busca documento | Sim |
| DELETE | `/api/v1/documents/{id}` | Deleta documento | Sim |
| POST | `/api/v1/search` | Busca semântica | Sim |
| GET | `/api/v1/stats` | Estatísticas | Sim |

**Fluxo de Upload:**
```
1. Cliente → POST /api/v1/documents/upload
2. Validação de autenticação (HTTP Auth)
3. Validação de arquivo (tipo, tamanho)
4. Extração de texto (DocumentProcessor)
5. Chunking (DocumentProcessor)
6. Geração de embeddings (EmbeddingService)
7. Inserção no banco (DatabaseManager)
   - INSERT INTO DOCUMENTS
   - INSERT INTO DOCUMENT_CHUNKS (batch)
8. Resposta com document_id e estatísticas
```

**Fluxo de Busca:**
```
1. Cliente → POST /api/v1/search {"query": "..."}
2. Validação de autenticação
3. Geração de embedding da query (EmbeddingService)
4. Busca vetorial no banco (VECTOR_DISTANCE)
5. Filtragem por threshold
6. Ordenação por similaridade
7. Resposta com top_k resultados
```

## Padrões de Design

### 1. Factory Pattern
```python
# Criação de instâncias via factory functions
processor = create_document_processor(chunk_size=500)
embedding_service = create_embedding_service(model_name="...")
```

### 2. Singleton Pattern
```python
# Instâncias globais para serviços compartilhados
_embedding_service = None

def get_embedding_service():
    return _embedding_service
```

### 3. Dependency Injection
```python
# Inicialização de dependências no startup
def initialize_services():
    oci_auth, http_auth = initialize_auth(...)
    embedding_service = initialize_embedding_service(...)
    db = initialize_database(...)
```

### 4. Middleware Pattern
```python
# Autenticação como middleware Flask
@app.before_request
def before_all_requests():
    if request.method == "OPTIONS":
        return "", 204
    http_auth.check_api_key()
```

## Configuração e Variáveis de Ambiente

### Arquivo .env
```bash
# Segurança
API_KEY=your-secure-api-key

# OCI
OCI_CONFIG_FILE=/path/to/credentials.conf
OCI_REGION=us-chicago-1
TEST_MODE=false

# Banco de Dados
DB_USER=ADMIN
DB_PASSWORD=password
DB_DSN=(description=...)

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Aplicação
UPLOAD_FOLDER=/app/uploads
MAX_UPLOAD_SIZE=52428800  # 50MB
PORT=8000
```

### Arquivo credentials.conf (OCI)
```ini
tenancy=ocid1.tenancy.oc1..aaa...
user=ocid1.user.oc1..aaa...
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
key_file=/path/to/oci_api_key.pem
pass_phrase=
region=us-chicago-1
test_mode=false
```

## Performance e Otimização

### Chunking
- **Trade-off**: Chunks menores = maior precisão, mais chunks, mais storage
- **Recomendação**: 500 caracteres com 50 de overlap para documentos técnicos
- **Ajuste**: Aumentar para 1000+ em documentos narrativos

### Embeddings
- **Batch Processing**: Processa múltiplos chunks de uma vez
- **GPU Support**: Configure `EMBEDDING_DEVICE=cuda` se disponível
- **Modelo**: MiniLM-L6 é rápido; use MPNet para maior qualidade

### Banco de Dados
- **Vector Index**: Essencial para performance em grandes volumes
- **Connection Pool**: Considere usar pool de conexões em produção
- **Batch Insert**: Chunks são inseridos em batch para eficiência

### Escalabilidade
- **Horizontal**: Múltiplas instâncias com load balancer
- **Vertical**: Aumentar CPU/RAM para processamento mais rápido
- **Storage**: Object Storage para arquivos originais (não implementado)

## Segurança

### Autenticação
- Dual HTTP auth (X-API-Key e Bearer)
- OCI Signer para serviços Oracle
- Timing-attack safe string comparison

### Validação
- Tipo de arquivo (whitelist)
- Tamanho de arquivo (configurável)
- Sanitização de filename

### Dados Sensíveis
- Credenciais em variáveis de ambiente
- Chaves privadas fora do repositório
- Secrets management recomendado (OCI Vault)

## Monitoramento e Logging

### Logs
```python
print(f"[module] Message")  # Formato padrão
```

### Métricas
- Tempo de processamento por documento
- Número de chunks gerados
- Taxa de sucesso/erro
- Estatísticas via `/api/v1/stats`

### Health Check
```bash
curl http://localhost:8000/health
```

## Testes

### Teste Manual
```bash
python test_service.py
```

### Teste com curl
```bash
./examples/curl_examples.sh
```

### Teste Unitário (Recomendado para produção)
```python
# Adicionar pytest e testes unitários
pytest tests/
```

## Limitações Conhecidas

1. **Armazenamento**: Arquivos originais não são persistidos (apenas texto extraído)
2. **OCR**: Qualidade depende da resolução da imagem
3. **Idiomas**: OCR configurado para português e inglês
4. **Concorrência**: Não há lock de documentos duplicados
5. **Rate Limiting**: Não implementado (adicionar se necessário)

## Roadmap Futuro

1. **Object Storage**: Armazenar arquivos originais no OCI Object Storage
2. **Async Processing**: Usar Celery para processamento assíncrono
3. **Webhooks**: Notificações de conclusão de processamento
4. **Versioning**: Suporte a múltiplas versões de documentos
5. **Multi-tenancy**: Isolamento por tenant/usuário
6. **Advanced Search**: Filtros por metadata, data, tipo
7. **Reranking**: Reranking de resultados com modelo cross-encoder
8. **Caching**: Cache de embeddings frequentes

## Referências

- [Oracle Autonomous Database 23AI - Vector Search](https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/)
- [Sentence Transformers](https://www.sbert.net/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
