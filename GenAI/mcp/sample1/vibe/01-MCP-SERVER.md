# 01 - Servidor MCP com 4 Operações Matemáticas

## 🎯 Objetivo

Gerar o arquivo `mcp_server.py` que implementa um servidor MCP com 4 ferramentas matemáticas: soma, subtração, multiplicação e divisão, incluindo tratamento robusto de erros.

## 📋 Contexto

O servidor MCP expõe ferramentas (tools) que podem ser chamadas pelo cliente. Cada ferramenta realiza uma operação matemática específica e retorna resultados estruturados em JSON.

## 🔧 Especificações Técnicas

- **Framework:** MCP (Model Context Protocol)
- **Comunicação:** stdio (entrada/saída padrão)
- **Formato de resposta:** JSON estruturado
- **Validações:** Parâmetros obrigatórios, tipos, divisão por zero
- **Operações:** soma, subtracao, multiplicacao, divisao

---

## 💬 PROMPT COMPLETO

```
Você é um desenvolvedor Python especialista em AI Agents e Model Context Protocol (MCP).

TAREFA:
Crie um arquivo Python chamado "mcp_server.py" que implemente um servidor MCP com 4 ferramentas matemáticas.

REQUISITOS FUNCIONAIS:

1. FERRAMENTAS (4 operações):
   - soma: Adiciona dois números inteiros
   - subtracao: Subtrai numero2 de numero1
   - multiplicacao: Multiplica dois números inteiros
   - divisao: Divide numero1 por numero2 (retorna float)

2. VALIDAÇÕES OBRIGATÓRIAS:
   - Verificar se ambos os parâmetros (numero1, numero2) foram fornecidos
   - Validar se os números são do tipo inteiro
   - Detectar divisão por zero e retornar erro apropriado
   - Tratar exceções com try-catch em cada operação

3. FORMATO DE RESPOSTA (Sucesso):
   {
     "operacao": "nome_da_operacao",
     "numero1": valor1,
     "numero2": valor2,
     "resultado": resultado_calculado,
     "expressao": "representacao_textual"  // ex: "15 + 7 = 22"
   }

4. FORMATO DE RESPOSTA (Erro):
   {
     "error": "descrição_do_erro",
     "operacao": "nome_da_operacao",
     ... (outros campos relevantes)
   }

5. OPERAÇÕES NÃO IMPLEMENTADAS:
   Se uma ferramenta desconhecida for chamada, retornar:
   {
     "error": "Operação 'nome' não está implementada",
     "operacao_solicitada": "nome",
     "operacoes_disponiveis": ["soma", "subtracao", "multiplicacao", "divisao"],
     "mensagem": "Por favor, utilize uma das operações disponíveis..."
   }

6. DIVISÃO ESPECIAL:
   Para divisão, incluir também:
   - resultado_inteiro: resultado da divisão inteira (numero1 // numero2)
   - resto: resto da divisão (numero1 % numero2)

REQUISITOS TÉCNICOS:

- Usar biblioteca: mcp.server, mcp.types, mcp.server.stdio
- Usar asyncio para operações assíncronas
- Nome do servidor: "math-tools-server"
- Comunicação via stdio_server()
- Decoradores: @app.list_tools() e @app.call_tool()
- Shebang: #!/usr/bin/env python3
- Docstrings em português

ESTRUTURA DO CÓDIGO:

1. Imports necessários
2. Criação da instância do servidor
3. Função list_tools() que retorna lista de Tool objects
4. Função call_tool(name, arguments) que executa as operações
5. Função main() que inicia o servidor via stdio
6. Bloco if __name__ == "__main__"

EXEMPLO DE VALIDAÇÃO DE DIVISÃO POR ZERO:
```python
if name == "divisao":
    if numero2 == 0:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Divisão por zero não é permitida",
                "operacao": "divisao",
                "numero1": numero1,
                "numero2": numero2
            })
        )]
```

Por favor, gere o código completo do arquivo mcp_server.py seguindo todas estas especificações.
```

---

## ✅ Resultado Esperado

Você deve receber um arquivo Python completo (~250 linhas) com:

**Estrutura:**
```python
#!/usr/bin/env python3
"""
Servidor MCP com ferramentas matemáticas...
"""

import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

app = Server("math-tools-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    # Retorna 4 ferramentas...

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Validações e execução...

async def main():
    # Inicia servidor...

if __name__ == "__main__":
    asyncio.run(main())
```

**Características:**
- ✅ 4 ferramentas definidas (soma, subtracao, multiplicacao, divisao)
- ✅ Validação de parâmetros obrigatórios
- ✅ Validação de tipos
- ✅ Tratamento de divisão por zero
- ✅ Try-catch em cada operação
- ✅ Respostas JSON estruturadas
- ✅ Mensagem para operações não implementadas

---

## 🧪 Como Validar

Salve o código gerado em `mcp_project/mcp_server.py` e verifique:

```bash
# 1. Verificar sintaxe Python
python -m py_compile mcp_server.py

# 2. Verificar imports (sem executar)
python -c "import ast; ast.parse(open('mcp_server.py').read())"

# 3. Contar linhas
wc -l mcp_server.py
```

**Saída esperada:**
```
253 mcp_server.py
```

**Verificação manual:**
- [ ] Arquivo tem shebang `#!/usr/bin/env python3`
- [ ] Imports: mcp.server, mcp.types, mcp.server.stdio, asyncio, json
- [ ] Decorador `@app.list_tools()` presente
- [ ] Decorador `@app.call_tool()` presente
- [ ] 4 ferramentas definidas no list_tools()
- [ ] Validação de divisão por zero implementada
- [ ] Função main() com stdio_server()

---

## 📝 Notas

- O servidor será executado pelo cliente via subprocess
- A comunicação acontece via stdin/stdout
- Não execute o servidor diretamente ainda (precisa do cliente)
- O servidor fica em loop aguardando comandos MCP

---

## 🔧 Troubleshooting

**Erro: "Module 'mcp' not found"**
- Solução: Instale as dependências (será feito no prompt 04)

**Erro de sintaxe:**
- Verifique se copiou o código completo
- Confirme que não há caracteres especiais corrompidos

---

## ➡️ Próximo Passo

Após validar o servidor, prossiga para: **`02-MCP-CLIENT.md`**
