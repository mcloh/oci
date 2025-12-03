# 🎨 Vibe Coding - Guia de Prompts para Recriar o Projeto MCP v2.0

Este diretório contém uma coleção completa de **prompts estruturados** que permitem recriar exatamente o projeto **Sistema MCP com AI Agent - Calculadora Inteligente v2.0** através de interações com um LLM (como Grok Code Fast).

## 📋 O que é Vibe Coding?

**Vibe Coding** é uma metodologia de desenvolvimento onde você utiliza prompts bem estruturados e específicos para guiar um LLM na geração de código, documentação e testes. Ao invés de escrever código manualmente, você "programa através de linguagem natural".

## 🎯 Objetivo

Permitir que qualquer pessoa recrie este projeto completo submetendo os prompts fornecidos a um LLM, obtendo como resultado exatamente os mesmos arquivos e funcionalidades da versão 2.0.

## 📂 Estrutura dos Prompts

Os prompts estão organizados em arquivos separados, cada um focado em gerar um componente específico do projeto:

```
vibe-coding-prompts/
├── README.md                          # Este arquivo (guia principal)
├── 00-SETUP.md                        # Prompt para setup inicial do projeto
├── 01-MCP-SERVER.md                   # Prompt para gerar mcp_server.py
├── 02-MCP-CLIENT.md                   # Prompt para gerar mcp_client.py
├── 03-TESTS.md                        # Prompt para gerar test_system.py
├── 04-REQUIREMENTS.md                 # Prompt para gerar requirements.txt
├── 05-RUN-SCRIPT.md                   # Prompt para gerar run.sh
├── 06-README-DOC.md                   # Prompt para gerar README.md
├── 07-QUICKSTART-DOC.md               # Prompt para gerar QUICKSTART.md
├── 08-CHANGELOG-DOC.md                # Prompt para gerar CHANGELOG.md
└── 09-VALIDATION.md                   # Prompt para validar o projeto completo
```

## 🚀 Como Usar Este Guia

### Método 1: Sequencial (Recomendado)

Execute os prompts na ordem numérica (00 → 09) para construir o projeto passo a passo:

1. **Leia** o arquivo de prompt (ex: `01-MCP-SERVER.md`)
2. **Copie** o prompt completo
3. **Cole** no LLM (Grok Code Fast ou similar)
4. **Salve** o código gerado no arquivo indicado
5. **Repita** para o próximo prompt

### Método 2: Por Componente

Se você já tem parte do projeto, pode usar prompts específicos para gerar ou atualizar componentes individuais.

### Método 3: Validação

Use o prompt `09-VALIDATION.md` para verificar se o projeto gerado está completo e funcional.

## 📝 Formato dos Prompts

Cada arquivo de prompt segue esta estrutura:

```markdown
# [Título do Componente]

## 🎯 Objetivo
[Descrição clara do que será gerado]

## 📋 Contexto
[Informações necessárias sobre o projeto]

## 🔧 Especificações Técnicas
[Requisitos técnicos detalhados]

## 💬 PROMPT COMPLETO
[Prompt pronto para copiar e colar no LLM]

## ✅ Resultado Esperado
[Descrição do arquivo que deve ser gerado]

## 🧪 Como Validar
[Instruções para testar o componente gerado]
```

## 🎓 Pré-requisitos

Antes de começar, certifique-se de ter:

- ✅ Acesso a um LLM (Grok Code Fast, GPT-4, Claude, etc.)
- ✅ Python 3.11+ instalado
- ✅ Conhecimento básico de terminal/linha de comando
- ✅ Editor de texto ou IDE

## 📊 Ordem de Execução Recomendada

| Ordem | Arquivo | Componente | Tempo Estimado |
|-------|---------|------------|----------------|
| 1 | `00-SETUP.md` | Setup inicial | 2 min |
| 2 | `01-MCP-SERVER.md` | Servidor MCP | 5 min |
| 3 | `02-MCP-CLIENT.md` | Cliente MCP | 5 min |
| 4 | `03-TESTS.md` | Testes automatizados | 3 min |
| 5 | `04-REQUIREMENTS.md` | Dependências | 1 min |
| 6 | `05-RUN-SCRIPT.md` | Script de execução | 2 min |
| 7 | `06-README-DOC.md` | Documentação principal | 3 min |
| 8 | `07-QUICKSTART-DOC.md` | Guia rápido | 2 min |
| 9 | `08-CHANGELOG-DOC.md` | Histórico de mudanças | 2 min |
| 10 | `09-VALIDATION.md` | Validação final | 5 min |

**Tempo total estimado:** ~30 minutos

## 🎯 O Que Você Vai Construir

Ao seguir todos os prompts, você terá um projeto completo com:

### Funcionalidades
- ✅ Servidor MCP com 4 operações matemáticas (soma, subtração, multiplicação, divisão)
- ✅ Cliente MCP com interpretação inteligente de operações
- ✅ Suporte a linguagem natural ("Eu tenho 25 maçãs e ganhei mais 13")
- ✅ Tratamento robusto de erros (divisão por zero, tipos inválidos)
- ✅ Mensagens educadas para operações não implementadas
- ✅ Interface de chat interativa

### Arquivos Gerados
- 📄 `mcp_server.py` (253 linhas) - Servidor MCP
- 📄 `mcp_client.py` (294 linhas) - Cliente MCP
- 📄 `test_system.py` (97 linhas) - Testes automatizados
- 📄 `requirements.txt` - Dependências
- 📄 `run.sh` - Script de inicialização
- 📄 `README.md` (472 linhas) - Documentação completa
- 📄 `QUICKSTART.md` (202 linhas) - Guia rápido
- 📄 `CHANGELOG.md` (128 linhas) - Histórico de mudanças

**Total:** ~1.800 linhas de código e documentação

## 💡 Dicas para Melhores Resultados

### 1. Seja Específico com o LLM
- Mencione que você quer código Python 3.11
- Especifique que está usando MCP e OpenAI SDK
- Indique claramente o nome do arquivo de saída

### 2. Valide Cada Etapa
- Teste cada componente antes de prosseguir
- Verifique se não há erros de sintaxe
- Confirme que as dependências estão corretas

### 3. Ajuste Quando Necessário
- Se o LLM gerar código diferente, você pode:
  - Pedir para ajustar detalhes específicos
  - Usar os prompts como base e iterar
  - Combinar partes de diferentes gerações

### 4. Mantenha o Contexto
- Ao usar prompts sequenciais, mencione o que já foi gerado
- Exemplo: "Já tenho o servidor MCP, agora preciso do cliente..."

## 🔧 Configurações Importantes

### API do LLM

Os prompts incluem configuração para:
- **URL Base:** `https://api.xptoai.com.br/genai/grokcode/v1`
- **API Key:** `chave de API do serviço de LLM`
- **Modelo:** `grokcode`

⚠️ **Nota:** Em produção, use variáveis de ambiente para credenciais.

### Dependências

O projeto requer:
- `mcp==1.23.1`
- `openai==2.8.1`

## 🧪 Testando o Projeto Gerado

Após gerar todos os componentes:

```bash
# 1. Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar testes
python test_system.py

# 4. Executar chat interativo
python mcp_client.py
```

## 📚 Recursos Adicionais

### Documentação de Referência
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

### Troubleshooting
Se encontrar problemas:
1. Verifique se todas as dependências estão instaladas
2. Confirme que está usando Python 3.11+
3. Valide que o ambiente virtual está ativado
4. Revise os logs de erro para identificar o problema

## 🤝 Contribuindo com Novos Prompts

Se você criar prompts para estender o projeto (novas operações, features, etc.), considere:
1. Seguir o formato estabelecido
2. Testar o prompt múltiplas vezes
3. Documentar o resultado esperado
4. Incluir exemplos de validação

## ⚡ Quick Start

Se você quer começar imediatamente:

```bash
# 1. Criar diretório do projeto
mkdir mcp_project && cd mcp_project

# 2. Abrir o primeiro prompt
cat vibe-coding-prompts/00-SETUP.md

# 3. Copiar o prompt e colar no LLM

# 4. Seguir as instruções geradas

# 5. Repetir para os próximos prompts
```

## ✨ Vantagens do Vibe Coding

- 🚀 **Velocidade:** Gere código completo em minutos
- 🎯 **Precisão:** Prompts estruturados garantem consistência
- 📚 **Aprendizado:** Entenda o código gerado estudando os prompts
- 🔄 **Reprodutibilidade:** Recrie o projeto quantas vezes quiser
- 🛠️ **Customização:** Ajuste prompts para suas necessidades

## 📖 Próximos Passos

1. **Leia** este README completamente
2. **Prepare** seu ambiente (Python, LLM, editor)
3. **Comece** pelo prompt `00-SETUP.md`
4. **Execute** os prompts sequencialmente
5. **Teste** cada componente gerado
6. **Valide** o projeto final com `09-VALIDATION.md`

---

**Pronto para começar?** Abra o arquivo `00-SETUP.md` e inicie sua jornada de Vibe Coding! 🚀

---

## 📞 Suporte

Se tiver dúvidas ou problemas:
1. Revise a seção de troubleshooting
2. Verifique se seguiu todos os passos
3. Consulte a documentação de referência
4. Ajuste os prompts conforme necessário

**Boa codificação vibrante!** ✨🎨
