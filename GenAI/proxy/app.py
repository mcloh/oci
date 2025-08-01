from flask import Flask, request, jsonify, abort
import oci
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# --------------------------
# Configuração
# --------------------------

def load_config(config_file="/home/app/credentials.conf"):
    config = {}
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo de configuração '{config_file}' não encontrado")
    except Exception as e:
        raise Exception(f"Erro ao carregar configuração: {str(e)}")

config = load_config()
TEST_MODE = config.get("test_mode", "false").lower() == "true"

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

# --------------------------
# Session Store
# --------------------------

SESSION_STORE = {}
SESSION_TTL = timedelta(hours=2)

def session_controller(region, agent_endpoint_id, channel, cuid):
    """
    Controla sessões com o agente, reaproveitando se estiver dentro do TTL (2h).
    A cada interação, a sessão é renovada (sliding TTL).
    """
    session_key = f"{channel}:{cuid}"
    now = datetime.utcnow()

    existing = SESSION_STORE.get(session_key)
    if existing:
        last_used = existing["lastUsedAt"]
        if now - last_used < SESSION_TTL:
            existing["lastUsedAt"] = now
            return {
                "id": existing["sessionId"],
                "sessionKey": session_key,
                "reused": True
            }

    # Sessão expirada ou inexistente → cria nova
    if TEST_MODE:
        new_session_id = f"test_session_{agent_endpoint_id[:8]}_{int(now.timestamp())}"
        SESSION_STORE[session_key] = {
            "sessionId": new_session_id,
            "createdAt": now,
            "lastUsedAt": now,
            "sessionKey": session_key
        }
        return {
            "id": new_session_id,
            "sessionKey": session_key,
            "reused": False
        }

    try:
        session = requests.Session()
        session.auth = signer
        url = (
            f"https://agent-runtime.generativeai.{region}.oci.oraclecloud.com/20240531/"
            f"agentEndpoints/{agent_endpoint_id}/sessions"
        )
        payload = {
            "description": f"Session for {session_key}",
            "displayName": session_key,
            "idleTimeoutInSeconds": str(int(SESSION_TTL.total_seconds()))
        }
        resp = session.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        SESSION_STORE[session_key] = {
            "sessionId": data.get("id"),
            "createdAt": now,
            "lastUsedAt": now,
            "sessionKey": session_key
        }
        data["sessionKey"] = session_key
        data["reused"] = False
        return data
    except Exception as e:
        return {"error": str(e), "sessionKey": session_key}

# --------------------------
# Funções de interação
# --------------------------

def ask_agent(region, agent_endpoint_id, session_id, user_message):
    if TEST_MODE:
        return {
            "message": f"Resposta simulada para: {user_message}",
            "sessionId": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
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
    response.raise_for_status()
    return response.json()

def call_inference_model(region, compartment_id, model_id, prompt):
    if TEST_MODE:
        return {"response": f"Resposta simulada para o prompt: {prompt}"}

    try:
        endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"

        generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config,
            service_endpoint=endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240)
        )
        chat_detail = oci.generative_ai_inference.models.ChatDetails()

        content = oci.generative_ai_inference.models.TextContent()
        content.text = f"{prompt}"
        message = oci.generative_ai_inference.models.Message()
        message.role = "USER"
        message.content = [content]

        chat_request = oci.generative_ai_inference.models.GenericChatRequest()
        chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
        chat_request.messages = [message]
        chat_request.max_tokens = 50000
        chat_request.temperature = 1
        chat_request.top_p = 1
        chat_request.top_k = 0

        chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_id)
        chat_detail.chat_request = chat_request
        chat_detail.compartment_id = compartment_id

        chat_response = generative_ai_inference_client.chat(chat_detail)
        chat_choices = chat_response.data.chat_response.choices
        chat_data = {
            "text": chat_choices[0].message.content[0].text,
            "finish_reason": chat_choices[0].finish_reason
        }

        return {"response": chat_data}
    except Exception as e:
        return {"error": str(e)}

# --------------------------
# Segurança
# --------------------------

def check_api_key():
    expected_key = os.environ.get("API_KEY")
    if not expected_key:
        print("AVISO: API_KEY não configurada nas variáveis de ambiente.")
        return
    provided_key = request.headers.get("X-API-Key")
    if provided_key != expected_key:
        abort(401, description="Chave de API inválida ou ausente.")

@app.before_request
def before_all_requests():
    check_api_key()

# --------------------------
# Endpoints
# --------------------------

@app.route("/", methods=["GET"])
def test():
    return jsonify({"test": "ok"})

@app.route("/test/<myvar>/copy", methods=["GET"])
def var_copy(myvar):
    return jsonify({"myvar": myvar})

@app.route("/genai-agent/<region>/<agent_endpoint_id>/session", methods=["POST"])
def manage_session(region, agent_endpoint_id):
    """
    Reaproveita ou cria uma sessão nova com base em channel + cuid.
    """
    data = request.get_json()
    channel = data.get("channel")
    cuid = data.get("cuid")
    if not all([channel, cuid]):
        return jsonify({"error": "Parâmetros 'channel' e 'cuid' são obrigatórios"}), 400
    response_data = session_controller(region, agent_endpoint_id, channel, cuid)
    return jsonify(response_data)

@app.route("/genai-agent/<region>/<agent_endpoint_id>/<session_id>/chat", methods=["POST"])
def agent_chat(region, agent_endpoint_id, session_id):
    data = request.get_json()
    user_message = data.get("userMessage")
    if not user_message:
        return jsonify({"error": "userMessage é obrigatório"}), 400
    response_data = ask_agent(region, agent_endpoint_id, session_id, user_message)
    return jsonify({"agentResponse": response_data})

@app.route("/genai/<region>/<compartment_id>/<model_id>/inference", methods=["POST"])
def inference(region, compartment_id, model_id):
    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400
    response_data = call_inference_model(region, compartment_id, model_id, prompt)
    return jsonify(response_data)

# --------------------------
# Main
# --------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
