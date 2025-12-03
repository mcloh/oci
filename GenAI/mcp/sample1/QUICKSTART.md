# Guia Rápido - Sistema MCP com Calculadora Inteligente

## 🚀 Início Rápido (3 passos)

### 1. Criar Ambiente Virtual

```bash
cd mcp_project
python3.11 -m venv venv
```

### 2. Instalar Dependências

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Executar o Sistema

**Opção A - Script automatizado:**
```bash
./run.sh
```

**Opção B - Comando direto:**
```bash
source venv/bin/activate
python mcp_client.py
```

## 💬 Como Usar

O sistema **interpreta automaticamente** qual operação você deseja realizar através de linguagem natural!

### Exemplos de Perguntas

#### Soma
- "Quanto é 15 mais 7?"
- "Some 25 com 13"
- "Eu tenho 30 maçãs e ganhei mais 12, quantas tenho?"

#### Subtração
- "Subtraia 5 de 20"
- "Quanto é 50 menos 18?"
- "Se eu tinha 100 reais e gastei 35, quanto sobrou?"

#### Multiplicação
- "Multiplique 8 por 6"
- "Quanto é 7 vezes 9?"
- "Calcule 12 multiplicado por 5"

#### Divisão
- "Divida 100 por 4"
- "Quanto é 50 dividido por 2?"
- "Calcule 144 dividido por 12"

## 🎯 Funcionalidades

✅ **4 Operações**: soma, subtração, multiplicação, divisão
✅ **Linguagem Natural**: Entende perguntas conversacionais
✅ **Tratamento de Erros**: Detecta divisão por zero
✅ **Operações Não Implementadas**: Informa quando algo não está disponível

## 🧪 Testar o Sistema

Execute o teste automatizado para ver todas as funcionalidades:

```bash
source venv/bin/activate
python test_system.py
```

O teste valida:
- ✓ Soma
- ✓ Subtração
- ✓ Multiplicação
- ✓ Divisão
- ✓ Erro de divisão por zero
- ✓ Operação não implementada
- ✓ Interpretação de linguagem natural

## 📋 Exemplo de Interação Completa

```
============================================================
  Chat com AI Agent - Operações Matemáticas
============================================================

✓ Conectado ao servidor MCP
✓ Ferramentas disponíveis: ['soma', 'subtracao', 'multiplicacao', 'divisao']

💬 Iniciando conversa com o assistente...
------------------------------------------------------------

👤 Você: Eu tenho 25 maçãs e ganhei mais 13, quantas tenho agora?

🔧 Executando ferramenta: soma
   Argumentos: {'numero1': 25, 'numero2': 13}
   ✓ Resultado: 38

🤖 Assistente: Você tinha 25 maçãs e ganhou mais 13, então agora tem 
38 maçãs no total!

------------------------------------------------------------

👤 Você: Divida 100 por 4

🔧 Executando ferramenta: divisao
   Argumentos: {'numero1': 100, 'numero2': 4}
   ✓ Resultado: 25.0

🤖 Assistente: 100 dividido por 4 é igual a 25!

------------------------------------------------------------

👤 Você: Divida 10 por 0

🔧 Executando ferramenta: divisao
   Argumentos: {'numero1': 10, 'numero2': 0}
   ⚠️  Erro: Divisão por zero não é permitida

🤖 Assistente: Dividir por zero é uma operação matematicamente 
indefinida. Não posso fazer isso, mas posso ajudar com outras contas!

------------------------------------------------------------

👤 Você: Calcule 5 elevado ao quadrado

🤖 Assistente: Desculpe, mas eu só consigo fazer as operações básicas: 
soma, subtração, multiplicação e divisão. Se quiser fazer 5 vezes 5, 
posso ajudar!
```

## 🛠️ Comandos Úteis

### Ativar ambiente virtual
```bash
source venv/bin/activate
```

### Desativar ambiente virtual
```bash
deactivate
```

### Reinstalar dependências
```bash
pip install -r requirements.txt --force-reinstall
```

### Verificar instalação
```bash
pip list | grep -E "mcp|openai"
```

### Executar testes
```bash
python test_system.py
```

## ❓ Problemas Comuns

### "Command not found: python3.11"
Use `python3` ou `python` dependendo da sua instalação.

### "Permission denied: ./run.sh"
Execute: `chmod +x run.sh`

### "Module not found: mcp"
Certifique-se de ativar o ambiente virtual: `source venv/bin/activate`

### "Divisão por zero"
Este é um erro esperado e tratado. O assistente informará que não é possível.

### "Operação não implementada"
O sistema suporta apenas 4 operações básicas. O assistente informará as limitações.

## 🎓 Dicas de Uso

1. **Seja Natural**: Fale como você falaria com uma pessoa
2. **Contexto**: Pode usar contexto ("Eu tinha X e ganhei Y")
3. **Variações**: Teste diferentes formas de perguntar
4. **Erros**: O sistema trata erros educadamente
5. **Limitações**: Apenas 4 operações básicas estão disponíveis

## 📚 Documentação Completa

Para mais detalhes sobre arquitetura, API e extensões, consulte [README.md](README.md)

## 🔑 Operações Disponíveis

| Operação | Exemplos de Perguntas |
|----------|----------------------|
| **Soma** | "15 mais 7", "Some 10 com 5", "Quanto é 3 + 8?" |
| **Subtração** | "20 menos 5", "Subtraia 7 de 15", "Quanto é 30 - 12?" |
| **Multiplicação** | "8 vezes 6", "Multiplique 5 por 9", "Quanto é 7 × 4?" |
| **Divisão** | "100 dividido por 4", "Divida 50 por 2", "Quanto é 81 ÷ 9?" |

---

**Sistema pronto para uso! Divirta-se calculando! 🧮✨**
