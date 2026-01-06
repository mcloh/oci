# OCI GenAI Automation Platform

Uma plataforma completa de automação e integração com Inteligência Artificial baseada na Oracle Cloud Infrastructure (OCI). Este projeto combina serviços de GenAI com ferramentas de automação de workflows para criar uma solução robusta de integração empresarial.

> **Disclaimer:**
> Este material é fornecido como um exemplo open-source de contribuição comunitária para implementação de soluções utilizando a plataforma Oracle.
> É distribuído "AS IS" (como está), sem garantias, responsabilidades ou suporte de qualquer natureza.
> A Oracle Corporation não assume qualquer responsabilidade pelo conteúdo, precisão, funcionalidade ou forma deste material.

## Visão Geral

A **OCI GenAI Automation Platform** é uma solução containerizada que oferece um proxy para os serviços GenAI da Oracle Cloud Infrastructure, integrado com ferramentas de automação como n8n e Node-RED. A plataforma foi projetada para facilitar a criação de workflows automatizados que incorporam capacidades de inteligência artificial, permitindo que desenvolvedores e empresas construam soluções inovadoras de forma rápida e eficiente.

O projeto utiliza uma arquitetura de microserviços baseada em Docker, com Traefik como reverse proxy e load balancer, garantindo escalabilidade, segurança e facilidade de manutenção. Todos os componentes são orquestrados para trabalhar em conjunto, proporcionando uma experiência integrada para desenvolvimento e produção.

## Características Principais

### Proxy GenAI para OCI
O componente central da plataforma é um proxy Flask que atua como intermediário entre aplicações cliente e os serviços GenAI da Oracle Cloud Infrastructure. Este proxy oferece autenticação automática via SDK OCI, simplificando significativamente o processo de integração com os serviços de IA da Oracle.

O proxy implementa endpoints RESTful (também compatíveis com OpenAI/v1) para criação de sessões de agentes IA e comunicação via chat, permitindo que aplicações interajam com modelos de linguagem avançados de forma transparente. Além disso, inclui um modo de teste que facilita o desenvolvimento e debugging, retornando respostas simuladas quando necessário.

### Plataforma de Automação Integrada
A solução incorpora duas poderosas ferramentas de automação que se complementam para diferentes casos de uso. O n8n oferece uma interface visual intuitiva para criação de workflows complexos, permitindo integração com centenas de serviços e APIs diferentes. Por sua vez, o Node-RED fornece capacidades especializadas para programação visual, especialmente útil para projetos de IoT e automação industrial.

Ambas as ferramentas são pré-configuradas para trabalhar em conjunto com o proxy GenAI, permitindo que workflows automatizados incorporem capacidades de inteligência artificial de forma nativa. Esta integração abre possibilidades para casos de uso inovadores, como processamento inteligente de documentos, análise automatizada de dados e criação de assistentes virtuais personalizados.

### Arquitetura Containerizada e Escalável
Toda a plataforma é construída sobre uma arquitetura de containers Docker, garantindo consistência entre ambientes de desenvolvimento e produção. O Traefik atua como reverse proxy e load balancer, fornecendo roteamento inteligente, terminação SSL/TLS automática e descoberta de serviços.

A configuração inclui volumes persistentes para garantir que dados importantes sejam preservados entre reinicializações, e uma rede isolada que garante comunicação segura entre os componentes. Scripts automatizados facilitam a configuração e deployment, reduzindo significativamente o tempo necessário para colocar a plataforma em funcionamento.

## Arquitetura do Sistema

### Componentes Principais

| Componente | Porta | Domínio | Descrição |
|------------|-------|---------|-----------|
| **Proxy GenAI** | 8000 | api.xptoai.com.br | Proxy Flask para serviços OCI GenAI |
| **n8n** | 5678 | n8n.xptoai.com.br | Plataforma de automação de workflows |
| **Node-RED** | 1880 | nodered.xptoai.com.br | Programação visual para IoT e automação |
| **Open Web UI** | 8080 | chat.xptoai.com.br | Interface de Chat com múltiplos LLMs |
| **Traefik** | 80/443 | - | Reverse proxy e load balancer |

### Fluxo de Dados
A arquitetura segue um padrão de microserviços onde cada componente tem responsabilidades bem definidas. Requisições externas chegam através do Traefik, que roteia o tráfego para o serviço apropriado baseado no domínio e path. O proxy GenAI autentica e encaminha requisições para os serviços OCI, enquanto n8n e Node-RED podem consumir estes serviços para criar workflows automatizados.

A comunicação entre serviços ocorre através de uma rede Docker isolada, garantindo segurança e performance. Volumes persistentes armazenam configurações, dados de workflows e credenciais, assegurando que informações importantes sejam preservadas.

## Estrutura do Projeto

```
oci/
├── GenAI/
│   └── proxy/
│       ├── app.py              # Aplicação Flask principal
│       ├── credentials.conf    # Configurações OCI
│       └── requirements.txt    # Dependências Python
├── docker/
│   ├── reverse-proxy-traefik/  # Configuração Traefik
│   ├── api_setup.sh           # Script setup da API
│   ├── n8n_setup.sh           # Script setup do n8n
│   ├── nodered_setup.sh       # Script setup do Node-RED
│   ├── webui_setup.sh         # Script setup do Open Web UI
│   ├── create_volumes.sh      # Criação de volumes Docker
│   ├── open_ports.sh          # Configuração de firewall
│   ├── n8n.env                # Variáveis ambiente n8n
│   ├── webui.env              # Variáveis ambiente Open Web UI
│   └── nodered.env            # Variáveis ambiente Node-RED
└── README.md
```

### Detalhamento dos Componentes

#### GenAI/proxy/
Este diretório contém o proxy Flask que serve como ponte entre aplicações cliente e os serviços GenAI da Oracle Cloud. O arquivo `app.py` implementa os endpoints da API, gerenciamento de sessões e autenticação OCI. As configurações de credenciais são armazenadas em `credentials.conf`, incluindo informações como user OCID, tenancy, fingerprint e localização da chave privada.

#### docker/
Contém todos os scripts e configurações necessários para orquestração dos containers. Os scripts de setup automatizam a criação e configuração de cada serviço, enquanto os arquivos de ambiente definem variáveis específicas para cada componente. A pasta `reverse-proxy-traefik` inclui configurações avançadas para roteamento e SSL.

## Instalação e Configuração

### Pré-requisitos

Antes de iniciar a instalação, certifique-se de que seu ambiente atende aos seguintes requisitos:

- **Docker Engine** versão 20.10 ou superior
- **Docker Compose** versão 2.0 ou superior  
- **Conta Oracle Cloud Infrastructure** com acesso aos serviços GenAI
- **Credenciais OCI** configuradas (API Key, tenancy, user OCID)
- **Domínio configurado** apontando para o servidor (opcional para desenvolvimento)

### Configuração das Credenciais OCI

1. **Obtenha suas credenciais OCI:**
   - Acesse o console da Oracle Cloud Infrastructure
   - Navegue até Identity & Security > Users
   - Selecione seu usuário e gere uma API Key
   - Anote o User OCID, Tenancy OCID e Fingerprint

2. **Configure o arquivo de credenciais:**
   ```bash
   cp GenAI/proxy/credentials.conf.example GenAI/proxy/credentials.conf
   ```

3. **Edite o arquivo `credentials.conf`:**
   ```ini
   user=ocid1.user.oc1..aaaaaaaad...
   fingerprint=a1:b2:c3:d4:e5:f6...
   tenancy=ocid1.tenancy.oc1..aaaaaaaad...
   region=us-ashburn-1
   key_file=/home/app/my_private_key.pem
   ```

### Instalação Rápida

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/mcloh/oci.git
   cd oci
   ```

2. **Configure as permissões:**
   ```bash
   chmod +x docker/*.sh
   ```

3. **Crie os volumes Docker:**
   ```bash
   ./docker/create_volumes.sh
   ```

4. **Configure o firewall:**
   ```bash
   sudo ./docker/open_ports.sh
   ```

5. **Inicie os serviços:**
   ```bash
   ./docker/api_setup.sh
   ./docker/n8n_setup.sh
   ./docker/nodered_setup.sh
   ./docker/webui_setup.sh
   ```

### Configuração Avançada

Para ambientes de produção, recomenda-se configurar certificados SSL personalizados e ajustar as configurações de segurança. O Traefik pode ser configurado para obter certificados Let's Encrypt automaticamente, ou você pode fornecer seus próprios certificados.

Edite os arquivos de ambiente (`n8n.env`, `nodered.env`) para personalizar configurações específicas de cada serviço, como URLs de webhook, configurações de banco de dados e parâmetros de segurança.

## Uso da API

### Endpoints Disponíveis

A API do proxy GenAI oferece os seguintes endpoints para interação com os serviços OCI:

#### Teste de Conectividade
```http
GET /
```
Retorna um status de saúde da API para verificar se o serviço está funcionando corretamente.

**Resposta:**
```json
{
  "test": "ok"
}
```

#### Criação de Nova Sessão
```http
POST /genai-agent/{region}/{agent_endpoint_id}/new-session
```
Cria uma nova sessão de chat com um agente GenAI específico.

**Parâmetros:**
- `region`: Região OCI onde o agente está hospedado
- `agent_endpoint_id`: ID do endpoint do agente GenAI

**Resposta:**
```json
{
  "sessionId": "session_12345"
}
```

#### Envio de Mensagem
```http
POST /genai-agent/{region}/{agent_endpoint_id}/{session_id}/chat
```
Envia uma mensagem para o agente GenAI em uma sessão específica.

**Corpo da Requisição:**
```json
{
  "userMessage": "Sua pergunta aqui"
}
```

**Resposta:**
```json
{
  "agentResponse": "Resposta do agente GenAI"
}
```

### Exemplos de Uso

#### Python
```python
import requests

# Criar nova sessão
response = requests.post(
    'http://api.xptoai.com.br/genai-agent/us-ashburn-1/agent123/new-session'
)
session_id = response.json()['sessionId']

# Enviar mensagem
response = requests.post(
    f'http://api.xptoai.com.br/genai-agent/us-ashburn-1/agent123/{session_id}/chat',
    json={'userMessage': 'Olá, como você pode me ajudar?'}
)
print(response.json()['agentResponse'])
```

#### JavaScript
```javascript
// Criar nova sessão
const sessionResponse = await fetch(
  'http://api.xptoai.com.br/genai-agent/us-ashburn-1/agent123/new-session',
  { method: 'POST' }
);
const { sessionId } = await sessionResponse.json();

// Enviar mensagem
const chatResponse = await fetch(
  `http://api.xptoai.com.br/genai-agent/us-ashburn-1/agent123/${sessionId}/chat`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userMessage: 'Olá, como você pode me ajudar?' })
  }
);
const { agentResponse } = await chatResponse.json();
console.log(agentResponse);
```

## Integração com n8n

O n8n oferece uma interface visual poderosa para criar workflows que podem integrar com o proxy GenAI. Através de nós HTTP, você pode facilmente incorporar capacidades de IA em seus processos automatizados.

### Exemplo de Workflow

1. **Trigger de Webhook:** Recebe dados de entrada
2. **Processamento:** Formata a mensagem para o GenAI
3. **Chamada API:** Envia para o proxy GenAI
4. **Resposta:** Processa a resposta da IA
5. **Ação:** Executa ação baseada na resposta

### Configuração no n8n

Acesse `http://n8n.xptoai.com.br` e configure um novo workflow:

1. Adicione um nó "HTTP Request"
2. Configure a URL: `http://api:8000/genai-agent/{region}/{agent_id}/new-session`
3. Adicione outro nó "HTTP Request" para enviar mensagens
4. Configure processamento da resposta conforme necessário

## Integração com Node-RED

O Node-RED complementa o n8n oferecendo capacidades especializadas para IoT e automação industrial. A integração com o proxy GenAI permite criar soluções inteligentes que respondem a eventos em tempo real.

### Casos de Uso Comuns

- **Análise de Sensores IoT:** Processar dados de sensores com IA
- **Manutenção Preditiva:** Analisar padrões para prever falhas
- **Automação Residencial:** Criar assistentes inteligentes para casa
- **Monitoramento Industrial:** Detectar anomalias automaticamente

### Configuração Básica

1. Acesse Node-RED na porta 1880
2. Adicione nós "http request" para comunicar com a API
3. Configure flows para processar dados de entrada
4. Implemente lógica de resposta baseada na IA

## Casos de Uso

### Desenvolvimento de Chatbots Empresariais

A plataforma facilita significativamente o desenvolvimento de chatbots personalizados para empresas. Utilizando o proxy GenAI, desenvolvedores podem criar interfaces conversacionais que aproveitam os modelos de linguagem avançados da Oracle Cloud, sem precisar lidar diretamente com a complexidade da autenticação e configuração OCI.

Um exemplo típico seria um chatbot de atendimento ao cliente que pode responder perguntas sobre produtos, processar solicitações de suporte e escalar questões complexas para agentes humanos. O n8n pode ser usado para criar workflows que integram o chatbot com sistemas CRM, bases de conhecimento e ferramentas de ticketing.

### Automação de Processos com IA

A combinação de n8n com o proxy GenAI permite criar automações sofisticadas que incorporam inteligência artificial. Por exemplo, um workflow pode monitorar emails recebidos, usar IA para classificar e priorizar mensagens, extrair informações relevantes e automaticamente criar tarefas ou tickets no sistema apropriado.

Outro caso comum é o processamento inteligente de documentos, onde arquivos são automaticamente analisados, categorizados e têm informações-chave extraídas usando capacidades de IA, reduzindo drasticamente o trabalho manual necessário.

### Análise e Monitoramento Inteligente

Para empresas que precisam monitorar grandes volumes de dados, a plataforma oferece capacidades de análise inteligente em tempo real. Node-RED pode coletar dados de múltiplas fontes (APIs, bancos de dados, sensores IoT), enquanto o GenAI analisa padrões, detecta anomalias e gera insights acionáveis.

Esta abordagem é particularmente valiosa para monitoramento de infraestrutura, análise de logs de segurança e detecção de fraudes, onde a capacidade de processar e compreender grandes volumes de dados não estruturados é crucial.

## Segurança e Melhores Práticas

### Configuração de Segurança

A segurança é uma consideração fundamental na arquitetura da plataforma. Todas as comunicações entre componentes ocorrem através de uma rede Docker isolada, minimizando a exposição a ataques externos. O Traefik fornece terminação SSL/TLS automática, garantindo que todas as comunicações externas sejam criptografadas.

As credenciais OCI são armazenadas de forma segura em arquivos de configuração protegidos, e o proxy implementa autenticação adequada para todos os requests aos serviços Oracle Cloud. É recomendado usar secrets management em ambientes de produção para maior segurança.

### Monitoramento e Logs

Todos os componentes geram logs detalhados que podem ser coletados e analisados para monitoramento de performance e detecção de problemas. O Docker facilita a coleta centralizada de logs, e ferramentas como ELK Stack ou Grafana podem ser integradas para visualização avançada.

Métricas de performance devem ser monitoradas regularmente, incluindo tempo de resposta da API, utilização de recursos dos containers e taxa de sucesso das requisições aos serviços OCI.

### Backup e Recuperação

Volumes Docker persistentes devem ser incluídos em estratégias regulares de backup para garantir que workflows, configurações e dados importantes sejam preservados. Scripts automatizados podem ser criados para backup incremental e restauração rápida em caso de falhas.

## Solução de Problemas

### Problemas Comuns

**Erro de Autenticação OCI:**
Verifique se as credenciais no arquivo `credentials.conf` estão corretas e se a chave privada está acessível no caminho especificado. Certifique-se de que o usuário OCI tem as permissões necessárias para acessar os serviços GenAI.

**Containers não iniciam:**
Verifique se todas as portas necessárias estão disponíveis e se o Docker tem permissões adequadas. Execute `docker logs <container_name>` para ver mensagens de erro específicas.

**Problemas de conectividade:**
Verifique se o firewall está configurado corretamente usando o script `open_ports.sh`. Certifique-se de que os domínios estão apontando para o servidor correto.

### Logs e Debugging

Para debugging detalhado, ative o modo de teste no proxy GenAI definindo `TEST_MODE=true` no arquivo de configuração. Isso fará com que a API retorne respostas simuladas, facilitando o teste de integração sem consumir recursos OCI.

Use `docker-compose logs -f` para monitorar logs em tempo real de todos os serviços, ou `docker logs -f <container_name>` para um serviço específico.

## Contribuição

Contribuições são bem-vindas! Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Diretrizes de Contribuição

- Mantenha o código limpo e bem documentado
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Siga as convenções de código existentes

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para detalhes completos.


