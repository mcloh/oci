from flask import Flask, request, jsonify
import oci
import requests

app = Flask(__name__)

# Função para carregar configurações do arquivo
def load_config(config_file="/home/app/credentials.conf"):
    config = {}
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Ignora linhas vazias e comentários
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo de configuração '{config_file}' não encontrado")
    except Exception as e:
        raise Exception(f"Erro ao carregar configuração: {str(e)}")

# Carrega configuração do arquivo
config = load_config()

# Modo de teste (define se deve usar credenciais reais ou simuladas)
TEST_MODE = config.get("test_mode", "false").lower() == "true"

# Cria o signer do OCI (apenas se não estiver em modo de teste)
signer = None
if not TEST_MODE:
    try:
        signer = oci.signer.Signer(
            tenancy=config.get("tenancy"),
            user=config.get("user"),
            fingerprint=config.get("fingerprint"),
            private_key_file_location=config.get("key_file"),
            pass_phrase=config.get("pass_phrase"),
            private_key_content=config.get("key_content"),
        )
    except Exception as e:
        print(f"Erro ao inicializar signer OCI: {e}")
        print("Executando em modo de teste...")
        TEST_MODE = True

# Funções de interação com o agente (adaptadas do agent_proxy.py)
def new_session_agent(region, agent_endpoint_id):
    if TEST_MODE:
        # Retorna uma resposta simulada em modo de teste
        return {"id": f"test_session_{agent_endpoint_id[:8]}"}

    session = requests.Session()
    session.auth = signer
    url = (
        f"https://agent-runtime.generativeai.{region}.oci.oraclecloud.com/20240531/agentEndpoints/{agent_endpoint_id}/sessions"
    )
    payload = {
        "description": "",
        "displayName": "",
        "idleTimeoutInSeconds": "1200"
    }
    resp = session.post(url, json=payload)
    resp.raise_for_status() # Levanta um erro para status codes 4xx/5xx
    return resp.json()

def ask_agent(region, agent_endpoint_id, session_id, user_message):
    if TEST_MODE:
        # Retorna uma resposta simulada em modo de teste
        return {
            "message": f"Resposta simulada para: {user_message}",
            "sessionId": session_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }

    session = requests.Session()
    session.auth = signer
    base_url = f"https://agent-runtime.generativeai.{region}.oci.oraclecloud.com/20240531"
    chat_url = f"{base_url}/agentEndpoints/{agent_endpoint_id}/actions/chat"
    payload = {
        "userMessage": user_message,
        "shouldStream": False,
        "sessionId": session_id
    }
    response = session.post(chat_url, json=payload)
    response.raise_for_status() # Levanta um erro para status codes 4xx/5xx
    return response.json()


# Endpoint para teste
@app.route("/", methods=["GET"])
def test():
    return jsonify({"test":"ok"})

# Endpoint para criar nova sessão
@app.route("/genai-agent/<region>/<agent_endpoint_id>/new-session", methods=["GET"])
def new_session(region, agent_endpoint_id):
    try:
        response_data = new_session_agent(region, agent_endpoint_id)
        return jsonify({"sessionId": response_data.get("id")})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"error": str(e)}), 400

# Endpoint para chat com o agente
@app.route("/genai-agent/<region>/<agent_endpoint_id>/<session_id>/chat", methods=["POST"])
def agent_chat(region, agent_endpoint_id, session_id):
    data = request.get_json()
    user_message = data.get("userMessage")
    if not all([user_message]):
        print("missing userMessage")
        return jsonify({"error": "userMessage é obrigatório"}), 400
    try:
        response_data = ask_agent(region, agent_endpoint_id, session_id, user_message)
        return jsonify({"agentResponse": response_data})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
