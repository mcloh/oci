# 04 - Arquivo de Dependências

## 🎯 Objetivo

Gerar o arquivo `requirements.txt` com as dependências necessárias para o projeto.

## 📋 Contexto

O arquivo requirements.txt lista todas as bibliotecas Python necessárias com suas versões específicas para garantir reprodutibilidade.

## 🔧 Especificações Técnicas

- **Formato:** Padrão pip (package==version)
- **Dependências:** mcp, openai
- **Versões:** Fixas para garantir compatibilidade

---

## 💬 PROMPT COMPLETO

```
Crie um arquivo chamado "requirements.txt" para um projeto Python que usa:
- Model Context Protocol (MCP) versão 1.23.1
- OpenAI SDK versão 2.8.1

O arquivo deve seguir o formato padrão do pip (package==version).
Liste apenas estas duas dependências, uma por linha.
```

---

## ✅ Resultado Esperado

Você deve receber um arquivo de texto simples:

```
mcp==1.23.1
openai==2.8.1
```

---

## 🧪 Como Validar

Salve o conteúdo em `mcp_project/requirements.txt` e verifique:

```bash
# 1. Verificar conteúdo
cat requirements.txt

# 2. Contar linhas (deve ser 2)
wc -l requirements.txt

# 3. Instalar dependências (com ambiente virtual ativado)
pip install -r requirements.txt
```

**Saída esperada da instalação:**
```
Successfully installed mcp-1.23.1 openai-2.8.1 [e outras dependências transitivas]
```

---

## 📝 Notas

- As versões especificadas foram testadas e são compatíveis
- Dependências transitivas serão instaladas automaticamente
- Em produção, considere usar `pip freeze > requirements.txt`

---

## ➡️ Próximo Passo

Após criar requirements.txt, prossiga para: **`05-RUN-SCRIPT.md`**
