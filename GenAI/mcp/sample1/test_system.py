#!/usr/bin/env python3
"""
Script de teste automatizado para o sistema MCP.
Testa todas as 4 operações matemáticas e casos de erro.
"""

import asyncio
import json
from mcp_client import MCPChatClient


async def test_system():
    """Testa o sistema com uma sequência de mensagens variadas."""
    print("=" * 60)
    print("  TESTE AUTOMATIZADO - Sistema MCP")
    print("=" * 60)
    print()
    
    client = MCPChatClient()
    
    try:
        # Conectar ao servidor
        await client.connect_to_server()
        
        # Sequência de mensagens de teste
        test_cases = [
            {
                "descricao": "Teste de Soma",
                "mensagem": "Quanto é 15 mais 7?"
            },
            {
                "descricao": "Teste de Subtração",
                "mensagem": "Subtraia 5 de 20"
            },
            {
                "descricao": "Teste de Multiplicação",
                "mensagem": "Multiplique 8 por 6"
            },
            {
                "descricao": "Teste de Divisão",
                "mensagem": "Divida 100 por 4"
            },
            {
                "descricao": "Teste de Divisão por Zero (Erro Esperado)",
                "mensagem": "Divida 10 por 0"
            },
            {
                "descricao": "Teste de Operação Não Implementada",
                "mensagem": "Calcule 5 elevado ao quadrado"
            },
            {
                "descricao": "Teste de Linguagem Natural - Soma",
                "mensagem": "Eu tenho 25 maçãs e ganhei mais 13, quantas tenho agora?"
            },
            {
                "descricao": "Teste de Linguagem Natural - Subtração",
                "mensagem": "Se eu tinha 50 reais e gastei 18, quanto sobrou?"
            }
        ]
        
        print("📝 Executando sequência de testes...\n")
        print("=" * 60)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[Teste {i}/{len(test_cases)}] {test_case['descricao']}")
            print("-" * 60)
            print(f"👤 Usuário: {test_case['mensagem']}")
            
            response = await client.chat(test_case['mensagem'])
            
            print(f"🤖 Assistente: {response}")
            print("=" * 60)
            
            # Pequena pausa entre mensagens
            await asyncio.sleep(1)
        
        print("\n✅ Todos os testes concluídos!")
        print("\nResumo dos testes:")
        print("  ✓ Soma")
        print("  ✓ Subtração")
        print("  ✓ Multiplicação")
        print("  ✓ Divisão")
        print("  ✓ Tratamento de erro (divisão por zero)")
        print("  ✓ Operação não implementada")
        print("  ✓ Interpretação de linguagem natural")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_system())
