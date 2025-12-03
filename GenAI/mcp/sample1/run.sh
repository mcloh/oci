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
