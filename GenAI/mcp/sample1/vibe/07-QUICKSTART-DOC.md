# 07 - Guia Rápido (QUICKSTART.md)

## 🎯 Objetivo

Gerar o arquivo `QUICKSTART.md` com um guia conciso de início rápido focado em fazer o usuário começar a usar o sistema em minutos.

## 📋 Contexto

O QUICKSTART é uma versão simplificada do README, focada em ação rápida com exemplos práticos e comandos prontos para copiar e colar.

## 🔧 Especificações Técnicas

- **Formato:** Markdown
- **Tamanho:** ~200 linhas
- **Foco:** Praticidade e velocidade
- **Tom:** Direto e objetivo

---

## 💬 PROMPT COMPLETO

```
Você é um technical writer especialista em documentação de início rápido.

TAREFA:
Crie um arquivo QUICKSTART.md conciso e prático para o projeto "Sistema MCP - Calculadora Inteligente".

ESTRUTURA DO DOCUMENTO:

1. TÍTULO
   # Guia Rápido - Sistema MCP com Calculadora Inteligente

2. INÍCIO RÁPIDO (## 🚀 Início Rápido (3 passos))
   Passos numerados com comandos bash:
   ### 1. Criar Ambiente Virtual
   ### 2. Instalar Dependências
   ### 3. Executar o Sistema (Opção A e B)

3. COMO USAR (## 💬 Como Usar)
   Explicar que o sistema interpreta automaticamente.
   
   ### Exemplos de Perguntas
   
   #### Soma
   - 3 exemplos de perguntas
   
   #### Subtração
   - 3 exemplos
   
   #### Multiplicação
   - 3 exemplos
   
   #### Divisão
   - 3 exemplos

4. FUNCIONALIDADES (## 🎯 Funcionalidades)
   Lista com checkmarks (✅)

5. TESTAR O SISTEMA (## 🧪 Testar o Sistema)
   Comando e lista de validações

6. EXEMPLO DE INTERAÇÃO COMPLETA (## 📋 Exemplo de Interação Completa)
   Bloco de código mostrando uma sessão completa:
   - Soma em linguagem natural
   - Divisão
   - Erro de divisão por zero
   - Operação não implementada

7. COMANDOS ÚTEIS (## 🛠️ Comandos Úteis)
   Lista de comandos com descrições:
   - Ativar ambiente virtual
   - Desativar ambiente virtual
   - Reinstalar dependências
   - Verificar instalação
   - Executar testes

8. PROBLEMAS COMUNS (## ❓ Problemas Comuns)
   4-5 problemas com soluções rápidas

9. DICAS DE USO (## 🎓 Dicas de Uso)
   5 dicas numeradas

10. DOCUMENTAÇÃO COMPLETA (## 📚 Documentação Completa)
    Link para README.md

11. OPERAÇÕES DISPONÍVEIS (## 🔑 Operações Disponíveis)
    Tabela com 3 colunas:
    | Operação | Exemplos de Perguntas |
    
    4 linhas (uma para cada operação)

12. RODAPÉ
    ---
    **Sistema pronto para uso! Divirta-se calculando! 🧮✨**

REQUISITOS DE FORMATAÇÃO:

- Usar emojis nos títulos
- Blocos de código bash com ```bash
- Comandos prontos para copiar
- Listas com bullet points ou numeradas
- Tabela markdown para operações
- Negrito para comandos importantes

CONTEÚDO ESPECÍFICO:

Comandos de instalação:
```bash
cd mcp_project
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Comandos de execução:
```bash
./run.sh
# ou
python mcp_client.py
```

Comando de teste:
```bash
python test_system.py
```

Exemplo de interação completa (incluir 4 interações):
1. Soma: "Eu tenho 25 maçãs e ganhei mais 13" → 38
2. Divisão: "Divida 100 por 4" → 25
3. Erro: "Divida 10 por 0" → Erro tratado
4. Não implementada: "Calcule 5 ao quadrado" → Limitação informada

Tabela de operações:
| Operação | Exemplos de Perguntas |
|----------|----------------------|
| **Soma** | "15 mais 7", "Some 10 com 5", "Quanto é 3 + 8?" |
| **Subtração** | "20 menos 5", "Subtraia 7 de 15", "Quanto é 30 - 12?" |
| **Multiplicação** | "8 vezes 6", "Multiplique 5 por 9", "Quanto é 7 × 4?" |
| **Divisão** | "100 dividido por 4", "Divida 50 por 2", "Quanto é 81 ÷ 9?" |

Por favor, gere o documento QUICKSTART.md completo seguindo esta estrutura.
O documento deve ter aproximadamente 200 linhas e ser direto ao ponto.
```

---

## ✅ Resultado Esperado

Você deve receber um documento Markdown (~200 linhas) com:

**Características:**
- ✅ Guia de 3 passos para começar
- ✅ Exemplos práticos de perguntas
- ✅ Comandos prontos para copiar
- ✅ Exemplo de interação completa
- ✅ Tabela de operações disponíveis
- ✅ Troubleshooting rápido
- ✅ Dicas de uso

---

## 🧪 Como Validar

```bash
# 1. Contar linhas
wc -l QUICKSTART.md

# 2. Verificar estrutura
grep "^#" QUICKSTART.md
```

**Saída esperada:**
```
202 QUICKSTART.md
```

---

## ➡️ Próximo Passo

Prossiga para: **`08-CHANGELOG-DOC.md`**
