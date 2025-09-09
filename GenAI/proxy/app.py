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
# Modelos suportados
# --------------------------

SUPPORTED_MODELS = {
    "gpt5": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyasebknceb4ekbiaiisjtu3fj5i7s4io3ignvg4ip2uyma",
    "grok3mini": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyavwbgai5nlntsd5hngaileroifuoec5qxttmydhq7mykq",
    "llama4maverick": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyayjawvuonfkw2ua4bob4rlnnlhs522pafbglivtwlfzta"
}

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

def call_inference_model(region, compartment_id, model_id, prompt, **kwargs):
    if TEST_MODE:
        return {"response": {"text": f"Resposta simulada: {prompt}", "finish_reason": "stop"}}

    if model_id not in SUPPORTED_MODELS.values():
        return {"error": "Modelo não implementado"}

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
            max_tokens=kwargs.get("max_tokens", 600),
            temperature=kwargs.get("temperature", 1),
            top_p=kwargs.get("top_p", 1),
            top_k=kwargs.get("top_k", 0),
            frequency_penalty=kwargs.get("frequency_penalty", 0),
            presence_penalty=kwargs.get("presence_penalty", 0)
        )

        if model_id == SUPPORTED_MODELS["gpt5"]:
            chat_request.reasoning_effort = kwargs.get("reasoning_effort", "MEDIUM")
            chat_request.verbosity = kwargs.get("verbosity", "MEDIUM")

        chat_detail = oci.generative_ai_inference.models.ChatDetails(
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_id),
            chat_request=chat_request,
            compartment_id=compartment_id
        )

        chat_response = generative_ai_inference_client.chat(chat_detail)
        choice = chat_response.data.chat_response.choices[0]

        return {
            "response": {
                "text": choice.message.content[0].text,
                "finish_reason": choice.finish_reason
            }
        }

    except Exception as e:
        return {"error": str(e)}
