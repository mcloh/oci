# Document Embedding Service

Serviço web para upload de documentos (Word, PDF, imagens escaneadas), geração de chunks de texto e embeddings, com armazenamento no Oracle Autonomous Database (ADW 23AI).

## Características

- **Autenticação OCI**: Suporte completo para OCI Signer com configuração via arquivo
- **Autenticação HTTP Dual**: Suporte para `X-API-Key` header e `Authorization: Bearer` token
- **Processamento de Documentos**: 
  - PDF (texto nativo)
  - Word (.docx)
  - Imagens escaneadas (OCR via Tesseract)
- **Chunking Inteligente**: Divisão de texto em chunks com sobreposição configurável
- **Embeddings**: Geração de vetores usando Sentence Transformers
- **Banco de Dados ADW 23AI**: Armazenamento estruturado com criação automática de tabelas
- **API RESTful**: Endpoints para upload, consulta e busca semântica

## Arquitetura

```
doc-embedding-service/
├── app.py                 # Aplicação Flask principal
├── auth.py                # Módulo de autenticação OCI e HTTP
├── document_processor.py  # Processamento de documentos e chunking
├── embedding_service.py   # Geração de embeddings
├── database.py            # Integração com ADW 23AI
├── config/
│   └── credentials.conf   # Configuração OCI
├── uploads/               # Diretório temporário para uploads
├── logs/                  # Logs da aplicação
├── requirements.txt       # Dependências Python
└── .env                   # Variáveis de ambiente
```

## Instalação

### 1. Instalar dependências do sistema

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils

# Para Oracle Instant Client (necessário para oracledb)
# Baixe e instale de: https://www.oracle.com/database/technologies/instant-client/downloads.html
```

### 2. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 3. Configurar credenciais OCI

```bash
cp config/credentials.conf.example config/credentials.conf
# Edite config/credentials.conf com suas credenciais OCI
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas configurações
```

## Configuração

### Variáveis de Ambiente

- **API_KEY**: Chave de API para autenticação HTTP
- **DB_USER**: Usuário do banco de dados
- **DB_PASSWORD**: Senha do banco de dados
- **DB_DSN**: DSN de conexão (formato: `(description=...`)
- **EMBEDDING_MODEL**: Modelo de embedding (padrão: `sentence-transformers/all-MiniLM-L6-v2`)
- **CHUNK_SIZE**: Tamanho dos chunks em caracteres (padrão: 500)
- **CHUNK_OVERLAP**: Sobreposição entre chunks (padrão: 50)

### Estrutura do Banco de Dados

O serviço cria automaticamente as seguintes tabelas no ADW 23AI:

#### Tabela `DOCUMENTS`
```sql
CREATE TABLE DOCUMENTS (
    id VARCHAR2(36) PRIMARY KEY,
    filename VARCHAR2(500) NOT NULL,
    file_type VARCHAR2(50) NOT NULL,
    file_size NUMBER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR2(64),
    metadata CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Tabela `DOCUMENT_CHUNKS`
```sql
CREATE TABLE DOCUMENT_CHUNKS (
    id VARCHAR2(36) PRIMARY KEY,
    document_id VARCHAR2(36) NOT NULL,
    chunk_index NUMBER NOT NULL,
    chunk_text CLOB NOT NULL,
    chunk_size NUMBER NOT NULL,
    embedding VECTOR(384, FLOAT32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES DOCUMENTS(id) ON DELETE CASCADE
)
```

## Uso

### Iniciar o serviço

```bash
python app.py
```

O serviço estará disponível em `http://localhost:8000`

### Endpoints da API

#### 1. Health Check
```bash
GET /
```

Resposta:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "document-embedding-service"
}
```

#### 2. Upload de Documento
```bash
POST /api/v1/documents/upload
Headers:
  X-API-Key: your-api-key
  # ou
  Authorization: Bearer your-api-key
Body (multipart/form-data):
  file: <arquivo>
  metadata: {"description": "Documento de exemplo"} (opcional)
```

Resposta:
```json
{
  "document_id": "uuid-do-documento",
  "filename": "exemplo.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "chunks_created": 15,
  "processing_time": 2.5
}
```

#### 3. Listar Documentos
```bash
GET /api/v1/documents
Headers:
  X-API-Key: your-api-key
```

Resposta:
```json
{
  "documents": [
    {
      "id": "uuid-1",
      "filename": "documento1.pdf",
      "file_type": "application/pdf",
      "upload_date": "2024-12-04T10:30:00",
      "chunks_count": 15
    }
  ],
  "total": 1
}
```

#### 4. Buscar Documento por ID
```bash
GET /api/v1/documents/{document_id}
Headers:
  X-API-Key: your-api-key
```

#### 5. Busca Semântica
```bash
POST /api/v1/search
Headers:
  X-API-Key: your-api-key
Body:
{
  "query": "texto de busca",
  "top_k": 5,
  "threshold": 0.7
}
```

Resposta:
```json
{
  "results": [
    {
      "document_id": "uuid-1",
      "chunk_id": "chunk-uuid-1",
      "chunk_text": "Texto do chunk...",
      "similarity": 0.92,
      "document_filename": "documento1.pdf"
    }
  ],
  "query": "texto de busca",
  "total_results": 5
}
```

#### 6. Deletar Documento
```bash
DELETE /api/v1/documents/{document_id}
Headers:
  X-API-Key: your-api-key
```

## Autenticação

O serviço suporta dois métodos de autenticação HTTP:

1. **X-API-Key Header**:
   ```bash
   curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/documents
   ```

2. **Authorization Bearer Token**:
   ```bash
   curl -H "Authorization: Bearer your-api-key" http://localhost:8000/api/v1/documents
   ```

## Formatos Suportados

- **PDF**: Extração de texto nativo
- **Word (.docx)**: Extração de texto de documentos Word
- **Imagens** (PNG, JPG, TIFF): OCR via Tesseract para documentos escaneados

## Desenvolvimento

### Estrutura de Módulos

- **auth.py**: Gerenciamento de autenticação OCI e validação de API keys
- **document_processor.py**: Extração de texto e chunking de documentos
- **embedding_service.py**: Geração de embeddings vetoriais
- **database.py**: Operações de banco de dados e gerenciamento de schema
- **app.py**: Aplicação Flask e definição de rotas

### Modo de Teste

Para executar em modo de teste (sem OCI):
```bash
export TEST_MODE=true
python app.py
```

## Segurança

- Autenticação obrigatória em todos os endpoints (exceto health check)
- Comparação de API keys usando `hmac.compare_digest` para prevenir timing attacks
- Validação de tipos de arquivo no upload
- Limite de tamanho de arquivo configurável
- Sanitização de nomes de arquivo

## Logs

Logs são armazenados em `logs/app.log` com rotação automática.

## Licença

Proprietário - Uso interno apenas

## Suporte

Para questões e suporte, entre em contato com a equipe de desenvolvimento.
