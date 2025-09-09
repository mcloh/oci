# api.py — OCI GenAI + OpenAI v1 Compatibility
# -----------------------------------------------------------------------------
# Requisitos:
#   pip install flask oci requests
# Execução:
#   export API_KEY="minha-chave"
#   python api.py  # porta 8000
# -----------------------------------------------------------------------------

from flask import Flask, request, jsonify, abort, Response, stream_with_context
import oci
import requests
import os
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Generator

app = Flask(__name__)

# ==========================
# Configuração
# ==========================

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

# ==========================
# Modelos suportados (defaults)
# ==========================

SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
    "gpt5": {
        "id": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyasebknceb4ekbiaiisjtu3fj5i7s4io3ignvg4ip2uyma",
        "params": {
            "max_completion_tokens": 2048,
            "reasoning_effort": "MEDIUM",
            "verbosity": "MEDIUM"
        }
    },
    "grok3mini": {
        "id": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyavwbgai5nlntsd5hngaileroifuoec5qxttmydhq7mykq",
        "params": {
            "temperature": 1,
            "top_p": 1,
            "max_tokens": 600
        }
    },
    "llama4maverick": {
        "id": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyayjawvuonfkw2ua4bob4rlnnlhs522pafbglivtwlfzta",
        "params": {
            "temperature": 1,
            "top_p": 0.75,
            "max_tokens": 600,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
    }
}

# ==========================
# Session Store (Agente)
# ==========================

SESSION_STORE = {}
SESSION_TTL = timedelta(hours=1)

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

# ==========================
# Funções de interação (Agente + Inference)
# ==========================

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
    # DEBUG: imprimir o corpo recebido (pedido por você)
    print(">>> /inference payload recebido:")
    data = {"prompt": prompt, "region": region, "compartment_id": compartment_id, "model_id": model_id}
    #print(data)

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

# ==========================
# Utilitários (OpenAI v1 compat)
# ==========================

ROLE_MAP = {
    "system": "SYSTEM",
    "user": "USER",
    "assistant": "ASSISTANT",
}

def resolve_model_and_params(body: Dict[str, Any], path_model_id: str) -> Dict[str, Any]:
    """
    Resolve o OCID do modelo a partir de:
      1) body['model'] se for chave suportada;
      2) body['model'] se for OCID;
      3) path_model_id se for chave suportada ou OCID.
    Mescla defaults + overrides do corpo (OpenAI-like).
    """
    user_model = body.get("model")
    model_key = None
    model_ocid = None

    if isinstance(user_model, str) and user_model in SUPPORTED_MODELS:
        model_key = user_model
        model_ocid = SUPPORTED_MODELS[user_model]["id"]
        defaults = SUPPORTED_MODELS[user_model]["params"].copy()
    elif isinstance(user_model, str) and user_model.startswith("ocid1.generativeaimodel"):
        model_ocid = user_model
        defaults = {}
    else:
        if path_model_id and path_model_id.startswith("ocid1.generativeaimodel"):
            model_ocid = path_model_id
            defaults = {}
        elif path_model_id in SUPPORTED_MODELS:
            model_key = path_model_id
            model_ocid = SUPPORTED_MODELS[path_model_id]["id"]
            defaults = SUPPORTED_MODELS[path_model_id]["params"].copy()
        else:
            raise ValueError("Modelo ausente ou não suportado: use um dos "
                             f"{list(SUPPORTED_MODELS.keys())} ou forneça um OCID válido.")

    overrides = {}
    for k in [
        "temperature", "top_p", "max_tokens", "frequency_penalty", "presence_penalty",
        "reasoning_effort", "verbosity", "max_completion_tokens"
    ]:
        if k in body and body[k] is not None:
            overrides[k] = body[k]

    merged = {**defaults, **overrides}
    return {"model_key": model_key, "model_ocid": model_ocid, "params": merged}

def to_oci_messages(openai_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converte mensagens no formato OpenAI para o formato da OCI.
    """
    oci_msgs: List[Dict[str, Any]] = []
    for m in openai_messages:
        role = ROLE_MAP.get(str(m.get("role", "")).lower(), "USER")
        content = m.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for p in content:
                if isinstance(p, dict) and p.get("type") == "text":
                    text_parts.append(p.get("text", ""))
                elif isinstance(p, str):
                    text_parts.append(p)
            content_str = "\n".join([t for t in text_parts if t])
        elif isinstance(content, str):
            content_str = content
        else:
            content_str = str(content)

        oci_msgs.append({
            "role": role,
            "content": [
                {"type": "TEXT", "text": content_str}
            ]
        })
    return oci_msgs

def build_oci_chat_payload(messages: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monta o payload para /actions/chat da OCI.
    """
    payload = {"messages": messages}

    if "temperature" in params:
        payload["temperature"] = params["temperature"]
    if "top_p" in params:
        payload["top_p"] = params["top_p"]
    if "frequency_penalty" in params:
        payload["frequency_penalty"] = params["frequency_penalty"]
    if "presence_penalty" in params:
        payload["presence_penalty"] = params["presence_penalty"]

    if "max_completion_tokens" in params:
        payload["max_completion_tokens"] = params["max_completion_tokens"]
    elif "max_tokens" in params:
        payload["max_completion_tokens"] = params["max_tokens"]

    if "reasoning_effort" in params:
        payload["reasoning_effort"] = params["reasoning_effort"]
    if "verbosity" in params:
        payload["verbosity"] = params["verbosity"]

    return payload

def oci_chat_invoke(region: str, compartment_id: str, model_ocid: str, oci_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoca o /actions/chat da OCI. Em TEST_MODE retorna dry-run.
    """
    # DEBUG: imprimir o payload que vai para a OCI (útil para validar 'role')
    print(">>> OCI CHAT REQUEST (payload que será enviado):")
    print(json.dumps(oci_payload, ensure_ascii=False, indent=2))

    if TEST_MODE:
        return {
            "dry_run": True,
            "note": "TEST_MODE=True — retorno simulado.",
            "payload": oci_payload,
            "output_text": "[dry-run] ambiente de teste — valide o payload impresso no console."
        }

    try:
        endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"
        client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config,
            service_endpoint=endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240)
        )

        # Monta ChatDetails + GenericChatRequest com api_format=GENERIC
        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        generic = oci.generative_ai_inference.models.GenericChatRequest()
        generic.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC

        # Converte nosso payload em objetos do SDK
        sdk_messages = []
        for m in oci_payload["messages"]:
            sdk_msg = oci.generative_ai_inference.models.Message()
            sdk_msg.role = m["role"]
            parts = []
            for c in m["content"]:
                tc = oci.generative_ai_inference.models.TextContent()
                tc.text = c.get("text", "")
                parts.append(tc)
            sdk_msg.content = parts
            sdk_messages.append(sdk_msg)

        generic.messages = sdk_messages

        # Parâmetros
        if "temperature" in oci_payload:
            generic.temperature = oci_payload["temperature"]
        if "top_p" in oci_payload:
            generic.top_p = oci_payload["top_p"]
        if "frequency_penalty" in oci_payload:
            generic.frequency_penalty = oci_payload["frequency_penalty"]
        if "presence_penalty" in oci_payload:
            generic.presence_penalty = oci_payload["presence_penalty"]
        if "max_completion_tokens" in oci_payload:
            # Algumas versões do SDK usam 'max_tokens'; mantemos ambos por segurança
            generic.max_tokens = oci_payload["max_completion_tokens"]

        # Extras (se suportados pelo modelo)
        # OBS: reasoning_effort/verbosity são específicos e podem não ter
        # mapeamento direto no SDK — ficam omitidos se não houver suporte.

        chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_ocid)
        chat_detail.chat_request = generic
        chat_detail.compartment_id = compartment_id

        chat_response = client.chat(chat_detail)
        data = chat_response.data

        # Normalize saída
        if hasattr(data, "chat_response") and data.chat_response and data.chat_response.choices:
            choice = data.chat_response.choices[0]
            # Tenta pegar o texto do primeiro bloco
            text = None
            if choice.message and choice.message.content:
                if hasattr(choice.message.content[0], "text"):
                    text = choice.message.content[0].text
            return {"output_text": text, "raw": "sdk"}
        # fallback
        return {"output_text": None, "raw": "unknown"}
    except Exception as e:
        return {"error": f"Falha ao chamar OCI: {e}"}

def to_openai_chat_response(model_label: str, content_text: str, finish_reason: str = "stop") -> Dict[str, Any]:
    now = int(time.time())
    rid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    return {
        "id": rid,
        "object": "chat.completion",
        "created": now,
        "model": model_label,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content_text},
                "finish_reason": finish_reason
            }
        ],
        "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    }

def to_openai_text_response(model_label: str, content_text: str, finish_reason: str = "stop") -> Dict[str, Any]:
    now = int(time.time())
    rid = f"cmpl-{uuid.uuid4().hex[:24]}"
    return {
        "id": rid,
        "object": "text_completion",
        "created": now,
        "model": model_label,
        "choices": [
            {"index": 0, "text": content_text, "finish_reason": finish_reason, "logprobs": None}
        ],
        "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    }

def sse_chat_stream(model_label: str, full_text: str) -> Generator[str, None, None]:
    """
    Simula stream de deltas no formato OpenAI.
    """
    rid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    now = int(time.time())
    first = {
        "id": rid, "object": "chat.completion.chunk", "created": now,
        "model": model_label,
        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
    }
    yield f"data: {json.dumps(first)}\n\n"
    for ch in full_text or "":
        chunk = {
            "id": rid, "object": "chat.completion.chunk", "created": now,
            "model": model_label,
            "choices": [{"index": 0, "delta": {"content": ch}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    endchunk = {
        "id": rid, "object": "chat.completion.chunk", "created": now,
        "model": model_label,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
    }
    yield f"data: {json.dumps(endchunk)}\n\n"
    yield "data: [DONE]\n\n"

# ==========================
# Segurança
# ==========================

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

# ==========================
# Endpoints existentes (mantidos)
# ==========================

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
    data = request.get_json() or {}
    # DEBUG:
    print(">>> /genai-agent/.../session payload recebido:")
    #print(data)
    channel = data.get("channel")
    cuid = data.get("cuid")
    if not all([channel, cuid]):
        return jsonify({"error": "Parâmetros 'channel' e 'cuid' são obrigatórios"}), 400
    response_data = session_controller(region, agent_endpoint_id, channel, cuid)
    return jsonify(response_data)

@app.route("/genai-agent/<region>/<agent_endpoint_id>/<session_id>/chat", methods=["POST"])
def agent_chat(region, agent_endpoint_id, session_id):
    data = request.get_json() or {}
    # DEBUG:
    print(">>> /genai-agent/.../chat payload recebido:")
    #print(data)
    user_message = data.get("userMessage")
    if not user_message:
        return jsonify({"error": "userMessage é obrigatório"}), 400
    response_data = ask_agent(region, agent_endpoint_id, session_id, user_message)
    return jsonify({"agentResponse": response_data})

@app.route("/genai/<region>/<compartment_id>/<model_id>/inference", methods=["POST"])
def inference(region, compartment_id, model_id):
    data = request.get_json() or {}
    # DEBUG:
    print(">>> /inference request body:")
    #print(data)
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400
    response_data = call_inference_model(region, compartment_id, model_id, prompt)
    return jsonify(response_data)

# ==========================
# Novos endpoints — OpenAI v1 compat
# ==========================

@app.route("/genai/<region>/<compartment_id>/<path_model_id>/v1/chat/completions", methods=["POST"])
def v1_chat_completions(region, compartment_id, path_model_id):
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        return jsonify({"error": f"JSON inválido: {e}"}), 400

    # DEBUG: imprimir o que chegou
    print(">>> /v1/chat/completions body recebido:")
    print(body)

    try:
        resolved = resolve_model_and_params(body, path_model_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    model_label = body.get("model") or resolved["model_key"] or resolved["model_ocid"]
    msgs = body.get("messages") or []
    if not isinstance(msgs, list) or not msgs:
        return jsonify({"error": "Campo 'messages' é obrigatório e deve ser uma lista."}), 400

    oci_msgs = to_oci_messages(msgs)
    oci_payload = build_oci_chat_payload(oci_msgs, resolved["params"])

    oci_result = oci_chat_invoke(region, compartment_id, resolved["model_ocid"], oci_payload)
    if isinstance(oci_result, dict):
        output_text = (
            oci_result.get("output_text")
            or oci_result.get("generated_text")
            or oci_result.get("inference_response", {}).get("output_text")
            or oci_result.get("payload", {}).get("output_text")  # dry-run
        )
    else:
        output_text = None

    if output_text is None:
        output_text = json.dumps(oci_result, ensure_ascii=False)

    if body.get("stream") is True:
        return Response(stream_with_context(sse_chat_stream(model_label, output_text)),
                        mimetype="text/event-stream")

    return jsonify(to_openai_chat_response(model_label, output_text))

@app.route("/genai/<region>/<compartment_id>/<path_model_id>/v1/completions", methods=["POST"])
def v1_text_completions(region, compartment_id, path_model_id):
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        return jsonify({"error": f"JSON inválido: {e}"}), 400

    # DEBUG:
    print(">>> /v1/completions body recebido:")
    print(body)

    try:
        resolved = resolve_model_and_params(body, path_model_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    model_label = body.get("model") or resolved["model_key"] or resolved["model_ocid"]
    prompt = body.get("prompt")
    if prompt is None:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400

    # Compat: empacotar como chat com 1 mensagem user
    if isinstance(prompt, list):
        prompt_text = "\n".join([str(p) for p in prompt])
    else:
        prompt_text = str(prompt)

    msgs = [{"role": "user", "content": prompt_text}]
    oci_msgs = to_oci_messages(msgs)
    oci_payload = build_oci_chat_payload(oci_msgs, resolved["params"])

    oci_result = oci_chat_invoke(region, compartment_id, resolved["model_ocid"], oci_payload)
    if isinstance(oci_result, dict):
        output_text = (
            oci_result.get("output_text")
            or oci_result.get("generated_text")
            or oci_result.get("inference_response", {}).get("output_text")
            or oci_result.get("payload", {}).get("output_text")
        )
    else:
        output_text = None

    if output_text is None:
        output_text = json.dumps(oci_result, ensure_ascii=False)

    if body.get("stream") is True:
        return Response(stream_with_context(sse_chat_stream(model_label, output_text)),
                        mimetype="text/event-stream")

    return jsonify(to_openai_text_response(model_label, output_text))

# ==========================
# Main
# ==========================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
