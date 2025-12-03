# 03 - Testes Automatizados Abrangentes

## 🎯 Objetivo

Gerar o arquivo `test_system.py` que implementa testes automatizados para validar todas as 4 operações matemáticas, tratamento de erros e interpretação de linguagem natural.

## 📋 Contexto

Os testes devem cobrir casos de sucesso (happy path), casos de erro (divisão por zero), operações não implementadas e interpretação de linguagem natural contextual.

## 🔧 Especificações Técnicas

- **Framework:** Reutiliza MCPChatClient
- **Casos de teste:** 8 cenários diferentes
- **Execução:** Sequencial com pausas entre testes
- **Saída:** Relatório formatado com resumo final

---

## 💬 PROMPT COMPLETO

```
Você é um desenvolvedor Python especialista em testes automatizados para sistemas com AI Agents.

TAREFA:
Crie um arquivo Python chamado "test_system.py" que implemente testes automatizados abrangentes para o sistema MCP de calculadora inteligente.

REQUISITOS FUNCIONAIS:

1. IMPORTAR E REUTILIZAR:
   - Importar a classe MCPChatClient de mcp_client.py
   - Usar asyncio para execução assíncrona
   - Não duplicar código, apenas testar

2. CASOS DE TESTE (8 cenários):

   TESTE 1 - Soma:
   - Descrição: "Teste de Soma"
   - Mensagem: "Quanto é 15 mais 7?"
   - Resultado esperado: 22

   TESTE 2 - Subtração:
   - Descrição: "Teste de Subtração"
   - Mensagem: "Subtraia 5 de 20"
   - Resultado esperado: 15

   TESTE 3 - Multiplicação:
   - Descrição: "Teste de Multiplicação"
   - Mensagem: "Multiplique 8 por 6"
   - Resultado esperado: 48

   TESTE 4 - Divisão:
   - Descrição: "Teste de Divisão"
   - Mensagem: "Divida 100 por 4"
   - Resultado esperado: 25

   TESTE 5 - Divisão por Zero (Erro Esperado):
   - Descrição: "Teste de Divisão por Zero (Erro Esperado)"
   - Mensagem: "Divida 10 por 0"
   - Resultado esperado: Erro tratado educadamente

   TESTE 6 - Operação Não Implementada:
   - Descrição: "Teste de Operação Não Implementada"
   - Mensagem: "Calcule 5 elevado ao quadrado"
   - Resultado esperado: Informação sobre limitação

   TESTE 7 - Linguagem Natural (Soma):
   - Descrição: "Teste de Linguagem Natural - Soma"
   - Mensagem: "Eu tenho 25 maçãs e ganhei mais 13, quantas tenho agora?"
   - Resultado esperado: 38

   TESTE 8 - Linguagem Natural (Subtração):
   - Descrição: "Teste de Linguagem Natural - Subtração"
   - Mensagem: "Se eu tinha 50 reais e gastei 18, quanto sobrou?"
   - Resultado esperado: 32

3. ESTRUTURA DE DADOS:
   Usar lista de dicionários:
   ```python
   test_cases = [
       {
           "descricao": "Teste de Soma",
           "mensagem": "Quanto é 15 mais 7?"
       },
       # ... outros casos
   ]
   ```

4. FUNÇÃO test_system():
   - Criar instância de MCPChatClient
   - Conectar ao servidor
   - Iterar sobre test_cases
   - Para cada teste:
     * Imprimir cabeçalho com número e descrição
     * Imprimir mensagem do usuário
     * Chamar client.chat(mensagem)
     * Imprimir resposta do assistente
     * Adicionar pausa de 1 segundo entre testes
   - Imprimir resumo final

5. FORMATAÇÃO DE SAÍDA:
   ```
   ============================================================
     TESTE AUTOMATIZADO - Sistema MCP
   ============================================================
   
   ✓ Conectado ao servidor MCP
   ✓ Ferramentas disponíveis: ['soma', 'subtracao', 'multiplicacao', 'divisao']
   
   📝 Executando sequência de testes...
   
   ============================================================
   
   [Teste 1/8] Teste de Soma
   ------------------------------------------------------------
   👤 Usuário: Quanto é 15 mais 7?
   🤖 Assistente: [resposta do LLM]
   ============================================================
   
   [Teste 2/8] Teste de Subtração
   ...
   
   ✅ Todos os testes concluídos!
   
   Resumo dos testes:
     ✓ Soma
     ✓ Subtração
     ✓ Multiplicação
     ✓ Divisão
     ✓ Tratamento de erro (divisão por zero)
     ✓ Operação não implementada
     ✓ Interpretação de linguagem natural
   ```

6. TRATAMENTO DE ERROS:
   - Try-catch na função test_system()
   - Imprimir traceback completo em caso de erro
   - Sempre fechar conexão no bloco finally

REQUISITOS TÉCNICOS:

- Imports: asyncio, json, MCPChatClient
- Função async test_system()
- Usar await asyncio.sleep(1) entre testes
- Shebang: #!/usr/bin/env python3
- Docstrings em português
- Bloco if __name__ == "__main__"

ESTRUTURA DO CÓDIGO:

1. Shebang e docstring
2. Imports
3. Função async test_system()
4. Bloco if __name__ == "__main__"

EXEMPLO DE LOOP DE TESTES:
```python
for i, test_case in enumerate(test_cases, 1):
    print(f"\n[Teste {i}/{len(test_cases)}] {test_case['descricao']}")
    print("-" * 60)
    print(f"👤 Usuário: {test_case['mensagem']}")
    
    response = await client.chat(test_case['mensagem'])
    
    print(f"🤖 Assistente: {response}")
    print("=" * 60)
    
    await asyncio.sleep(1)
```

Por favor, gere o código completo do arquivo test_system.py seguindo todas estas especificações.
```

---

## ✅ Resultado Esperado

Você deve receber um arquivo Python completo (~100 linhas) com:

**Estrutura:**
```python
#!/usr/bin/env python3
"""
Script de teste automatizado para o sistema MCP...
"""

import asyncio
import json
from mcp_client import MCPChatClient

async def test_system():
    # Implementação dos testes...

if __name__ == "__main__":
    asyncio.run(test_system())
```

**Características:**
- ✅ 8 casos de teste definidos
- ✅ Formatação visual clara
- ✅ Numeração de testes (1/8, 2/8, etc.)
- ✅ Pausas entre testes
- ✅ Resumo final
- ✅ Tratamento de erros
- ✅ Bloco finally para cleanup

---

## 🧪 Como Validar

Salve o código gerado em `mcp_project/test_system.py` e verifique:

```bash
# 1. Verificar sintaxe Python
python -m py_compile test_system.py

# 2. Contar linhas
wc -l test_system.py

# 3. Verificar estrutura
grep -E "test_cases|async def test_system" test_system.py
```

**Saída esperada:**
```
97 test_system.py
```

**Verificação manual:**
- [ ] Arquivo tem shebang `#!/usr/bin/env python3`
- [ ] Import de MCPChatClient presente
- [ ] Lista test_cases com 8 casos
- [ ] Função async test_system()
- [ ] Loop iterando sobre test_cases
- [ ] Formatação com emojis e separadores
- [ ] Resumo final com checkmarks
- [ ] Bloco try-except-finally

---

## 📝 Notas

- Os testes não executam ainda (dependências não instaladas)
- Cada teste espera 1 segundo para não sobrecarregar a API
- O resumo final é apenas visual, não valida resultados
- Em produção, considere usar pytest para assertions

---

## 🔧 Troubleshooting

**Erro: "Cannot import MCPChatClient"**
- Verifique se mcp_client.py está no mesmo diretório
- Confirme que não há erros de sintaxe em mcp_client.py

**Testes muito lentos:**
- Ajuste o asyncio.sleep(1) para valores menores
- Considere executar testes em paralelo (avançado)

---

## ➡️ Próximo Passo

Após validar os testes, prossiga para: **`04-REQUIREMENTS.md`**
