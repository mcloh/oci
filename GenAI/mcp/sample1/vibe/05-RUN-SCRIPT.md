# 05 - Script de Inicialização Rápida

## 🎯 Objetivo

Gerar o arquivo `run.sh` que automatiza a inicialização do sistema MCP.

## 📋 Contexto

O script bash facilita a execução do projeto, verificando dependências e ativando o ambiente virtual automaticamente.

## 🔧 Especificações Técnicas

- **Linguagem:** Bash script
- **Funcionalidades:** Verificação de ambiente, instalação de deps, execução
- **Permissões:** Executável (chmod +x)

---

## 💬 PROMPT COMPLETO

```
Crie um script bash chamado "run.sh" para iniciar um projeto Python MCP.

REQUISITOS:

1. CABEÇALHO:
   - Shebang: #!/bin/bash
   - Comentário descritivo

2. BANNER INICIAL:
   Imprimir:
   ```
   ==========================================
     Sistema MCP - Operações Matemáticas
   ==========================================
   ```

3. VERIFICAÇÕES:
   - Verificar se diretório "venv" existe
   - Se não existir, imprimir erro e instruções
   - Exit code 1 se falhar

4. ATIVAÇÃO DO AMBIENTE VIRTUAL:
   - source venv/bin/activate

5. VERIFICAÇÃO DE DEPENDÊNCIAS:
   - Tentar importar módulo "mcp" em Python
   - Se falhar, instalar dependências: pip install -r requirements.txt

6. EXECUÇÃO:
   - Imprimir "🚀 Iniciando cliente MCP..."
   - Executar: python mcp_client.py

FORMATO DE MENSAGENS:
- Usar emojis: ❌ para erro, 📦 para instalação, 🚀 para execução
- Linhas em branco para separação visual

EXEMPLO DE VERIFICAÇÃO:
```bash
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "   Execute: python3.11 -m venv venv"
    exit 1
fi
```

Por favor, gere o script bash completo seguindo estas especificações.
```

---

## ✅ Resultado Esperado

Você deve receber um script bash (~25 linhas):

```bash
#!/bin/bash
# Script de inicialização rápida do sistema MCP

echo "=========================================="
echo "  Sistema MCP - Operações Matemáticas"
echo "=========================================="
echo ""

# Verificar se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "   Execute: python3.11 -m venv venv"
    exit 1
fi

# Ativar ambiente virtual
source venv/bin/activate

# Verificar se dependências estão instaladas
if ! python -c "import mcp" 2>/dev/null; then
    echo "📦 Instalando dependências..."
    pip install -r requirements.txt
    echo ""
fi

# Executar cliente MCP
echo "🚀 Iniciando cliente MCP..."
echo ""
python mcp_client.py
```

---

## 🧪 Como Validar

Salve o script em `mcp_project/run.sh` e execute:

```bash
# 1. Tornar executável
chmod +x run.sh

# 2. Verificar sintaxe
bash -n run.sh

# 3. Testar execução (com venv criado)
./run.sh
```

**Saída esperada:**
```
==========================================
  Sistema MCP - Operações Matemáticas
==========================================

🚀 Iniciando cliente MCP...

[Chat interface inicia]
```

---

## 📝 Notas

- O script assume que você está no diretório do projeto
- Funciona em Linux/Mac (no Windows, use Git Bash ou WSL)
- Instala dependências automaticamente se necessário
- Requer que o ambiente virtual já exista

---

## 🔧 Troubleshooting

**Erro: "Permission denied"**
```bash
chmod +x run.sh
```

**Erro: "venv not found"**
```bash
python3.11 -m venv venv
```

---

## ➡️ Próximo Passo

Após criar o script, prossiga para: **`06-README-DOC.md`**
