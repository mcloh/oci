#!/usr/bin/env python3
"""
Servidor MCP com ferramentas matemáticas: soma, subtração, multiplicação e divisão.
Inclui tratamento de erros e validações.
"""

import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server


# Criar instância do servidor MCP
app = Server("math-tools-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista as ferramentas disponíveis no servidor."""
    return [
        Tool(
            name="soma",
            description="Realiza a soma de dois números inteiros",
            inputSchema={
                "type": "object",
                "properties": {
                    "numero1": {
                        "type": "integer",
                        "description": "Primeiro número inteiro"
                    },
                    "numero2": {
                        "type": "integer",
                        "description": "Segundo número inteiro"
                    }
                },
                "required": ["numero1", "numero2"]
            }
        ),
        Tool(
            name="subtracao",
            description="Realiza a subtração de dois números inteiros (numero1 - numero2)",
            inputSchema={
                "type": "object",
                "properties": {
                    "numero1": {
                        "type": "integer",
                        "description": "Primeiro número inteiro (minuendo)"
                    },
                    "numero2": {
                        "type": "integer",
                        "description": "Segundo número inteiro (subtraendo)"
                    }
                },
                "required": ["numero1", "numero2"]
            }
        ),
        Tool(
            name="multiplicacao",
            description="Realiza a multiplicação de dois números inteiros",
            inputSchema={
                "type": "object",
                "properties": {
                    "numero1": {
                        "type": "integer",
                        "description": "Primeiro número inteiro"
                    },
                    "numero2": {
                        "type": "integer",
                        "description": "Segundo número inteiro"
                    }
                },
                "required": ["numero1", "numero2"]
            }
        ),
        Tool(
            name="divisao",
            description="Realiza a divisão de dois números inteiros (numero1 / numero2). Retorna resultado como float.",
            inputSchema={
                "type": "object",
                "properties": {
                    "numero1": {
                        "type": "integer",
                        "description": "Primeiro número inteiro (dividendo)"
                    },
                    "numero2": {
                        "type": "integer",
                        "description": "Segundo número inteiro (divisor)"
                    }
                },
                "required": ["numero1", "numero2"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executa a ferramenta solicitada com tratamento de erros."""
    
    # Validar argumentos comuns
    numero1 = arguments.get("numero1")
    numero2 = arguments.get("numero2")
    
    if numero1 is None or numero2 is None:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Ambos os números são obrigatórios",
                "operacao": name
            })
        )]
    
    # Validar tipos
    if not isinstance(numero1, int) or not isinstance(numero2, int):
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Os números devem ser inteiros",
                "operacao": name,
                "numero1_tipo": type(numero1).__name__,
                "numero2_tipo": type(numero2).__name__
            })
        )]
    
    # Executar operação específica
    if name == "soma":
        try:
            resultado = numero1 + numero2
            return [TextContent(
                type="text",
                text=json.dumps({
                    "operacao": "soma",
                    "numero1": numero1,
                    "numero2": numero2,
                    "resultado": resultado,
                    "expressao": f"{numero1} + {numero2} = {resultado}"
                })
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Erro ao executar soma: {str(e)}",
                    "operacao": "soma"
                })
            )]
    
    elif name == "subtracao":
        try:
            resultado = numero1 - numero2
            return [TextContent(
                type="text",
                text=json.dumps({
                    "operacao": "subtracao",
                    "numero1": numero1,
                    "numero2": numero2,
                    "resultado": resultado,
                    "expressao": f"{numero1} - {numero2} = {resultado}"
                })
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Erro ao executar subtração: {str(e)}",
                    "operacao": "subtracao"
                })
            )]
    
    elif name == "multiplicacao":
        try:
            resultado = numero1 * numero2
            return [TextContent(
                type="text",
                text=json.dumps({
                    "operacao": "multiplicacao",
                    "numero1": numero1,
                    "numero2": numero2,
                    "resultado": resultado,
                    "expressao": f"{numero1} × {numero2} = {resultado}"
                })
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Erro ao executar multiplicação: {str(e)}",
                    "operacao": "multiplicacao"
                })
            )]
    
    elif name == "divisao":
        # Validação específica: divisão por zero
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
        
        try:
            resultado = numero1 / numero2
            return [TextContent(
                type="text",
                text=json.dumps({
                    "operacao": "divisao",
                    "numero1": numero1,
                    "numero2": numero2,
                    "resultado": resultado,
                    "resultado_inteiro": numero1 // numero2,
                    "resto": numero1 % numero2,
                    "expressao": f"{numero1} ÷ {numero2} = {resultado}"
                })
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Erro ao executar divisão: {str(e)}",
                    "operacao": "divisao"
                })
            )]
    
    else:
        # Operação não implementada
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Operação '{name}' não está implementada",
                "operacao_solicitada": name,
                "operacoes_disponiveis": ["soma", "subtracao", "multiplicacao", "divisao"],
                "mensagem": "Por favor, utilize uma das operações disponíveis: soma, subtração, multiplicação ou divisão"
            })
        )]


async def main():
    """Inicia o servidor MCP via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
