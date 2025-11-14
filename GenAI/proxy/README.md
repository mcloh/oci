# OCI GenAI Proxy API

Proxy compatível com OpenAI v1 para modelos e agents da Oracle Cloud Infrastructure (OCI) GenAI.

---

## 🚀 Início Rápido

### **1. Configurar Modelos**

Edite `llm_models.json`:

```json
{
  "gpt5": {
    "id": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaa...",
    "region": "us-chicago-1",
    "compartmentId": "ocid1.compartment.oc1..aaaaaa...",
    "type": "model"
  },
  "my-agent": {
    "id": "ocid1.generativeaiagentendpoint.oc1.us-chicago-1.amaaa...",
    "region": "us-chicago-1",
    "compartmentId": "ocid1.compartment.oc1..aaaaaa...",
    "type": "agent"
  }
}
```

### **2. Configurar Credenciais OCI**

Edite `credentials.conf`:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaa...
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
tenancy=ocid1.tenancy.oc1..aaaaaa...
region=us-chicago-1
key_file=/path/to/oci_api_key.pem
```

### **3. Iniciar API**

```bash
python3.11 app.py
```

API disponível em: `http://localhost:8000`

---

## 📋 Endpoints Disponíveis

### **Compatíveis com OpenAI v1:**
- `POST /genai/{model}/v1/chat/completions` - Chat completion
- `POST /genai/{model}/v1/completions` - Text completion
- `GET /genai/{model}/v1/models` - Informações do modelo
- `POST /genai/{model}/v1/embeddings` - Embeddings (Cohere)

### **Diretos OCI:**
- `POST /genai/{model}/session` - Criar sessão (agents)
- `POST /genai/{model}/chat` - Chat com agent
- `POST /genai/{model}/inference` - Inferência direta (models)

---

## 💬 Exemplos de Uso

### **1. Chat com Model (OpenAI v1)**

```python
import requests

response = requests.post(
    "http://localhost:8000/genai/gpt5/v1/chat/completions",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "messages": [
            {"role": "user", "content": "Explique computação quântica"}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
)

data = response.json()
print(data["choices"][0]["message"]["content"])
print(f"Tokens: {data['usage']['total_tokens']}")
```

---

### **2. Chat com Agent (Modo Automático)** ⭐

```python
import requests

# Primeira mensagem
response = requests.post(
    "http://localhost:8000/genai/my-agent/chat",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "channel": "web-app",
        "cuid": "user-12345",
        "userMessage": "Olá, preciso de ajuda"
    }
)

data = response.json()
print(data["agentResponse"]["content"][0]["text"])
print(f"Sessão: {data['sessionInfo']['sessionId']}")
print(f"Reutilizada: {data['sessionInfo']['reused']}")

# Segunda mensagem (mesma sessão - automático!)
response2 = requests.post(
    "http://localhost:8000/genai/my-agent/chat",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "channel": "web-app",
        "cuid": "user-12345",
        "userMessage": "Qual é o status do pedido #12345?"
    }
)

data2 = response2.json()
print(data2["agentResponse"]["content"][0]["text"])
print(f"Reutilizada: {data2['sessionInfo']['reused']}")  # True
```

**Benefícios:**
- ✅ Gerenciamento automático de sessão
- ✅ Retry automático em erro 409
- ✅ Cache local com TTL de 2h

---

### **3. Chat com Agent (Modo Manual)**

```python
import requests

# Passo 1: Criar sessão
session_resp = requests.post(
    "http://localhost:8000/genai/my-agent/session",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "channel": "web-app",
        "cuid": "user-12345"
    }
)

session_id = session_resp.json()["id"]

# Passo 2: Enviar mensagem
chat_resp = requests.post(
    "http://localhost:8000/genai/my-agent/chat",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "sessionId": session_id,
        "userMessage": "Olá"
    }
)

response = chat_resp.json()["agentResponse"]["content"][0]["text"]
print(response)
```

---

### **4. Inferência Direta (OCI)**

```python
import requests

response = requests.post(
    "http://localhost:8000/genai/gpt5/inference",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "prompt": "Traduza para inglês: Olá, mundo!",
        "temperature": 0.3,
        "max_tokens": 100
    }
)

data = response.json()
print(data["response"]["text"])
print(data["response"]["finish_reason"])
```

---

### **5. Streaming**

```python
import requests

response = requests.post(
    "http://localhost:8000/genai/gpt5/v1/chat/completions",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "messages": [{"role": "user", "content": "Conte uma história"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

---

### **6. Embeddings**

```python
import requests

response = requests.post(
    "http://localhost:8000/genai/gpt5/v1/embeddings",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "input": "Texto para gerar embedding",
        "model": "cohere.embed-multilingual-v3.0"
    }
)

data = response.json()
embedding = data["data"][0]["embedding"]
print(f"Dimensões: {len(embedding)}")
```

---

## 🔑 Autenticação

Configure `API_KEY` no código ou use variável de ambiente:

```bash
export API_KEY="your-secret-key"
python3.11 app.py
```

Envie em todas as requisições:

```bash
# Opção 1: Header Authorization
Authorization: Bearer YOUR_API_KEY

# Opção 2: Header X-API-Key
X-API-Key: YOUR_API_KEY
```

---

## 📊 Parâmetros Comuns

### **Chat Completions:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `messages` | array | Lista de mensagens (role + content) |
| `temperature` | float | Aleatoriedade (0.0 a 2.0) |
| `max_tokens` | integer | Máximo de tokens na resposta |
| `top_p` | float | Nucleus sampling |
| `stream` | boolean | Streaming (Server-Sent Events) |

### **Chat com Agent (Modo Automático):**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `channel` | string | ✅ | Canal (ex: `web-app`, `mobile-app`) |
| `cuid` | string | ✅ | Customer User ID |
| `userMessage` | string | ✅ | Mensagem do usuário |

### **Inferência Direta:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `prompt` | string | Texto de entrada |
| `temperature` | float | Aleatoriedade (0.0 a 2.0) |
| `max_tokens` | integer | Máximo de tokens |
| `top_p` | float | Nucleus sampling |
| `top_k` | integer | Top-k sampling |

---

## 🛠️ Configuração Avançada

### **Modo de Teste**

```bash
export TEST_MODE=true
python3.11 app.py
```

Retorna respostas simuladas sem chamar OCI.

### **Porta Customizada**

```bash
python3.11 app.py --port 9000
```

### **CORS**

CORS habilitado por padrão para `*`. Edite `app.py` para restringir.

---

## 📝 Estrutura de Resposta

### **Chat Completion (OpenAI v1):**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699999999,
  "model": "gpt5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Resposta do modelo..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 120,
    "total_tokens": 135
  }
}
```

### **Chat com Agent (Modo Automático):**

```json
{
  "agentResponse": {
    "role": "ASSISTANT",
    "content": [
      {
        "text": "Resposta do agent..."
      }
    ],
    "timeCreated": "2024-11-14T10:05:00.000Z"
  },
  "sessionInfo": {
    "sessionId": "ocid1.generativeaiagentsession.oc1.us-chicago-1.amaaa...",
    "sessionKey": "web-app:user-12345",
    "reused": true
  }
}
```

### **Inferência Direta:**

```json
{
  "response": {
    "text": "Resposta do modelo...",
    "finish_reason": "STOP"
  }
}
```

---

## ⚠️ Erros Comuns

### **1. Modelo não encontrado**

```json
{"error": "Modelo 'xxx' não encontrado no arquivo de configuração"}
```

**Solução:** Adicione o modelo em `llm_models.json`.

---

### **2. Tipo incorreto**

```json
{"error": "Modelo 'gpt5' não é um agent. Use type='agent' no JSON."}
```

**Solução:** Verifique o campo `type` no `llm_models.json`.

---

### **3. Sessão expirada (modo manual)**

```json
{
  "error": "Sessão inválida ou expirada",
  "suggestion": "Use modo automático com 'channel' e 'cuid'"
}
```

**Solução:** Use modo automático ou crie nova sessão.

---

### **4. Autenticação inválida**

```json
{"error": "API Key inválida"}
```

**Solução:** Verifique header `Authorization` ou `X-API-Key`.

---

## 🔄 Comparação: Models vs Agents

| Aspecto | Models | Agents |
|---------|--------|--------|
| **Endpoint OpenAI** | `/v1/chat/completions` | `/v1/chat/completions` |
| **Endpoint OCI** | `/inference` | `/chat` |
| **Sessão** | Não | Sim (gerenciada automaticamente) |
| **Token usage** | ✅ Sim | ❌ Não |
| **Contexto** | Stateless | Mantido na sessão |
| **Streaming** | ✅ Sim | ✅ Sim |

---

## 📚 Documentação Completa

Para documentação detalhada, consulte:
- `CHAT_FUSIONADO_v2.0.4.md` - Endpoint /chat com gerenciamento automático
- `ENDPOINTS_OCI_DIRETOS.md` - Endpoints diretos OCI
- `EXPLICACAO_CHAMADAS_OCI.md` - Detalhes técnicos internos
- `CHANGELOG.md` - Histórico de versões

---

## 🎯 Resumo Rápido

### **Para Models:**
```python
# OpenAI v1 (recomendado)
POST /genai/{model}/v1/chat/completions
Body: {"messages": [...]}

# OCI direto
POST /genai/{model}/inference
Body: {"prompt": "..."}
```

### **Para Agents:**
```python
# Modo automático (recomendado)
POST /genai/{agent}/chat
Body: {"channel": "...", "cuid": "...", "userMessage": "..."}

# Modo manual
POST /genai/{agent}/session  # Criar sessão
POST /genai/{agent}/chat      # Enviar mensagem
Body: {"sessionId": "...", "userMessage": "..."}
```

---

## 📦 Versão

**v2.0.3** - Novembro 2024

**Funcionalidades:**
- ✅ Compatibilidade OpenAI v1
- ✅ Endpoints diretos OCI
- ✅ Gerenciamento automático de sessão (agents)
- ✅ Retry automático de erro 409
- ✅ Streaming
- ✅ Token usage
- ✅ Embeddings (Cohere)
- ✅ Upload de arquivos

---

## 🚀 Suporte

Para dúvidas ou problemas, consulte a documentação completa ou abra uma issue no repositório.
