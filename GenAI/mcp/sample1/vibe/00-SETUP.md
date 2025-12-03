# 00 - Setup Inicial do Projeto

## 🎯 Objetivo

Criar a estrutura inicial do projeto MCP com ambiente virtual Python e preparar o diretório de trabalho.

## 📋 Contexto

Este é o primeiro passo para construir um sistema MCP (Model Context Protocol) com AI Agent que funciona como uma calculadora inteligente. O projeto utilizará Python 3.11, bibliotecas MCP e OpenAI SDK.

## 🔧 Especificações Técnicas

- **Linguagem:** Python 3.11+
- **Estrutura:** Ambiente virtual isolado
- **Diretório:** `mcp_project/`
- **Dependências principais:** mcp, openai

---

## 💬 PROMPT COMPLETO

```
Preciso criar um projeto Python para implementar um sistema MCP (Model Context Protocol) com AI Agent.

REQUISITOS:
1. Criar diretório chamado "mcp_project"
2. Configurar ambiente virtual Python 3.11
3. Preparar estrutura básica de arquivos

ESTRUTURA ESPERADA:
mcp_project/
├── venv/                  # Ambiente virtual (será criado)
├── mcp_server.py          # Servidor MCP (será criado depois)
├── mcp_client.py          # Cliente MCP (será criado depois)
├── test_system.py         # Testes (será criado depois)
├── requirements.txt       # Dependências (será criado depois)
├── run.sh                 # Script de execução (será criado depois)
└── README.md              # Documentação (será criado depois)

Por favor, forneça os comandos bash para:
1. Criar o diretório do projeto
2. Criar ambiente virtual Python
3. Ativar o ambiente virtual
4. Verificar a versão do Python

Formato de resposta: comandos bash prontos para executar.
```

---

## ✅ Resultado Esperado

Você deve receber comandos bash similares a:

```bash
# Criar diretório do projeto
mkdir mcp_project
cd mcp_project

# Criar ambiente virtual
python3.11 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Verificar versão do Python
python --version
```

---

## 🧪 Como Validar

Execute os comandos fornecidos e verifique:

```bash
# 1. Verificar se diretório foi criado
ls -la mcp_project/

# 2. Verificar se ambiente virtual existe
ls -la mcp_project/venv/

# 3. Verificar se Python está correto (deve mostrar 3.11.x)
python --version
```

**Saída esperada:**
```
Python 3.11.x
```

---

## 📝 Notas

- Se você não tiver Python 3.11, pode usar `python3` ou `python`
- O ambiente virtual isola as dependências do projeto
- Sempre ative o ambiente virtual antes de instalar pacotes
- No Windows, use `venv\Scripts\activate` ao invés de `source venv/bin/activate`

---

## ➡️ Próximo Passo

Após completar o setup, prossiga para: **`01-MCP-SERVER.md`**
