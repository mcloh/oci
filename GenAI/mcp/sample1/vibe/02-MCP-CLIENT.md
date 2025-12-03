# 02 - Cliente MCP com Interpretação Inteligente

## 🎯 Objetivo

Gerar o arquivo `mcp_client.py` que implementa um cliente MCP com integração ao LLM, capaz de interpretar operações matemáticas solicitadas em linguagem natural e executá-las através do servidor MCP.

## 📋 Contexto

O cliente MCP conecta-se ao servidor via stdio, integra-se com um LLM (via API compatível com OpenAI) para interpretar as intenções do usuário, e executa tool calls apropriados. O sistema deve entender linguagem natural como "Eu tenho 25 maçãs e ganhei mais 13".

## 🔧 Especificações Técnicas

- **Framework:** MCP Client, OpenAI SDK
- **Comunicação:** stdio com servidor MCP
- **LLM:** API compatível com OpenAI
- **Interface:** Chat interativo via terminal
- **Histórico:** Mantém contexto da conversação

---

## 💬 PROMPT COMPLETO

```
Você é um desenvolvedor Python especialista em AI Agents e Model Context Protocol (MCP).

TAREFA:
Crie um arquivo Python chamado "mcp_client.py" que implemente um cliente MCP com integração a um LLM para criar uma calculadora inteligente com interface de chat.

REQUISITOS FUNCIONAIS:

1. CONEXÃO COM SERVIDOR MCP:
   - Conectar ao servidor via stdio (subprocess)
   - Comando: python3, args: ["mcp_server.py"]
   - Usar StdioServerParameters e stdio_client
   - Inicializar sessão e obter lista de ferramentas disponíveis

2. INTEGRAÇÃO COM LLM:
   - API Base URL: "https://api.xptoai.com.br/genai/grokcode/v1"
   - API Key: "chave de API para o serviço de LLM"
   - Modelo: "grokcode"
   - Usar OpenAI SDK (compatível)

3. INTERPRETAÇÃO INTELIGENTE:
   O LLM deve ser instruído (via system prompt) a:
   - Interpretar qual operação matemática o usuário deseja
   - Identificar os dois números envolvidos na conversa
   - Chamar a ferramenta apropriada automaticamente
   - Apresentar resultados de forma amigável

4. SYSTEM PROMPT (incluir no código):
   """
   Você é um assistente matemático inteligente que ajuda usuários a realizar operações matemáticas.
   Você tem acesso a 4 ferramentas: soma, subtração, multiplicação e divisão.
   
   Seu objetivo é:
   1. Interpretar qual operação matemática o usuário deseja realizar através da conversa natural
   2. Identificar os dois números que o usuário quer usar
   3. Chamar a ferramenta apropriada com os números corretos
   4. Apresentar o resultado de forma clara e amigável
   
   Exemplos de interpretação:
   - 'Quanto é 5 mais 3?' → usar ferramenta 'soma' com 5 e 3
   - 'Subtraia 10 de 25' → usar ferramenta 'subtracao' com 25 e 10
   - 'Multiplique 7 por 8' → usar ferramenta 'multiplicacao' com 7 e 8
   - 'Divida 20 por 4' → usar ferramenta 'divisao' com 20 e 4
   - '15 menos 7' → usar ferramenta 'subtracao' com 15 e 7
   
   Se o usuário pedir uma operação que não está disponível (como potência, raiz quadrada, etc.),
   informe educadamente que apenas as 4 operações básicas estão implementadas.
   
   Se houver erro na execução (como divisão por zero), explique o erro de forma educada e sugira uma alternativa.
   
   Seja conversacional, natural e prestativo na interação.
   """

5. CLASSE MCPChatClient:
   Métodos necessários:
   - __init__(): Inicializar OpenAI client, session, tools, histórico
   - connect_to_server(): Conectar ao servidor MCP via stdio
   - format_tools_for_openai(): Converter ferramentas MCP para formato OpenAI
   - call_mcp_tool(tool_name, arguments): Executar ferramenta no servidor
   - chat(user_message): Processar mensagem e retornar resposta
   - close(): Fechar conexões

6. FLUXO DO MÉTODO chat():
   a. Adicionar mensagem do usuário ao histórico
   b. Preparar mensagens (system prompt + histórico)
   c. Chamar LLM com ferramentas disponíveis
   d. Se LLM retornar tool_calls:
      - Executar cada tool call no servidor MCP
      - Adicionar resultados ao histórico
      - Fazer nova chamada ao LLM com os resultados
      - Retornar resposta final generativa
   e. Se não houver tool_calls:
      - Retornar resposta textual diretamente

7. FEEDBACK VISUAL:
   Ao executar ferramentas, imprimir:
   ```
   🔧 Executando ferramenta: nome_da_ferramenta
      Argumentos: {argumentos}
      ✓ Resultado: valor    (se sucesso)
      ⚠️  Erro: mensagem     (se erro)
   ```

8. INTERFACE DE CHAT:
   - Função main() com loop interativo
   - Prompt: "👤 Você: "
   - Resposta: "🤖 Assistente: "
   - Comando "sair" para encerrar
   - Tratamento de KeyboardInterrupt (Ctrl+C)

9. GERENCIAMENTO DE CONTEXTO:
   - Usar context managers assíncronos corretamente
   - stdio_context = stdio_client(server_params)
   - await stdio_context.__aenter__()
   - await stdio_context.__aexit__() no close()

REQUISITOS TÉCNICOS:

- Imports: asyncio, json, typing.Optional, mcp, mcp.client.stdio, openai
- Usar async/await para todas operações assíncronas
- Manter histórico de conversação (lista de dicts)
- Shebang: #!/usr/bin/env python3
- Docstrings em português

ESTRUTURA DO CÓDIGO:

1. Imports e constantes (API_BASE_URL, API_KEY, MODEL_NAME)
2. Classe MCPChatClient com todos os métodos
3. Função async main() com loop de chat
4. Bloco if __name__ == "__main__"

EXEMPLO DE CONVERSÃO DE FERRAMENTAS:
```python
def format_tools_for_openai(self) -> list:
    openai_tools = []
    for tool in self.available_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        })
    return openai_tools
```

Por favor, gere o código completo do arquivo mcp_client.py seguindo todas estas especificações.
```

---

## ✅ Resultado Esperado

Você deve receber um arquivo Python completo (~290 linhas) com:

**Estrutura:**
```python
#!/usr/bin/env python3
"""
Cliente MCP que interage com o usuário via chat usando LLM...
"""

import asyncio
import json
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

# Configuração do LLM
API_BASE_URL = "https://api.xptoai.com.br/genai/grokcode/v1"
API_KEY = "biasb986lk657fsdv6d3543vs5b65s7v373sd321vsdv4sdv34bv3f4hb5f4j6mn546tu"
MODEL_NAME = "grok-2-1212"

class MCPChatClient:
    # Métodos...

async def main():
    # Loop de chat...

if __name__ == "__main__":
    asyncio.run(main())
```

**Características:**
- ✅ Classe MCPChatClient completa
- ✅ Conexão com servidor MCP via stdio
- ✅ Integração com OpenAI SDK
- ✅ System prompt para interpretação inteligente
- ✅ Conversão de ferramentas MCP para formato OpenAI
- ✅ Execução de tool calls
- ✅ Feedback visual (✓ e ⚠️)
- ✅ Loop de chat interativo
- ✅ Tratamento de erros

---

## 🧪 Como Validar

Salve o código gerado em `mcp_project/mcp_client.py` e verifique:

```bash
# 1. Verificar sintaxe Python
python -m py_compile mcp_client.py

# 2. Verificar imports
python -c "import ast; ast.parse(open('mcp_client.py').read())"

# 3. Contar linhas
wc -l mcp_client.py

# 4. Verificar se constantes estão definidas
grep -E "API_BASE_URL|API_KEY|MODEL_NAME" mcp_client.py
```

**Saída esperada:**
```
294 mcp_client.py
```

**Verificação manual:**
- [ ] Arquivo tem shebang `#!/usr/bin/env python3`
- [ ] Constantes API_BASE_URL, API_KEY, MODEL_NAME definidas
- [ ] Classe MCPChatClient presente
- [ ] Método connect_to_server() implementado
- [ ] Método chat() com lógica de tool calls
- [ ] System prompt detalhado incluído
- [ ] Função main() com loop interativo
- [ ] Feedback visual com emojis (🔧, ✓, ⚠️)

---

## 📝 Notas

- O cliente inicia o servidor automaticamente via subprocess
- A API key está hardcoded (em produção, use variáveis de ambiente)
- O histórico de conversação permite contexto entre mensagens
- O LLM decide quando chamar ferramentas baseado no system prompt

---

## 🔧 Troubleshooting

**Erro: "Module 'openai' not found"**
- Solução: Instale as dependências (será feito no prompt 04)

**Erro: "Connection refused" ao conectar servidor**
- Verifique se mcp_server.py existe no mesmo diretório
- Confirme que o comando no StdioServerParameters está correto

**LLM não chama ferramentas:**
- Verifique se o system prompt está correto
- Confirme que format_tools_for_openai() retorna formato válido

---

## ➡️ Próximo Passo

Após validar o cliente, prossiga para: **`03-TESTS.md`**
