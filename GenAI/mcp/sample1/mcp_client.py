#!/usr/bin/env python3
"""
Cliente MCP que interage com o usuário via chat usando LLM.
Interpreta a operação matemática desejada e executa através do servidor MCP.
"""

import asyncio
import json
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI


# Configuração do LLM
API_BASE_URL = "https://api.xptoai.com.br/genai/grokcode/v1"
API_KEY = "sua chave de API para o endopoint do LLM"
MODEL_NAME = "grokcode"  # Modelo padrão, pode ser ajustado


class MCPChatClient:
    """Cliente de chat que integra MCP com LLM."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=API_BASE_URL,
            api_key=API_KEY
        )
        self.session: Optional[ClientSession] = None
        self.available_tools = []
        self.conversation_history = []
        
    async def connect_to_server(self):
        """Conecta ao servidor MCP."""
        server_params = StdioServerParameters(
            command="python3",
            args=["mcp_server.py"],
            env=None
        )
        
        # stdio_client retorna um context manager assíncrono
        self.stdio_context = stdio_client(server_params)
        self.stdio, self.write = await self.stdio_context.__aenter__()
        self.session = ClientSession(self.stdio, self.write)
        
        await self.session.__aenter__()
        
        # Inicializar sessão
        await self.session.initialize()
        
        # Obter lista de ferramentas disponíveis
        tools_list = await self.session.list_tools()
        self.available_tools = tools_list.tools
        
        print(f"✓ Conectado ao servidor MCP")
        print(f"✓ Ferramentas disponíveis: {[tool.name for tool in self.available_tools]}\n")
    
    def format_tools_for_openai(self) -> list:
        """Formata as ferramentas MCP para o formato OpenAI."""
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
    
    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Chama uma ferramenta no servidor MCP."""
        result = await self.session.call_tool(tool_name, arguments)
        
        # Extrair o conteúdo de texto do resultado
        if result.content and len(result.content) > 0:
            return result.content[0].text
        return json.dumps({"error": "Nenhum resultado retornado"})
    
    async def chat(self, user_message: str) -> str:
        """Processa uma mensagem do usuário e retorna a resposta do LLM."""
        
        # Adicionar mensagem do usuário ao histórico
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Preparar mensagens para o LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente matemático inteligente que ajuda usuários a realizar operações matemáticas. "
                    "Você tem acesso a 4 ferramentas: soma, subtração, multiplicação e divisão. "
                    "\n\n"
                    "Seu objetivo é:\n"
                    "1. Interpretar qual operação matemática o usuário deseja realizar através da conversa natural\n"
                    "2. Identificar os dois números que o usuário quer usar\n"
                    "3. Chamar a ferramenta apropriada com os números corretos\n"
                    "4. Apresentar o resultado de forma clara e amigável\n"
                    "\n"
                    "Exemplos de interpretação:\n"
                    "- 'Quanto é 5 mais 3?' → usar ferramenta 'soma' com 5 e 3\n"
                    "- 'Subtraia 10 de 25' → usar ferramenta 'subtracao' com 25 e 10\n"
                    "- 'Multiplique 7 por 8' → usar ferramenta 'multiplicacao' com 7 e 8\n"
                    "- 'Divida 20 por 4' → usar ferramenta 'divisao' com 20 e 4\n"
                    "- '15 menos 7' → usar ferramenta 'subtracao' com 15 e 7\n"
                    "\n"
                    "Se o usuário pedir uma operação que não está disponível (como potência, raiz quadrada, etc.), "
                    "informe educadamente que apenas as 4 operações básicas estão implementadas. "
                    "\n"
                    "Seja conversacional, natural e prestativo na interação."
                )
            }
        ] + self.conversation_history
        
        # Fazer chamada ao LLM com ferramentas
        openai_tools = self.format_tools_for_openai()
        
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            tool_choice="auto" if openai_tools else None
        )
        
        assistant_message = response.choices[0].message
        
        # Verificar se o LLM quer chamar ferramentas
        if assistant_message.tool_calls:
            # Adicionar a resposta do assistente ao histórico
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            # Executar as ferramentas solicitadas
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Executando ferramenta: {function_name}")
                print(f"   Argumentos: {function_args}")
                
                # Chamar a ferramenta MCP
                tool_result = await self.call_mcp_tool(function_name, function_args)
                
                # Verificar se houve erro no resultado
                try:
                    result_data = json.loads(tool_result)
                    if "error" in result_data:
                        print(f"   ⚠️  Erro: {result_data['error']}")
                    else:
                        print(f"   ✓ Resultado: {result_data.get('resultado', tool_result)}")
                except:
                    print(f"   Resultado: {tool_result}")
                
                print()
                
                # Adicionar resultado da ferramenta ao histórico
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Fazer nova chamada ao LLM com os resultados das ferramentas
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente matemático inteligente que ajuda usuários a realizar operações matemáticas. "
                        "Você tem acesso a 4 ferramentas: soma, subtração, multiplicação e divisão. "
                        "\n\n"
                        "Seu objetivo é:\n"
                        "1. Interpretar qual operação matemática o usuário deseja realizar através da conversa natural\n"
                        "2. Identificar os dois números que o usuário quer usar\n"
                        "3. Chamar a ferramenta apropriada com os números corretos\n"
                        "4. Apresentar o resultado de forma clara e amigável\n"
                        "\n"
                        "Exemplos de interpretação:\n"
                        "- 'Quanto é 5 mais 3?' → usar ferramenta 'soma' com 5 e 3\n"
                        "- 'Subtraia 10 de 25' → usar ferramenta 'subtracao' com 25 e 10\n"
                        "- 'Multiplique 7 por 8' → usar ferramenta 'multiplicacao' com 7 e 8\n"
                        "- 'Divida 20 por 4' → usar ferramenta 'divisao' com 20 e 4\n"
                        "- '15 menos 7' → usar ferramenta 'subtracao' com 15 e 7\n"
                        "\n"
                        "Se o usuário pedir uma operação que não está disponível (como potência, raiz quadrada, etc.), "
                        "informe educadamente que apenas as 4 operações básicas estão implementadas. "
                        "\n"
                        "Se houver erro na execução (como divisão por zero), explique o erro de forma educada e sugira uma alternativa. "
                        "\n"
                        "Seja conversacional, natural e prestativo na interação."
                    )
                }
            ] + self.conversation_history
            
            final_response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages
            )
            
            final_message = final_response.choices[0].message.content
            
            # Adicionar resposta final ao histórico
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })
            
            return final_message
        
        else:
            # Não há chamadas de ferramentas, apenas resposta textual
            response_text = assistant_message.content or ""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            return response_text
    
    async def close(self):
        """Fecha a conexão com o servidor MCP."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, 'stdio_context'):
            await self.stdio_context.__aexit__(None, None, None)


async def main():
    """Função principal que executa o chat interativo."""
    print("=" * 60)
    print("  Chat com AI Agent - Operações Matemáticas")
    print("=" * 60)
    print()
    
    client = MCPChatClient()
    
    try:
        # Conectar ao servidor MCP
        await client.connect_to_server()
        
        print("💬 Iniciando conversa com o assistente...")
        print("   (Digite 'sair' para encerrar)\n")
        print("-" * 60)
        
        # Loop de chat interativo
        while True:
            # Obter entrada do usuário
            user_input = input("\n👤 Você: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Encerrando chat. Até logo!")
                break
            
            # Processar mensagem
            print("\n🤖 Assistente: ", end="", flush=True)
            response = await client.chat(user_input)
            print(response)
            print("-" * 60)
    
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrompido. Até logo!")
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Fechar conexão
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
