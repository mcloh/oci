# Sistema MCP com AI Agent - Calculadora Inteligente

Este projeto implementa um **servidor MCP (Model Context Protocol)** e um **cliente MCP** em Python que utiliza um LLM para interpretar operações matemáticas solicitadas pelo usuário em linguagem natural e executá-las através de tool calls.

## 📋 Visão Geral

O sistema é composto por três componentes principais:

1. **Servidor MCP** (`mcp_server.py`): Expõe 4 ferramentas matemáticas (soma, subtração, multiplicação e divisão) através do protocolo MCP
2. **Cliente MCP** (`mcp_client.py`): Interface de chat que conecta o usuário ao LLM e ao servidor MCP
3. **Script de Teste** (`test_system.py`): Testa automaticamente todas as operações e casos de erro

## 🎯 Funcionalidades Principais

### ✨ Interpretação Inteligente de Operações

O agente **interpreta automaticamente** qual operação matemática o usuário deseja realizar através de linguagem natural:

- **"Quanto é 15 mais 7?"** → Executa soma
- **"Subtraia 5 de 20"** → Executa subtração
- **"Multiplique 8 por 6"** → Executa multiplicação
- **"Divida 100 por 4"** → Executa divisão
- **"Eu tenho 25 maçãs e ganhei mais 13"** → Interpreta como soma e calcula

### 🛡️ Tratamento Robusto de Erros

- **Divisão por zero**: Detectada e tratada com mensagem educada
- **Operações não implementadas**: Informa que apenas as 4 operações básicas estão disponíveis
- **Validação de tipos**: Garante que os números sejam inteiros
- **Parâmetros faltantes**: Verifica se ambos os números foram fornecidos

### 🧮 4 Operações Matemáticas

1. **Soma** (`soma`): Adição de dois números inteiros
2. **Subtração** (`subtracao`): Subtração de dois números inteiros
3. **Multiplicação** (`multiplicacao`): Multiplicação de dois números inteiros
4. **Divisão** (`divisao`): Divisão de dois números (retorna float)

## 🏗️ Arquitetura

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│   Usuário   │ ◄─────► │  Cliente MCP     │ ◄─────► │ Servidor MCP │
│             │  Chat   │  + LLM           │  stdio  │  (4 Tools)   │
│             │         │  (Interpretação) │         │              │
└─────────────┘         └──────────────────┘         └──────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │  LLM API     │
                        │ (Grok Code)  │
                        └──────────────┘
```

### Fluxo de Execução

1. **Usuário** envia mensagem em linguagem natural (ex: "Quanto é 15 mais 7?")
2. **Cliente MCP** envia mensagem para o LLM
3. **LLM** interpreta a operação desejada e identifica os números
4. **LLM** faz tool call para a ferramenta apropriada (ex: `soma`)
5. **Cliente MCP** executa a ferramenta no **Servidor MCP**
6. **Servidor MCP** valida parâmetros e retorna resultado ou erro
7. **Cliente MCP** envia resultado de volta ao LLM
8. **LLM** gera resposta generativa e amigável
9. **Usuário** recebe resposta final

## 🔧 Tecnologias Utilizadas

- **Python 3.11**: Linguagem de programação
- **MCP (Model Context Protocol)**: Protocolo para comunicação entre cliente e servidor
- **OpenAI SDK**: Cliente para comunicação com LLM compatível com API OpenAI
- **LLM**: Grok Code via API compatível com OpenAI
- **asyncio**: Programação assíncrona

## 📦 Estrutura do Projeto

```
mcp_project/
├── venv/                  # Ambiente virtual Python
├── mcp_server.py          # Servidor MCP com 4 ferramentas matemáticas
├── mcp_client.py          # Cliente MCP com interpretação inteligente
├── test_system.py         # Script de teste automatizado completo
├── requirements.txt       # Dependências do projeto
├── run.sh                 # Script de inicialização rápida
├── README.md              # Esta documentação
└── QUICKSTART.md          # Guia rápido de início
```

## 🚀 Instalação

### 1. Criar Ambiente Virtual

```bash
cd mcp_project
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

## 💻 Uso

### Modo Interativo (Chat com Usuário)

Execute o cliente MCP para iniciar uma sessão de chat interativa:

```bash
source venv/bin/activate
python mcp_client.py
```

Ou use o script de inicialização rápida:

```bash
./run.sh
```

### Exemplos de Interação

#### Exemplo 1: Soma em Linguagem Natural

```
👤 Você: Eu tenho 25 maçãs e ganhei mais 13, quantas tenho agora?

🔧 Executando ferramenta: soma
   Argumentos: {'numero1': 25, 'numero2': 13}
   ✓ Resultado: 38

🤖 Assistente: Você tinha 25 maçãs e ganhou mais 13, então agora tem 38 maçãs no total!
```

#### Exemplo 2: Divisão

```
👤 Você: Divida 100 por 4

🔧 Executando ferramenta: divisao
   Argumentos: {'numero1': 100, 'numero2': 4}
   ✓ Resultado: 25.0

🤖 Assistente: 100 dividido por 4 é igual a 25!
```

#### Exemplo 3: Erro - Divisão por Zero

```
👤 Você: Divida 10 por 0

🔧 Executando ferramenta: divisao
   Argumentos: {'numero1': 10, 'numero2': 0}
   ⚠️  Erro: Divisão por zero não é permitida

🤖 Assistente: Dividir 10 por 0 é uma operação matematicamente indefinida. 
Não posso fazer isso. Mas posso ajudar com outras contas válidas!
```

#### Exemplo 4: Operação Não Implementada

```
👤 Você: Calcule 5 elevado ao quadrado

🤖 Assistente: Desculpe, mas eu só consigo fazer as operações básicas: 
soma, subtração, multiplicação e divisão. Potências não estão disponíveis. 
Se quiser fazer 5 vezes 5, posso ajudar!
```

### Modo Teste Automatizado

Execute o script de teste para validar todas as operações:

```bash
source venv/bin/activate
python test_system.py
```

O teste valida:
- ✅ Soma
- ✅ Subtração
- ✅ Multiplicação
- ✅ Divisão
- ✅ Tratamento de erro (divisão por zero)
- ✅ Operação não implementada
- ✅ Interpretação de linguagem natural

## 📝 Componentes Detalhados

### 1. Servidor MCP (`mcp_server.py`)

O servidor MCP expõe quatro ferramentas matemáticas com validação completa:

#### Ferramenta: `soma`

Realiza a soma de dois números inteiros.

**Parâmetros:**
- `numero1` (integer): Primeiro número
- `numero2` (integer): Segundo número

**Retorno de Sucesso:**
```json
{
  "operacao": "soma",
  "numero1": 15,
  "numero2": 7,
  "resultado": 22,
  "expressao": "15 + 7 = 22"
}
```

#### Ferramenta: `subtracao`

Realiza a subtração de dois números inteiros (numero1 - numero2).

**Parâmetros:**
- `numero1` (integer): Minuendo
- `numero2` (integer): Subtraendo

**Retorno de Sucesso:**
```json
{
  "operacao": "subtracao",
  "numero1": 20,
  "numero2": 5,
  "resultado": 15,
  "expressao": "20 - 5 = 15"
}
```

#### Ferramenta: `multiplicacao`

Realiza a multiplicação de dois números inteiros.

**Parâmetros:**
- `numero1` (integer): Primeiro número
- `numero2` (integer): Segundo número

**Retorno de Sucesso:**
```json
{
  "operacao": "multiplicacao",
  "numero1": 8,
  "numero2": 6,
  "resultado": 48,
  "expressao": "8 × 6 = 48"
}
```

#### Ferramenta: `divisao`

Realiza a divisão de dois números (numero1 / numero2). Retorna resultado como float.

**Parâmetros:**
- `numero1` (integer): Dividendo
- `numero2` (integer): Divisor

**Retorno de Sucesso:**
```json
{
  "operacao": "divisao",
  "numero1": 100,
  "numero2": 4,
  "resultado": 25.0,
  "resultado_inteiro": 25,
  "resto": 0,
  "expressao": "100 ÷ 4 = 25.0"
}
```

**Retorno de Erro (Divisão por Zero):**
```json
{
  "error": "Divisão por zero não é permitida",
  "operacao": "divisao",
  "numero1": 10,
  "numero2": 0
}
```

#### Tratamento de Operações Não Implementadas

Se uma ferramenta não reconhecida for chamada:

```json
{
  "error": "Operação 'potencia' não está implementada",
  "operacao_solicitada": "potencia",
  "operacoes_disponiveis": ["soma", "subtracao", "multiplicacao", "divisao"],
  "mensagem": "Por favor, utilize uma das operações disponíveis..."
}
```

### 2. Cliente MCP (`mcp_client.py`)

O cliente MCP integra três componentes principais:

#### Conexão com Servidor MCP

Estabelece comunicação via stdio com o servidor MCP e obtém lista de ferramentas disponíveis.

#### Integração com LLM

Utiliza a API do LLM (compatível com OpenAI) para:
- **Interpretar** a operação matemática desejada pelo usuário
- **Identificar** os números na conversa natural
- **Executar** tool calls apropriados
- **Gerar** respostas generativas e amigáveis

**Configuração do LLM:**
- **URL Base**: `https://api.xptoai.com.br/genai/grokcode/v1`
- **Autenticação**: Bearer Token
- **Modelo**: `grok-2-1212`

**Prompt do Sistema:**

O cliente instrui o LLM a:
1. Interpretar qual operação matemática o usuário deseja
2. Identificar os dois números envolvidos
3. Chamar a ferramenta apropriada
4. Apresentar resultados de forma clara
5. Tratar erros educadamente
6. Informar sobre operações não disponíveis

#### Loop de Chat

Mantém histórico de conversação e gerencia o fluxo de mensagens entre usuário, LLM e servidor MCP.

### 3. Script de Teste (`test_system.py`)

Automatiza o teste do sistema com 8 casos de teste:

1. **Soma**: "Quanto é 15 mais 7?"
2. **Subtração**: "Subtraia 5 de 20"
3. **Multiplicação**: "Multiplique 8 por 6"
4. **Divisão**: "Divida 100 por 4"
5. **Divisão por Zero**: "Divida 10 por 0" (erro esperado)
6. **Operação Não Implementada**: "Calcule 5 elevado ao quadrado"
7. **Linguagem Natural - Soma**: "Eu tenho 25 maçãs e ganhei mais 13..."
8. **Linguagem Natural - Subtração**: "Se eu tinha 50 reais e gastei 18..."

## 🔐 Configuração de Segurança

A chave de API está hardcoded no código para fins de demonstração. Em produção, recomenda-se:

1. Usar variáveis de ambiente:
```python
import os
API_KEY = os.getenv("XPTOAI_API_KEY")
```

2. Usar arquivo `.env`:
```bash
echo "XPTOAI_API_KEY=sua_chave_aqui" > .env
```

3. Carregar com `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

## 🧪 Testes

### Teste Manual

1. Execute o cliente: `python mcp_client.py`
2. Digite mensagens em linguagem natural
3. Teste diferentes operações
4. Teste casos de erro (divisão por zero)
5. Teste operações não implementadas

### Teste Automatizado

```bash
python test_system.py
```

Verifica automaticamente:
- ✅ Conexão com servidor MCP
- ✅ Listagem de 4 ferramentas
- ✅ Interpretação de operações
- ✅ Execução de todas as 4 operações
- ✅ Tratamento de divisão por zero
- ✅ Resposta para operações não implementadas
- ✅ Interpretação de linguagem natural

## 🐛 Troubleshooting

### Erro: "Permission denied"

Se encontrar erros de permissão ao instalar pacotes:
```bash
# Use ambiente virtual
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: "Connection refused"

Verifique se o servidor MCP está sendo iniciado corretamente pelo cliente.

### Erro: "API Key invalid"

Verifique se a chave de API está correta em `mcp_client.py`:
```python
API_KEY = "biasb986lk657fsdv6d3543vs5b65s7v373sd321vsdv4sdv34bv3f4hb5f4j6mn546tu"
```

### Erro: "Model not found"

Ajuste o nome do modelo em `mcp_client.py` se necessário:
```python
MODEL_NAME = "grok-2-1212"  # Ajuste conforme disponível na API
```

### Erro: "Divisão por zero"

Este é um erro esperado e tratado pelo sistema. O agente informará que a operação não é permitida.

## 📚 Referências

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

## 🤝 Extensões Futuras

Sugestões para expandir o sistema:

### Novas Operações
- Potenciação
- Raiz quadrada
- Módulo/resto
- Valor absoluto
- Arredondamento

### Melhorias
- Suporte a números decimais (float)
- Histórico de cálculos
- Exportar resultados para arquivo
- Interface gráfica (GUI)
- API REST para integração

### Testes
- Testes unitários com pytest
- Testes de integração
- Testes de carga
- Cobertura de código

## 📄 Licença

Este projeto é fornecido como exemplo educacional.

## ✨ Características Principais

- ✅ **Interpretação Inteligente**: LLM identifica automaticamente a operação desejada
- ✅ **Linguagem Natural**: Entende perguntas contextuais e conversacionais
- ✅ **4 Operações Básicas**: Soma, subtração, multiplicação e divisão
- ✅ **Tratamento de Erros**: Validação completa e mensagens educadas
- ✅ **Operações Não Implementadas**: Informa claramente as limitações
- ✅ **Protocolo MCP**: Comunicação padronizada entre componentes
- ✅ **Assíncrono**: Uso de asyncio para melhor performance
- ✅ **Extensível**: Fácil adicionar novas ferramentas matemáticas
- ✅ **Testável**: Scripts de teste automatizado incluídos

---

**Desenvolvido como demonstração de AI Agent com MCP e interpretação inteligente de operações**
