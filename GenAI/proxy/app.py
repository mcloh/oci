from flask import Flask, request, jsonify, abort
import oci
import requests
import os
from datetime import datetime, timedelta
import uuid
import time

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
# Inferência GenAI
# --------------------------

def call_inference_model(region, compartment_id, model_id, prompt):
    if TEST_MODE:
        return {"response": {"text": f"Resposta simulada: {prompt}", "finish_reason": "stop"}}

    try:
        endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"

        generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config,
            service_endpoint=endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240)
        )

        content = oci.generative_ai_inference.models.TextContent(text=prompt)
        message = oci.generative_ai_inference.models.Message(role="USER", content=[content])

        chat_request = oci.generative_ai_inference.models.GenericChatRequest(
            api_format=oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC,
            messages=[message],
            max_tokens=50000,
            temperature=1,
            top_p=1,
            top_k=0
        )

        chat_detail = oci.generative_ai_inference.models.ChatDetails(
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_id),
            chat_request=chat_request,
            compartment_id=compartment_id
        )

        chat_response = generative_ai_inference_client.chat(chat_detail)
        choice = chat_response.data.chat_response.choices[0]

        return {"response": {
            "text": choice.message.content[0].text,
            "finish_reason": choice.finish_reason
        }}

    except Exception as e:
        return {"error": str(e)}

# --------------------------
# Autenticação
# --------------------------

def check_api_key():
    expected_key = os.environ.get("API_KEY")
    if not expected_key:
        print("AVISO: API_KEY não configurada.")
        return

    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1].strip()
    else:
        token = request.headers.get("X-API-Key")

    if token != expected_key:
        abort(401, description="API key inválida.")

@app.before_request
def before_all_requests():
    check_api_key()

# --------------------------
# Endpoints REST
# --------------------------

@app.route("/", methods=["GET"])
def test():
    return jsonify({"status": "ok"})

@app.route("/genai-agent/<region>/<agent_endpoint_id>/session", methods=["POST"])
def manage_session(region, agent_endpoint_id):
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

    try:
        base_url = f"https://agent-runtime.generativeai.{region}.oci.oraclecloud.com/20240531"
        chat_url = f"{base_url}/agentEndpoints/{agent_endpoint_id}/actions/chat"
        session_obj = requests.Session()
        session_obj.auth = signer
        payload = {
            "userMessage": user_message,
            "shouldStream": False,
            "sessionId": session_id
        }
        response = session_obj.post(chat_url, json=payload)
        response.raise_for_status()
        return jsonify({"agentResponse": response.json()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/genai/<region>/<compartment_id>/<model_id>/inference", methods=["POST"])
def inference(region, compartment_id, model_id):
    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400

    response_data = call_inference_model(region, compartment_id, model_id, prompt)
    return jsonify(response_data)

@app.route("/genai/<region>/<compartment_id>/<model_id>/v1/chat/completions", methods=["POST"])
def openai_compatible_chat(region, compartment_id, model_id):
    data = request.get_json()
    messages = data.get("messages", [])
    temperature = data.get("temperature", 1)
    top_p = data.get("top_p", 1)
    top_k = data.get("top_k", 0)
    max_tokens = data.get("max_tokens", 1000)

    user_prompt = next((m["content"] for m in reversed(messages) if m["role"] == "user"), None)
    if not user_prompt:
        return jsonify({"error": "mensagem do usuário é obrigatória"}), 400

    response = call_inference_model(region, compartment_id, model_id, user_prompt)
    if "error" in response:
        return jsonify({"error": response["error"]}), 500

    result_text = response["response"]["text"]
    finish_reason = response["response"].get("finish_reason", "stop")

    return jsonify({
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": result_text},
                "finish_reason": finish_reason
            }
        ]
    })

@app.route("/genai/<region>/<compartment_id>/<model_id>/v1/completions", methods=["POST"])
def openai_compatible_completion(region, compartment_id, model_id):
    data = request.get_json()
    prompt = data.get("prompt")
    temperature = data.get("temperature", 1)
    top_p = data.get("top_p", 1)
    top_k = data.get("top_k", 0)
    max_tokens = data.get("max_tokens", 1000)
    stop = data.get("stop")

    if not prompt:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400

    response = call_inference_model(region, compartment_id, model_id, prompt)
    if "error" in response:
        return jsonify({"error": response["error"]}), 500

    result_text = response["response"]["text"]
    finish_reason = response["response"].get("finish_reason", "stop")

    if stop:
        if isinstance(stop, list):
            for s in stop:
                if s in result_text:
                    result_text = result_text.split(s)[0]
                    break
        elif isinstance(stop, str) and stop in result_text:
            result_text = result_text.split(stop)[0]

    return jsonify({
        "id": f"cmpl-{uuid.uuid4().hex[:12]}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "text": result_text,
                "logprobs": None,
                "finish_reason": finish_reason
            }
        ]
    })

# --------------------------
# Inicialização
# --------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
