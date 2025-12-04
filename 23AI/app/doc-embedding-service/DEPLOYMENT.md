# Guia de Deployment - Document Embedding Service

Este documento fornece instruções detalhadas para fazer deployment do Document Embedding Service em diferentes ambientes.

## Pré-requisitos

### 1. Oracle Cloud Infrastructure (OCI)

- **Autonomous Database (ADW) 23AI** provisionado
- **Credenciais OCI** configuradas (tenancy, user, fingerprint, chave privada)
- **Connection OCID** do ADW disponível
- **Credenciais do banco de dados** (usuário e senha)

### 2. Sistema Operacional

- **Ubuntu 22.04** ou superior (recomendado)
- **Python 3.11** ou superior
- **Docker** e **Docker Compose** (para deployment containerizado)

### 3. Dependências do Sistema

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    python3-pip \
    python3-venv
```

## Deployment Local (Desenvolvimento)

### 1. Clone ou copie o projeto

```bash
cd /home/ubuntu
# Se estiver usando git:
# git clone <repository-url> doc-embedding-service
cd doc-embedding-service
```

### 2. Crie ambiente virtual Python

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale dependências

```bash
pip install -r requirements.txt
```

### 4. Configure credenciais OCI

```bash
# Copie o template
cp config/credentials.conf.example config/credentials.conf

# Edite com suas credenciais
nano config/credentials.conf
```

Exemplo de `config/credentials.conf`:
```ini
tenancy=ocid1.tenancy.oc1..aaaaaaa...
user=ocid1.user.oc1..aaaaaaa...
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
key_file=/home/ubuntu/doc-embedding-service/config/oci_api_key.pem
pass_phrase=
region=us-chicago-1
test_mode=false
```

**Importante**: Copie sua chave privada OCI para o local especificado em `key_file`.

### 5. Configure variáveis de ambiente

```bash
# Copie o template
cp .env.example .env

# Edite com suas configurações
nano .env
```

Exemplo de `.env`:
```bash
# API Security
API_KEY=your-secure-api-key-here

# OCI Configuration
OCI_CONFIG_FILE=/home/ubuntu/doc-embedding-service/config/credentials.conf
OCI_REGION=us-chicago-1
TEST_MODE=false

# Database Configuration
DB_USER=ADMIN
DB_PASSWORD=YourSecurePassword123!
DB_DSN=(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=your-adw.oraclecloud.com))(connect_data=(service_name=your_service_low.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Application Configuration
UPLOAD_FOLDER=/home/ubuntu/doc-embedding-service/uploads
MAX_UPLOAD_SIZE=52428800
DEBUG_AUTH=false
PORT=8000
```

### 6. Obtenha o DSN do ADW

No Oracle Cloud Console:
1. Acesse seu Autonomous Database
2. Clique em "DB Connection"
3. Baixe o Wallet (se necessário)
4. Copie o DSN do tipo `_low` ou `_medium`

### 7. Inicie o serviço

```bash
python app.py
```

O serviço estará disponível em `http://localhost:8000`

### 8. Teste o serviço

```bash
# Em outro terminal
python test_service.py
```

## Deployment com Docker

### 1. Configure variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas configurações
```

### 2. Configure credenciais OCI

```bash
cp config/credentials.conf.example config/credentials.conf
# Edite config/credentials.conf
# Copie sua chave privada para config/oci_api_key.pem
```

### 3. Build da imagem

```bash
docker build -t doc-embedding-service:latest .
```

### 4. Execute com Docker Compose

```bash
docker-compose up -d
```

### 5. Verifique os logs

```bash
docker-compose logs -f
```

### 6. Teste o serviço

```bash
curl http://localhost:8000/health
```

### 7. Pare o serviço

```bash
docker-compose down
```

## Deployment em Produção

### 1. Oracle Container Engine for Kubernetes (OKE)

#### Criar Secret para credenciais

```bash
kubectl create secret generic doc-embedding-secrets \
  --from-literal=api-key='your-api-key' \
  --from-literal=db-user='ADMIN' \
  --from-literal=db-password='YourPassword' \
  --from-file=oci-config=config/credentials.conf \
  --from-file=oci-key=config/oci_api_key.pem
```

#### Criar ConfigMap para DSN

```bash
kubectl create configmap doc-embedding-config \
  --from-literal=db-dsn='(description=...)'
```

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: doc-embedding-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: doc-embedding-service
  template:
    metadata:
      labels:
        app: doc-embedding-service
    spec:
      containers:
      - name: doc-embedding-service
        image: your-registry/doc-embedding-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: doc-embedding-secrets
              key: api-key
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: doc-embedding-secrets
              key: db-user
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: doc-embedding-secrets
              key: db-password
        - name: DB_DSN
          valueFrom:
            configMapKeyRef:
              name: doc-embedding-config
              key: db-dsn
        volumeMounts:
        - name: oci-credentials
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: oci-credentials
        secret:
          secretName: doc-embedding-secrets
          items:
          - key: oci-config
            path: credentials.conf
          - key: oci-key
            path: oci_api_key.pem
---
apiVersion: v1
kind: Service
metadata:
  name: doc-embedding-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: doc-embedding-service
```

### 2. Oracle Compute Instance

#### Instalar dependências

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv tesseract-ocr poppler-utils
```

#### Configurar serviço systemd

```bash
sudo nano /etc/systemd/system/doc-embedding.service
```

```ini
[Unit]
Description=Document Embedding Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/doc-embedding-service
Environment="PATH=/home/ubuntu/doc-embedding-service/venv/bin"
ExecStart=/home/ubuntu/doc-embedding-service/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Habilitar e iniciar

```bash
sudo systemctl daemon-reload
sudo systemctl enable doc-embedding
sudo systemctl start doc-embedding
sudo systemctl status doc-embedding
```

### 3. Nginx como Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoramento

### Health Check

```bash
curl http://localhost:8000/health
```

### Estatísticas

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/stats
```

### Logs

```bash
# Docker
docker-compose logs -f

# Systemd
sudo journalctl -u doc-embedding -f

# Arquivo de log (se configurado)
tail -f logs/app.log
```

## Troubleshooting

### Erro de conexão com banco de dados

1. Verifique se o DSN está correto
2. Verifique se as credenciais estão corretas
3. Verifique se o ADW está acessível (firewall, VCN)
4. Teste a conexão manualmente:

```python
import oracledb
conn = oracledb.connect(user="ADMIN", password="pwd", dsn="dsn")
print(conn.version)
```

### Erro ao carregar modelo de embeddings

1. Verifique se há espaço em disco suficiente
2. Verifique se há memória RAM suficiente
3. Tente usar um modelo menor:

```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Erro de OCR

1. Verifique se o Tesseract está instalado:

```bash
tesseract --version
```

2. Instale idiomas adicionais:

```bash
sudo apt-get install tesseract-ocr-por tesseract-ocr-eng
```

## Segurança

### Recomendações

1. **Nunca commite credenciais** no repositório Git
2. **Use HTTPS** em produção (configure SSL/TLS)
3. **Rotacione API keys** regularmente
4. **Use secrets management** (OCI Vault, Kubernetes Secrets)
5. **Limite tamanho de upload** conforme necessário
6. **Configure rate limiting** se necessário
7. **Monitore logs** para atividades suspeitas

### Firewall

```bash
# Permitir apenas porta 8000 (ou 80/443 se usar Nginx)
sudo ufw allow 8000/tcp
sudo ufw enable
```

## Backup

### Banco de Dados

O ADW possui backup automático. Configure retenção conforme necessário no OCI Console.

### Arquivos de Upload

```bash
# Backup diário
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
```

## Escalabilidade

### Horizontal Scaling

- Use **Load Balancer** (OCI Load Balancer ou Nginx)
- Deploy múltiplas instâncias do serviço
- Compartilhe storage de uploads (Object Storage)

### Vertical Scaling

- Aumente recursos da instância (CPU, RAM)
- Use GPU para embeddings mais rápidos (configure `EMBEDDING_DEVICE=cuda`)

## Suporte

Para questões e problemas:
1. Verifique os logs
2. Consulte a documentação do README.md
3. Execute o script de testes: `python test_service.py`
