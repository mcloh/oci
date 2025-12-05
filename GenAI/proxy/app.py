# api.py — OCI GenAI + OpenAI v1 Compatibility (files + images + multimodal)
# -----------------------------------------------------------------------------
# Requisitos:
#   pip install flask oci requests pillow flask-cors
# Execução:
#   export API_KEY="minha-chave"
#   export GENAI_BUCKET="lohmann-ai-br"
#   export GENAI_UPLOAD_PREFIX="genai-uploads/"
#   export OCI_CONFIG_FILE="./credentials.conf"  # opcional, padrão: ./credentials.conf
#   export LLM_CONFIG_PATH="./llm_models.json"    # opcional, padrão: ./llm_models.json
#   export DEBUG_AUTH=true                        # opcional
#   python app.py  # porta 8000
# -----------------------------------------------------------------------------

from flask import Flask, request, jsonify, abort, Response, stream_with_context, send_file
import oci
import requests
import os
import io
import json
import uuid
import base64
import time
import mimetypes
import hmac
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Generator
from functools import lru_cache, wraps

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==========================
# CORS (habilita para OpenWebUI e browsers)
# ==========================

try:
    from flask_cors import CORS
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Channel", "X-Cuid"],
        expose_headers=["Content-Type", "Authorization", "X-API-Key"],
        methods=["GET", "POST", "OPTIONS"]
    )
except Exception as _e:
    logger.warning("flask-cors não instalado; CORS mínimo será aplicado via after_request.")

@app.after_request
def add_cors_headers(resp):
    resp.headers.setdefault("Access-Control-Allow-Origin", "*")
    resp.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key, X-Channel, X-Cuid")
    return resp

# ==========================
# Constantes de Parâmetros de Modelo
# ==========================

# Parâmetros de modelo com mapeamento 1:1 (sem transformação)
SIMPLE_MODEL_PARAMS = [
    "temperature",
    "top_p",
    "top_k",
    "frequency_penalty",
    "presence_penalty",
    "reasoning_effort",
    "verbosity"
]

# ==========================
# Configuração e Autenticação OCI
# ==========================

def load_config(config_file=None):
    """Carrega configuração OCI de arquivo.
    
    Args:
        config_file: Caminho do arquivo de configuração. Se None, usa variável de ambiente OCI_CONFIG_FILE
                     ou padrão './credentials.conf'
    """
    if config_file is None:
        config_file = os.environ.get("OCI_CONFIG_FILE", "./credentials.conf")
    
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
        logger.error(f"Erro ao inicializar signer OCI: {e}")
        logger.info("Executando em modo de teste...")
        TEST_MODE = True

# ==========================
# Segurança API
# ==========================

DEBUG_AUTH = os.environ.get("DEBUG_AUTH", "false").lower() == "true"

def _safe_equals(a: str, b: str) -> bool:
    if a is None or b is None:
        return False
    return hmac.compare_digest(a, b)

def _parse_bearer_token(auth_header: str) -> str:
    if not auth_header:
        return ""
    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() in ("bearer", "token"):
        return parts[1]
    return ""

def check_api_key():
    expected_key = os.environ.get("API_KEY")
    if not expected_key:
        logger.warning("API_KEY não configurada nas variáveis de ambiente.")
        return

    provided_key = request.headers.get("X-API-Key")
    auth_header = request.headers.get("Authorization")
    bearer_token = _parse_bearer_token(auth_header)

    if DEBUG_AUTH:
        logger.debug(f"[auth] method={request.method} path={request.path} "
              f"X-API-Key={'<set>' if provided_key else '<none>'} "
              f"Authorization={'<set>' if auth_header else '<none>'}")

    if _safe_equals(provided_key, expected_key) or _safe_equals(bearer_token, expected_key):
        return

    abort(401, description="Credenciais inválidas ou ausentes. Use X-API-Key ou Authorization: Bearer.")

@app.before_request
def before_all_requests():
    if request.method == "OPTIONS":
        return "", 204
    check_api_key()

# ==========================
# Variáveis de Bucket / Uploads
# ==========================

BUCKET_NAME = os.environ.get("GENAI_BUCKET", "lohmann-ai-br")
UPLOAD_PREFIX = os.environ.get("GENAI_UPLOAD_PREFIX", "genai-uploads/")
if UPLOAD_PREFIX and not UPLOAD_PREFIX.endswith("/"):
    UPLOAD_PREFIX += "/"

object_client = None
namespace = None
region = config.get("region") or os.environ.get("OCI_REGION", "us-chicago-1")

if not TEST_MODE:
    try:
        object_client = oci.object_storage.ObjectStorageClient(config)
        namespace = object_client.get_namespace().data
    except Exception as e:
        logger.error(f"Erro ao inicializar ObjectStorageClient: {e}")
        TEST_MODE = True

FILE_INDEX: Dict[str, str] = {}

# ==========================
# Cache de Clientes OCI
# ==========================

@lru_cache(maxsize=10)
def get_oci_inference_client(region: str) -> 'oci.generative_ai_inference.GenerativeAiInferenceClient':
    """Retorna cliente OCI GenAI Inference com cache"""
    endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"
    return oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=config,
        service_endpoint=endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240)
    )

# ==========================
# Helpers: Signed URL (PAR) + Upload
# ==========================

def guess_mime(filename: str, default: str = "application/octet-stream") -> str:
    mt, _ = mimetypes.guess_type(filename)
    return mt or default

def create_par_for_object(object_name: str, hours_valid: int = 1, model_region: str = None) -> str:
    """Cria PAR para leitura do objeto"""
    target_region = model_region or region
    if TEST_MODE:
        return f"https://objectstorage.{target_region}.oraclecloud.com/test/{object_name}"
    expires = datetime.utcnow() + timedelta(hours=hours_valid)
    details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name=f"par-{uuid.uuid4().hex[:8]}",
        access_type="ObjectRead",
        time_expires=expires,
        bucket_listing_action=None,
        object_name=object_name
    )
    par = object_client.create_preauthenticated_request(
        namespace_name=namespace,
        bucket_name=BUCKET_NAME,
        create_preauthenticated_request_details=details
    ).data
    base = f"https://objectstorage.{target_region}.oraclecloud.com"
    return base + par.access_uri

def upload_file_to_bucket(file_storage, filename: str) -> Dict[str, Any]:
    """Upload de arquivo para bucket com PAR"""
    file_storage.stream.seek(0)
    content = file_storage.read()
    size = len(content)
    if TEST_MODE:
        file_id = f"file-{uuid.uuid4().hex[:12]}"
        url = f"https://objectstorage.{region}.oraclecloud.com/test/{UPLOAD_PREFIX}{file_id}_{filename}"
        FILE_INDEX[file_id] = f"{UPLOAD_PREFIX}{file_id}_{filename}"
        return {"id": file_id, "object": "file", "filename": filename, "bytes": size, "url": url}

    object_name = f"{UPLOAD_PREFIX}{uuid.uuid4().hex}_{filename}"
    object_client.put_object(
        namespace,
        BUCKET_NAME,
        object_name,
        content,
        content_type=guess_mime(filename, "application/octet-stream")
    )
    url = create_par_for_object(object_name, hours_valid=24)
    file_id = f"file-{uuid.uuid4().hex[:12]}"
    FILE_INDEX[file_id] = object_name
    return {"id": file_id, "object": "file", "filename": filename, "bytes": size, "url": url}

# ==========================
# Modelos — JSON externo (hot-reload) 
# ==========================

LLM_CONFIG_PATH = os.environ.get("LLM_CONFIG_PATH", "./llm_models.json")

SUPPORTED_MODELS_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "gpt5": {
        "id": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyasebknceb4ekbiaiisjtu3fj5i7s4io3ignvg4ip2uyma",
        "compartmentId": "ocid1.compartment.oc1..aaaaaaaaxxxxxxxxxxx",
        "region": "us-chicago-1",
        "type": "model",
        "params": {"max_completion_tokens": 2048, "reasoning_effort": "MEDIUM", "verbosity": "MEDIUM"}
    },
    "my-agent": {
        "id": "ocid1.genaiagentendpoint.oc1.us-chicago-1.amaaaaaask7dceyasebknceb4ekbiaiisjtu3fj5i7s4io3ignvg4ip2uyma",
        "compartmentId": "ocid1.compartment.oc1..aaaaaaaaxxxxxxxxxxx",
        "region": "us-chicago-1",
        "type": "agent",
        "params": {}
    }
}

def get_supported_models() -> Dict[str, Dict[str, Any]]:
    """Lê JSON de modelos (hot-reload) com suporte a compartmentId, region e type"""
    try:
        with open(LLM_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        models = data.get("models", {})
        valid = {k: v for k, v in models.items() if isinstance(v, dict) and v.get("id")}
        if not valid:
            raise ValueError("Arquivo de modelos não contém 'models' válidos.")
        return valid
    except Exception as e:
        logger.warning(f"Usando SUPPORTED_MODELS_DEFAULTS (motivo: {e})")
        return SUPPORTED_MODELS_DEFAULTS

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Retorna configuração completa de um modelo pelo nome"""
    supported = get_supported_models()
    if model_name not in supported:
        raise ValueError(f"Modelo '{model_name}' não encontrado. Modelos disponíveis: {list(supported.keys())}")
    return supported[model_name]

# ==========================
# Session Store (Agente)
# ==========================

SESSION_STORE = {}
SESSION_TTL = timedelta(hours=2)

def session_controller(region, agent_endpoint_id, channel, cuid):
    """Controla sessões com agente (sliding TTL de 2h)"""
    session_key = f"{channel}:{cuid}"
    now = datetime.utcnow()

    existing = SESSION_STORE.get(session_key)
    if existing:
        last_used = existing["lastUsedAt"]
        if now - last_used < SESSION_TTL:
            existing["lastUsedAt"] = now
            return {"id": existing["sessionId"], "sessionKey": session_key, "reused": True}

    if TEST_MODE:
        new_session_id = f"test_session_{agent_endpoint_id[:8]}_{int(now.timestamp())}"
        SESSION_STORE[session_key] = {
            "sessionId": new_session_id, "createdAt": now, "lastUsedAt": now, "sessionKey": session_key
        }
        logger.info(f"[agent] nova sessão criada (TEST): key={session_key} id={new_session_id}")
        return {"id": new_session_id, "sessionKey": session_key, "reused": False}

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
            "sessionId": data.get("id"), "createdAt": now, "lastUsedAt": now, "sessionKey": session_key
        }
        logger.info(f"[agent] nova sessão criada: key={session_key} id={data.get('id')}")
        data["sessionKey"] = session_key
        data["reused"] = False
        return data
    except Exception as e:
        return {"error": str(e), "sessionKey": session_key}

def _invalidate_session(session_key: str):
    try:
        if session_key in SESSION_STORE:
            del SESSION_STORE[session_key]
            logger.info(f"[agent] sessão invalidada: key={session_key}")
    except Exception:
        pass

def ask_agent(region, agent_endpoint_id, session_id, user_message):
    """Envia mensagem para agente OCI"""
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
    payload = {"userMessage": user_message, "shouldStream": False, "sessionId": session_id}

    try:
        response = session.post(chat_url, json=payload)
        status = response.status_code
        text_body = None
        try:
            json_body = response.json()
        except Exception:
            json_body = None
            text_body = response.text

        if 200 <= status < 300:
            return json_body if json_body is not None else {"message": text_body or ""}
        else:
            return {"_http_status": status, "_raw_text": text_body, "_raw_json": json_body}
    except Exception as e:
        return {"_http_status": 0, "error": f"Falha de rede ao chamar Agent: {e}"}

# ==========================
# Utilitários OpenAI v1
# ==========================

ROLE_MAP = {"system": "SYSTEM", "user": "USER", "assistant": "ASSISTANT"}

def ensure_data_url(image_url: str) -> str:
    """Converte URL de imagem para data URL (base64)"""
    if not image_url or image_url.startswith("data:"):
        return image_url
    try:
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()
        content = resp.content
        mime = resp.headers.get("Content-Type") or guess_mime(image_url, "image/jpeg")
        b64 = base64.b64encode(content).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        logger.warning(f"Falha ao baixar imagem '{image_url}': {e}")
        return image_url

def to_oci_messages(openai_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converte mensagens OpenAI para formato OCI"""
    oci_msgs: List[Dict[str, Any]] = []
    for m in openai_messages:
        role = ROLE_MAP.get(str(m.get("role", "")).lower(), "USER")
        content = m.get("content", "")

        parts: List[Dict[str, Any]] = []
        if isinstance(content, list):
            for p in content:
                if isinstance(p, dict) and p.get("type") == "text":
                    txt = p.get("text", "")
                    if txt:
                        parts.append({"type": "TEXT", "text": txt})
                elif isinstance(p, dict) and p.get("type") == "image_url":
                    url = p.get("image_url", {})
                    if isinstance(url, dict):
                        url = url.get("url", "")
                    if isinstance(url, str) and url:
                        data_url = ensure_data_url(url)
                        parts.append({"type": "IMAGE_URL", "url": data_url})
                elif isinstance(p, str):
                    parts.append({"type": "TEXT", "text": p})
        elif isinstance(content, str):
            parts.append({"type": "TEXT", "text": content})
        else:
            parts.append({"type": "TEXT", "text": json.dumps(content, ensure_ascii=False)})

        oci_msgs.append({"role": role, "content": parts})
    return oci_msgs

def build_oci_chat_payload(messages: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """Constrói payload para OCI Chat API"""
    payload = {"messages": messages}
    
    # Parâmetros simples (mapeamento 1:1)
    for param in SIMPLE_MODEL_PARAMS:
        if param in params:
            payload[param] = params[param]
    
    # Tratamento especial: max_tokens → max_completion_tokens (compatibilidade OpenAI)
    if "max_completion_tokens" in params:
        payload["max_completion_tokens"] = params["max_completion_tokens"]
    elif "max_tokens" in params:
        payload["max_completion_tokens"] = params["max_tokens"]
    
    return payload

def extract_token_usage(oci_response: Any) -> Dict[str, Optional[int]]:
    """Extrai informações de uso de tokens da resposta OCI"""
    usage = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    
    if not oci_response:
        return usage
    
    try:
        # Tenta extrair do objeto data.chat_response
        if hasattr(oci_response, 'data'):
            data = oci_response.data
            if hasattr(data, 'chat_response') and data.chat_response:
                chat_resp = data.chat_response
                # Verifica se há informações de uso
                if hasattr(chat_resp, 'usage') and chat_resp.usage:
                    usage_obj = chat_resp.usage
                    if hasattr(usage_obj, 'prompt_tokens'):
                        usage["prompt_tokens"] = usage_obj.prompt_tokens
                    if hasattr(usage_obj, 'completion_tokens'):
                        usage["completion_tokens"] = usage_obj.completion_tokens
                    if hasattr(usage_obj, 'total_tokens'):
                        usage["total_tokens"] = usage_obj.total_tokens
                    
                    # Se total_tokens não estiver disponível, calcula
                    if usage["total_tokens"] is None and usage["prompt_tokens"] and usage["completion_tokens"]:
                        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    except Exception as e:
        logger.warning(f"Erro ao extrair token usage: {e}")
    
    return usage

def extract_agent_token_usage(agent_response):
    """
    Extrai informações de token usage de uma resposta de agente OCI.
    Suporta múltiplas etapas de tool calling.
    
    Estrutura esperada:
    {
        "traces": [
            {
                "traceType": "GENERATION_TRACE",
                "usage": [
                    {
                        "usageDetails": {
                            "inputTokenCount": int,
                            "outputTokenCount": int
                        }
                    }
                ]
            }
        ]
    }
    
    Args:
        agent_response: Resposta do agente (dict)
    
    Returns:
        dict: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    """
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    if not agent_response or not isinstance(agent_response, dict):
        return usage
    
    try:
        # Obter traces
        traces = agent_response.get('traces', [])
        
        total_input_tokens = 0
        total_output_tokens = 0
        
        # Iterar por todos os traces
        for trace in traces:
            # Verificar se é um GENERATION_TRACE (pode vir como traceType ou trace_type)
            trace_type = trace.get('traceType') or trace.get('trace_type', '')
            
            if trace_type == 'GENERATION_TRACE':
                # Obter lista de usage
                usage_list = trace.get('usage', [])
                
                # Iterar por cada entrada de usage
                for usage_entry in usage_list:
                    # Obter usageDetails (pode vir como usageDetails ou usage_details)
                    usage_details = usage_entry.get('usageDetails') or usage_entry.get('usage_details', {})
                    
                    # Extrair contagens (pode vir em camelCase ou snake_case)
                    input_tokens = (
                        usage_details.get('inputTokenCount') or 
                        usage_details.get('input_token_count', 0)
                    )
                    output_tokens = (
                        usage_details.get('outputTokenCount') or 
                        usage_details.get('output_token_count', 0)
                    )
                    
                    total_input_tokens += input_tokens
                    total_output_tokens += output_tokens
        
        # Atualizar usage com os totais
        usage["prompt_tokens"] = total_input_tokens
        usage["completion_tokens"] = total_output_tokens
        usage["total_tokens"] = total_input_tokens + total_output_tokens
        
    except Exception as e:
        logger.warning(f"Erro ao extrair token usage de agente: {e}")
    
    return usage

def oci_chat_invoke(model_region: str, compartment_id: str, model_ocid: str, oci_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoca modelo OCI GenAI e retorna resposta com token usage"""
    logger.debug(">>> OCI CHAT REQUEST (payload que será enviado):")
    logger.debug(json.dumps(oci_payload, ensure_ascii=False, indent=2))

    if TEST_MODE:
        return {
            "dry_run": True,
            "note": "TEST_MODE=True — retorno simulado.",
            "payload": oci_payload,
            "output_text": "[dry-run] ambiente de teste — valide o payload impresso no console.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

    try:
        client = get_oci_inference_client(model_region)

        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        generic = oci.generative_ai_inference.models.GenericChatRequest()
        generic.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC

        sdk_messages = []
        for m in oci_payload["messages"]:
            sdk_msg = oci.generative_ai_inference.models.Message()
            sdk_msg.role = m["role"]
            parts = []
            for c in m["content"]:
                ctype = c.get("type")
                if ctype == "TEXT":
                    tc = oci.generative_ai_inference.models.TextContent()
                    tc.text = c.get("text", "")
                    parts.append(tc)
                elif ctype == "IMAGE_URL":
                    ic = oci.generative_ai_inference.models.ImageContent()
                    iu = oci.generative_ai_inference.models.ImageUrl()
                    iu.url = c.get("url", "")
                    ic.image_url = iu
                    parts.append(ic)
            sdk_msg.content = parts
            sdk_messages.append(sdk_msg)

        generic.messages = sdk_messages

        # Parâmetros simples (mapeamento 1:1)
        for param in SIMPLE_MODEL_PARAMS:
            if param in oci_payload:
                setattr(generic, param, oci_payload[param])
        
        # Tratamento especial: max_completion_tokens
        if "max_completion_tokens" in oci_payload:
            generic.max_completion_tokens = oci_payload["max_completion_tokens"]

        chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_ocid)
        chat_detail.chat_request = generic
        chat_detail.compartment_id = compartment_id

        chat_response = client.chat(chat_detail)
        data = chat_response.data

        output_text = None
        if hasattr(data, "chat_response") and data.chat_response and data.chat_response.choices:
            choice = data.chat_response.choices[0]
            if choice.message and choice.message.content:
                for block in choice.message.content:
                    if hasattr(block, "text") and block.text:
                        output_text = block.text
                        break

        # Extrai informações de token usage
        usage = extract_token_usage(chat_response)

        return {"output_text": output_text, "usage": usage, "raw": "sdk"}
    except Exception as e:
        return {"error": f"Falha ao chamar OCI: {e}", "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}}

def to_openai_chat_response(model_label: str, content_text: str, usage: Dict[str, Optional[int]] = None, finish_reason: str = "stop") -> Dict[str, Any]:
    """Formata resposta no padrão OpenAI Chat Completion"""
    now = int(time.time())
    rid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    
    if usage is None:
        usage = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    
    return {
        "id": rid,
        "object": "chat.completion",
        "created": now,
        "model": model_label,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content_text},
            "finish_reason": finish_reason
        }],
        "usage": usage
    }

def to_openai_text_response(model_label: str, content_text: str, usage: Dict[str, Optional[int]] = None, finish_reason: str = "stop") -> Dict[str, Any]:
    """Formata resposta no padrão OpenAI Text Completion"""
    now = int(time.time())
    rid = f"cmpl-{uuid.uuid4().hex[:24]}"
    
    if usage is None:
        usage = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    
    return {
        "id": rid,
        "object": "text_completion",
        "created": now,
        "model": model_label,
        "choices": [{
            "index": 0,
            "text": content_text,
            "finish_reason": finish_reason,
            "logprobs": None
        }],
        "usage": usage
    }

def sse_chat_stream(model_label: str, full_text: str) -> Generator[str, None, None]:
    """Gera stream SSE para chat completion"""
    rid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    now = int(time.time())
    first = {
        "id": rid,
        "object": "chat.completion.chunk",
        "created": now,
        "model": model_label,
        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
    }
    yield f"data: {json.dumps(first)}\n\n"
    
    for ch in full_text or "":
        chunk = {
            "id": rid,
            "object": "chat.completion.chunk",
            "created": now,
            "model": model_label,
            "choices": [{"index": 0, "delta": {"content": ch}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    
    endchunk = {
        "id": rid,
        "object": "chat.completion.chunk",
        "created": now,
        "model": model_label,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
    }
    yield f"data: {json.dumps(endchunk)}\n\n"
    yield "data: [DONE]\n\n"

# ==========================
# Helpers para extração de texto de Agents
# ==========================

def _coerce_to_text(val: Any) -> str:
    """Converte valor para texto, tentando extrair de estruturas aninhadas"""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    
    # Se for lista, tenta extrair texto do primeiro elemento
    if isinstance(val, list):
        for item in val:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                return item["text"]
            elif isinstance(item, str):
                return item
        # Se não encontrou texto, tenta recursivamente
        for item in val:
            txt = _coerce_to_text(item)
            if txt and not txt.startswith('{'):
                return txt
    
    try:
        if isinstance(val, dict):
            # Tenta extrair de campos comuns
            if isinstance(val.get("text"), str):
                return val["text"]
            if isinstance(val.get("content"), str):
                return val["content"]
            if isinstance(val.get("content"), dict) and isinstance(val["content"].get("text"), str):
                return val["content"]["text"]
            if isinstance(val.get("content"), list):
                for c in val["content"]:
                    if isinstance(c, dict) and isinstance(c.get("text"), str):
                        return c["text"]
            # Tenta extrair de data
            data = val.get("data")
            if isinstance(data, dict):
                for key in ("message", "output", "text"):
                    if isinstance(data.get(key), str):
                        return data[key]
                if isinstance(data.get("content"), dict) and isinstance(data["content"].get("text"), str):
                    return data["content"]["text"]
                if isinstance(data.get("content"), list):
                    for c in data["content"]:
                        if isinstance(c, dict) and isinstance(c.get("text"), str):
                            return c["text"]
        return json.dumps(val, ensure_ascii=False)
    except Exception:
        return str(val)

def _extract_agent_text(agent_payload: Any) -> str:
    """
    Extrai o texto principal de respostas de GenAI Agent em diferentes formatos,
    incluindo {"role":"AGENT","content":{"text":"..."}}.
    """
    if agent_payload is None:
        return ""
    if isinstance(agent_payload, str):
        try:
            maybe_json = json.loads(agent_payload)
            return _extract_agent_text(maybe_json)
        except Exception:
            return agent_payload

    if isinstance(agent_payload, dict):
        # Tenta extrair de campos candidatos na ordem de prioridade
        candidates = [
            agent_payload.get("message"),
            agent_payload.get("output"),
            agent_payload.get("text"),
            agent_payload.get("content"),
            agent_payload.get("data"),
            agent_payload.get("result"),
        ]
        for c in candidates:
            if c is not None:
                txt = _coerce_to_text(c)
                if txt:
                    return txt
        return _coerce_to_text(agent_payload)

    return _coerce_to_text(agent_payload)

# ==========================
# Endpoints OpenAI v1 — NOVA ESTRUTURA /genai/{modelname}/v1/...
# ==========================

@app.route("/", methods=["GET"])
def test():
    return jsonify({"test": "ok", "version": "2.0-refactored"})

# ==========================
# Endpoints Globais OpenAI v1 (compatibilidade total com SDK OpenAI)
# ==========================

@app.route("/v1/models", methods=["GET"])
def list_all_models():
    """
    Lista todos os modelos disponíveis.
    Compatível com: OpenAI SDK client.models.list()
    """
    supported = get_supported_models()
    now = int(time.time())
    models_list = []
    
    for name, cfg in supported.items():
        models_list.append({
            "id": name,
            "object": "model",
            "created": now,
            "owned_by": "oci.genai",
            "permission": [],
            "root": name,
            "parent": None,
            "type": cfg.get("type", "model"),
            "region": cfg.get("region"),
            "ocid": cfg.get("id"),
            "compartmentId": cfg.get("compartmentId"),
            "params": cfg.get("params", {})
        })
    
    return jsonify({"object": "list", "data": models_list})

@app.route("/v1/models/<model_id>", methods=["GET"])
def get_model_info(model_id):
    """
    Retorna informações de um modelo específico.
    Compatível com: OpenAI SDK client.models.retrieve(model_id)
    """
    try:
        model_config = get_model_config(model_id)
        return jsonify({
            "id": model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "oci.genai",
            "permission": [],
            "root": model_id,
            "parent": None,
            "ocid": model_config.get("id"),
            "compartmentId": model_config.get("compartmentId"),
            "region": model_config.get("region"),
            "type": model_config.get("type", "model"),
            "params": model_config.get("params", {})
        })
    except ValueError as e:
        return jsonify({"error": {"message": str(e), "type": "invalid_request_error", "code": "model_not_found"}}), 404

@app.route("/v1/chat/completions", methods=["POST"])
def global_chat_completions():
    """
    Chat completion global.
    Compatível com: OpenAI SDK client.chat.completions.create()
    """
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        return jsonify({"error": {"message": f"JSON inválido: {e}", "type": "invalid_request_error"}}), 400

    model_name = body.get("model")
    if not model_name:
        return jsonify({"error": {"message": "Campo 'model' é obrigatório", "type": "invalid_request_error", "param": "model"}}), 400

    try:
        model_config = get_model_config(model_name)
    except ValueError as e:
        return jsonify({"error": {"message": str(e), "type": "invalid_request_error", "code": "model_not_found"}}), 404

    # Redireciona para a lógica existente baseado no tipo
    if model_config.get("type") == "agent":
        return _handle_agent_chat(model_name, model_config, body)
    
    # Lógica para modelos
    msgs = body.get("messages") or []
    if not isinstance(msgs, list) or not msgs:
        return jsonify({"error": {"message": "Campo 'messages' é obrigatório e deve ser uma lista", "type": "invalid_request_error", "param": "messages"}}), 400

    params = model_config.get("params", {}).copy()
    for k in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", 
              "presence_penalty", "reasoning_effort", "verbosity", "max_completion_tokens"]:
        if k in body and body[k] is not None:
            params[k] = body[k]

    oci_msgs = to_oci_messages(msgs)
    oci_payload = build_oci_chat_payload(oci_msgs, params)
    
    model_region = model_config.get("region")
    compartment_id = model_config.get("compartmentId")
    model_ocid = model_config.get("id")
    
    oci_result = oci_chat_invoke(model_region, compartment_id, model_ocid, oci_payload)

    if isinstance(oci_result, dict):
        output_text = oci_result.get("output_text")
        usage = oci_result.get("usage", {})
    else:
        output_text = None
        usage = {}

    if output_text is None:
        output_text = json.dumps(oci_result, ensure_ascii=False)

    if body.get("stream") is True:
        return Response(
            stream_with_context(sse_chat_stream(model_name, output_text)),
            mimetype="text/event-stream"
        )

    return jsonify(to_openai_chat_response(model_name, output_text, usage))

@app.route("/v1/completions", methods=["POST"])
def global_text_completions():
    """
    Text completion global.
    Compatível com: OpenAI SDK client.completions.create()
    """
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        return jsonify({"error": {"message": f"JSON inválido: {e}", "type": "invalid_request_error"}}), 400

    model_name = body.get("model")
    if not model_name:
        return jsonify({"error": {"message": "Campo 'model' é obrigatório", "type": "invalid_request_error", "param": "model"}}), 400

    try:
        model_config = get_model_config(model_name)
    except ValueError as e:
        return jsonify({"error": {"message": str(e), "type": "invalid_request_error", "code": "model_not_found"}}), 404

    # Redireciona para a lógica existente baseado no tipo
    if model_config.get("type") == "agent":
        return _handle_agent_completion(model_name, model_config, body)
    
    # Lógica para modelos
    prompt = body.get("prompt")
    if not prompt:
        return jsonify({"error": {"message": "Campo 'prompt' é obrigatório", "type": "invalid_request_error", "param": "prompt"}}), 400

    params = model_config.get("params", {}).copy()
    for k in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", "presence_penalty"]:
        if k in body and body[k] is not None:
            params[k] = body[k]

    # Converte prompt para formato de mensagem
    msgs = [{"role": "USER", "content": [{"type": "TEXT", "text": str(prompt)}]}]
    oci_payload = build_oci_chat_payload(msgs, params)
    
    model_region = model_config.get("region")
    compartment_id = model_config.get("compartmentId")
    model_ocid = model_config.get("id")
    
    oci_result = oci_chat_invoke(model_region, compartment_id, model_ocid, oci_payload)

    if isinstance(oci_result, dict):
        output_text = oci_result.get("output_text")
        usage = oci_result.get("usage", {})
    else:
        output_text = None
        usage = {}

    if output_text is None:
        output_text = json.dumps(oci_result, ensure_ascii=False)

    if body.get("stream") is True:
        return Response(
            stream_with_context(sse_chat_stream(model_name, output_text)),
            mimetype="text/event-stream"
        )

    return jsonify(to_openai_text_response(model_name, output_text, usage))

# ==========================
# Endpoints OpenAI v1 — ESTRUTURA /genai/{modelname}/v1/...
# ==========================

@app.route("/genai/<model_name>/v1/models", methods=["GET"])
def v1_models(model_name):
    """
    Retorna informações do modelo específico (não mais lista completa).
    Compatível com OpenAI /v1/models/{model_id}
    """
    try:
        model_config = get_model_config(model_name)
        return jsonify({
            "id": model_name,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "oci.genai",
            "permission": [],
            "root": model_name,
            "parent": None,
            "ocid": model_config.get("id"),
            "compartmentId": model_config.get("compartmentId"),
            "region": model_config.get("region"),
            "type": model_config.get("type", "model"),
            "params": model_config.get("params", {})
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route("/genai/<model_name>/v1/chat/completions", methods=["POST"])
def v1_chat_completions(model_name):
    """
    Chat completion com nova estrutura de URL.
    Suporta tanto models quanto agents baseado no atributo 'type' do JSON.
    """
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        return jsonify({"error": f"JSON inválido: {e}"}), 400

    logger.debug(f">>> /genai/{model_name}/v1/chat/completions body recebido:")
    logger.debug(json.dumps(body, ensure_ascii=False, indent=2))

    try:
        model_config = get_model_config(model_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    model_type = model_config.get("type", "model")
    model_region = model_config.get("region")
    compartment_id = model_config.get("compartmentId")
    model_ocid = model_config.get("id")

    # Se for agent, delega para função específica
    if model_type == "agent":
        return _handle_agent_chat(model_name, model_config, body)

    # Caso contrário, trata como model
    msgs = body.get("messages") or []
    if not isinstance(msgs, list) or not msgs:
        return jsonify({"error": "Campo 'messages' é obrigatório e deve ser uma lista."}), 400

    # Mescla parâmetros do JSON com overrides do body
    params = model_config.get("params", {}).copy()
    for k in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", 
              "presence_penalty", "reasoning_effort", "verbosity", "max_completion_tokens"]:
        if k in body and body[k] is not None:
            params[k] = body[k]

    oci_msgs = to_oci_messages(msgs)
    oci_payload = build_oci_chat_payload(oci_msgs, params)
    oci_result = oci_chat_invoke(model_region, compartment_id, model_ocid, oci_payload)

    if isinstance(oci_result, dict):
        output_text = oci_result.get("output_text")
        usage = oci_result.get("usage", {})
    else:
        output_text = None
        usage = {}

    if output_text is None:
        output_text = json.dumps(oci_result, ensure_ascii=False)

    if body.get("stream") is True:
        return Response(
            stream_with_context(sse_chat_stream(model_name, output_text)),
            mimetype="text/event-stream"
        )

    return jsonify(to_openai_chat_response(model_name, output_text, usage))

def _handle_agent_chat(model_name: str, model_config: Dict[str, Any], body: Dict[str, Any]) -> Response:
    """Handler específico para agents"""
    model_region = model_config.get("region")
    agent_endpoint_id = model_config.get("id")
    
    msgs = body.get("messages") or []
    if not isinstance(msgs, list) or not msgs:
        return jsonify({"error": "Campo 'messages' é obrigatório e deve ser uma lista."}), 400

    # Extrai texto das mensagens
    user_text = ""
    for m in msgs:
        content = m.get("content", "")
        if isinstance(content, str):
            user_text += content + "\n"
        elif isinstance(content, list):
            for p in content:
                if isinstance(p, dict) and p.get("type") == "text":
                    user_text += p.get("text", "") + "\n"

    user_text = user_text.strip()
    if not user_text:
        return jsonify({"error": "Nenhum conteúdo textual encontrado nas mensagens"}), 400

    # Gerencia sessão automaticamente
    channel = request.headers.get("X-Channel") or "openai-v1"
    cuid = request.headers.get("X-Cuid")
    if not cuid:
        seed = request.headers.get("Authorization") or request.headers.get("X-API-Key") or uuid.uuid4().hex
        cuid = uuid.uuid5(uuid.NAMESPACE_OID, seed).hex

    sess = session_controller(model_region, agent_endpoint_id, channel, cuid)
    if "error" in sess:
        return jsonify({"error": f"Falha ao criar sessão: {sess['error']}"}), 500

    session_id = sess["id"]
    
    # Chama agente
    agent_resp = ask_agent(model_region, agent_endpoint_id, session_id, user_text)
    
    # Verifica erros HTTP
    if isinstance(agent_resp, dict) and "_http_status" in agent_resp:
        status = agent_resp["_http_status"]
        if status == 409:
            # Sessão inválida, invalida e tenta novamente
            _invalidate_session(sess.get("sessionKey", ""))
            sess = session_controller(model_region, agent_endpoint_id, channel, cuid)
            if "error" not in sess:
                session_id = sess["id"]
                agent_resp = ask_agent(model_region, agent_endpoint_id, session_id, user_text)

    # Extrai texto da resposta usando função auxiliar
    response_text = _extract_agent_text(agent_resp)

    # Streaming
    if body.get("stream") is True:
        return Response(
            stream_with_context(sse_chat_stream(model_name, response_text)),
            mimetype="text/event-stream"
        )

    # Extrair token usage da resposta do agente
    usage = extract_agent_token_usage(agent_resp)
    resp = to_openai_chat_response(model_name, response_text, usage)
    resp["_agent"] = {"session_id": session_id, "reused": sess.get("reused", False)}
    return jsonify(resp)

def _handle_agent_completion(model_name: str, model_config: Dict[str, Any], body: Dict[str, Any]) -> Response:
    """Handler específico para agents em /v1/completions"""
    model_region = model_config.get("region")
    agent_endpoint_id = model_config.get("id")
    
    prompt = body.get("prompt")
    if prompt is None:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400
    
    # Converte prompt para texto
    prompt_text = "\n".join([str(p) for p in prompt]) if isinstance(prompt, list) else str(prompt)
    
    if not prompt_text.strip():
        return jsonify({"error": "Prompt não pode estar vazio"}), 400
    
    # Gerencia sessão automaticamente (com fallback se não houver suporte)
    channel = request.headers.get("X-Channel") or "openai-v1-completion"
    cuid = request.headers.get("X-Cuid")
    if not cuid:
        seed = request.headers.get("Authorization") or request.headers.get("X-API-Key") or uuid.uuid4().hex
        cuid = uuid.uuid5(uuid.NAMESPACE_OID, seed).hex
    
    # Tenta criar/obter sessão
    sess = session_controller(model_region, agent_endpoint_id, channel, cuid)
    session_id = None
    session_error = False
    
    if "error" in sess:
        # Se falhar ao criar sessão, tenta continuar sem sessão (alguns agents não precisam)
        logger.warning(f"Falha ao criar sessão para agent: {sess['error']}")
        session_error = True
    else:
        session_id = sess["id"]
    
    # Chama agente (com ou sem session_id)
    if session_id:
        agent_resp = ask_agent(model_region, agent_endpoint_id, session_id, prompt_text)
        
        # Verifica erros HTTP e tenta recuperar
        if isinstance(agent_resp, dict) and "_http_status" in agent_resp:
            status = agent_resp["_http_status"]
            if status == 409:
                # Sessão inválida, invalida e tenta novamente
                _invalidate_session(sess.get("sessionKey", ""))
                sess = session_controller(model_region, agent_endpoint_id, channel, cuid)
                if "error" not in sess:
                    session_id = sess["id"]
                    agent_resp = ask_agent(model_region, agent_endpoint_id, session_id, prompt_text)
                else:
                    # Se ainda falhar, retorna erro
                    return jsonify({"error": f"Falha ao recuperar sessão: {sess['error']}"}), 500
            elif status >= 400:
                # Outros erros HTTP
                error_msg = agent_resp.get("_raw_text") or agent_resp.get("error") or f"HTTP {status}"
                return jsonify({"error": f"Agent retornou erro: {error_msg}"}), 502
    else:
        # Sem sessão - retorna erro informativo
        return jsonify({
            "error": "Agent requer sessão mas falhou ao criar. Use /v1/chat/completions ou configure sessão manualmente."
        }), 500
    
    # Extrai texto da resposta usando função auxiliar
    response_text = _extract_agent_text(agent_resp)
    
    # Streaming
    if body.get("stream") is True:
        return Response(
            stream_with_context(sse_chat_stream(model_name, response_text)),
            mimetype="text/event-stream"
        )
    
    # Extrair token usage da resposta do agente
    usage = extract_agent_token_usage(agent_resp)
    resp = to_openai_text_response(model_name, response_text, usage)
    if session_id:
        resp["_agent"] = {"session_id": session_id, "reused": sess.get("reused", False)}
    return jsonify(resp)

@app.route("/genai/<model_name>/v1/completions", methods=["POST"])
def v1_text_completions(model_name):
    """Text completion (legado OpenAI)"""
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        return jsonify({"error": f"JSON inválido: {e}"}), 400

    logger.debug(f">>> /genai/{model_name}/v1/completions body recebido:")
    logger.debug(json.dumps(body, ensure_ascii=False, indent=2))

    try:
        model_config = get_model_config(model_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    model_type = model_config.get("type", "model")
    
    # Se for agent, delega para função específica
    if model_type == "agent":
        return _handle_agent_completion(model_name, model_config, body)

    model_region = model_config.get("region")
    compartment_id = model_config.get("compartmentId")
    model_ocid = model_config.get("id")

    prompt = body.get("prompt")
    if prompt is None:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400

    prompt_text = "\n".join([str(p) for p in prompt]) if isinstance(prompt, list) else str(prompt)
    msgs = [{"role": "user", "content": prompt_text}]

    # Mescla parâmetros
    params = model_config.get("params", {}).copy()
    for k in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", 
              "presence_penalty", "max_completion_tokens"]:
        if k in body and body[k] is not None:
            params[k] = body[k]

    oci_msgs = to_oci_messages(msgs)
    oci_payload = build_oci_chat_payload(oci_msgs, params)
    oci_result = oci_chat_invoke(model_region, compartment_id, model_ocid, oci_payload)

    if isinstance(oci_result, dict):
        output_text = oci_result.get("output_text")
        usage = oci_result.get("usage", {})
    else:
        output_text = None
        usage = {}

    if output_text is None:
        output_text = json.dumps(oci_result, ensure_ascii=False)

    if body.get("stream") is True:
        return Response(
            stream_with_context(sse_chat_stream(model_name, output_text)),
            mimetype="text/event-stream"
        )

    return jsonify(to_openai_text_response(model_name, output_text, usage))

# ==========================
# Endpoints OpenAI v1 — FILES
# ==========================

@app.route("/genai/<model_name>/v1/files", methods=["POST"])
def v1_files_upload(model_name):
    """Upload de arquivo"""
    if "file" not in request.files:
        return jsonify({"error": "Campo 'file' é obrigatório"}), 400
    f = request.files["file"]
    result = upload_file_to_bucket(f, f.filename)
    return jsonify(result)

@app.route("/genai/<model_name>/v1/files", methods=["GET"])
def v1_files_list(model_name):
    """Lista arquivos"""
    if TEST_MODE:
        return jsonify({"data": [
            {"id": fid, "object": "file", "filename": os.path.basename(obj), "bytes": 0}
            for fid, obj in FILE_INDEX.items()
        ]})
    resp = object_client.list_objects(namespace, BUCKET_NAME, prefix=UPLOAD_PREFIX)
    files = []
    for obj in resp.data.objects:
        files.append({
            "id": f"file-{uuid.uuid4().hex[:12]}",
            "object": "file",
            "filename": obj.name.replace(UPLOAD_PREFIX, ""),
            "bytes": obj.size
        })
    return jsonify({"data": files})

@app.route("/genai/<model_name>/v1/files/<file_id>/content", methods=["GET"])
def v1_files_content(model_name, file_id):
    """Download de arquivo"""
    if TEST_MODE:
        return jsonify({"note": "TEST_MODE — conteúdo não disponível"}), 200
    obj = FILE_INDEX.get(file_id)
    if not obj:
        return jsonify({"error": "file_id não encontrado neste servidor"}), 404
    obj_resp = object_client.get_object(namespace, BUCKET_NAME, obj)
    data = obj_resp.data.content
    filename = os.path.basename(obj)
    return send_file(
        io.BytesIO(data.read()),
        mimetype=guess_mime(filename, "application/octet-stream"),
        as_attachment=False,
        download_name=filename
    )

# ==========================
# Endpoints OpenAI v1 — IMAGES (mock)
# ==========================

def _store_image_bytes_and_return_url(image_bytes: bytes, filename: str, model_region: str = None) -> str:
    """Armazena imagem e retorna URL com PAR"""
    target_region = model_region or region
    if TEST_MODE:
        return f"https://objectstorage.{target_region}.oraclecloud.com/test/{UPLOAD_PREFIX}{uuid.uuid4().hex}_{filename}"
    object_name = f"{UPLOAD_PREFIX}{uuid.uuid4().hex}_{filename}"
    object_client.put_object(
        namespace, BUCKET_NAME, object_name, image_bytes, content_type=guess_mime(filename, "image/png")
    )
    return create_par_for_object(object_name, hours_valid=24, model_region=target_region)

@app.route("/genai/<model_name>/v1/images/generations", methods=["POST"])
def v1_images_generations(model_name):
    """Geração de imagens (mock)"""
    body = request.form or request.get_json(force=True, silent=True) or {}
    prompt = body.get("prompt")
    if not prompt:
        return jsonify({"error": "Campo 'prompt' é obrigatório"}), 400
    
    try:
        model_config = get_model_config(model_name)
        model_region = model_config.get("region")
    except ValueError:
        model_region = None
    
    # Mock: pixel transparente
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHuwKp9w8H2AAAAABJRU5ErkJggg=="
    )
    url = _store_image_bytes_and_return_url(png_bytes, "generation.png", model_region)
    return jsonify({"created": int(time.time()), "data": [{"url": url}]})

@app.route("/genai/<model_name>/v1/images/edits", methods=["POST"])
def v1_images_edits(model_name):
    """Edição de imagens (mock)"""
    if "image" not in request.files:
        return jsonify({"error": "Campo 'image' (multipart) é obrigatório"}), 400
    
    try:
        model_config = get_model_config(model_name)
        model_region = model_config.get("region")
    except ValueError:
        model_region = None
    
    base_img = request.files["image"].read()
    url = _store_image_bytes_and_return_url(base_img, "edit.png", model_region)
    return jsonify({"created": int(time.time()), "data": [{"url": url, "note": "mock edit"}]})

@app.route("/genai/<model_name>/v1/images/variations", methods=["POST"])
def v1_images_variations(model_name):
    """Variações de imagens (mock)"""
    if "image" not in request.files:
        return jsonify({"error": "Campo 'image' (multipart) é obrigatório"}), 400
    
    try:
        model_config = get_model_config(model_name)
        model_region = model_config.get("region")
    except ValueError:
        model_region = None
    
    base_img = request.files["image"].read()
    url = _store_image_bytes_and_return_url(base_img, "variation.png", model_region)
    return jsonify({"created": int(time.time()), "data": [{"url": url, "note": "mock variation"}]})

# ==========================
# Endpoints Diretos OCI (sem camada OpenAI/v1)
# ==========================

@app.route("/genai/<model_name>/session", methods=["POST"])
def oci_session(model_name):
    """
    Gerenciamento de sessão para agents.
    Endpoint direto OCI (sem camada OpenAI/v1).
    """
    try:
        model_config = get_model_config(model_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
    model_type = model_config.get("type", "model")
    if model_type != "agent":
        return jsonify({"error": f"Modelo '{model_name}' não é um agent. Use type='agent' no JSON."}), 400
    
    data = request.get_json() or {}
    logger.debug(f">>> /genai/{model_name}/session payload recebido:")
    logger.debug(json.dumps(data, ensure_ascii=False, indent=2))
    
    channel = data.get("channel")
    cuid = data.get("cuid")
    
    if not all([channel, cuid]):
        return jsonify({"error": "Parâmetros 'channel' e 'cuid' são obrigatórios"}), 400
    
    model_region = model_config.get("region")
    agent_endpoint_id = model_config.get("id")
    
    response_data = session_controller(model_region, agent_endpoint_id, channel, cuid)
    return jsonify(response_data)

def _chat_with_retry_on_session_expired(model_region, agent_endpoint_id, session_id, session_key, user_message):
    """
    Envia mensagem ao agente com retry automático em caso de sessão expirada (409).
    
    Returns:
        tuple: (response_data, session_id, error_response)
        - Se sucesso: (response_data, session_id, None)
        - Se erro: (None, None, error_response)
    """
    # Primeira tentativa
    response_data = ask_agent(model_region, agent_endpoint_id, session_id, user_message)
    
    # Se retornou erro 409 (sessão inválida), tenta recuperar
    if isinstance(response_data, dict) and response_data.get("_http_status") == 409:
        logger.info(f"[chat] Sessão expirou (409), invalidando e recriando...")
        
        # Invalida sessão local
        _invalidate_session(session_key)
        
        # Extrai channel e cuid do session_key
        channel, cuid = session_key.split(":", 1)
        
        # Cria nova sessão
        sess = session_controller(model_region, agent_endpoint_id, channel, cuid)
        
        if "error" in sess:
            return None, None, (jsonify({
                "error": f"Falha ao recriar sessão após erro 409: {sess.get('error')}",
                "details": sess
            }), 500)
        
        new_session_id = sess.get("id")
        
        # Retry com nova sessão
        response_data = ask_agent(model_region, agent_endpoint_id, new_session_id, user_message)
        
        # Se ainda falhou, retorna erro
        if isinstance(response_data, dict) and response_data.get("_http_status") == 409:
            return None, None, (jsonify({
                "error": "Falha persistente de sessão após retry",
                "details": response_data
            }), 500)
        
        return response_data, new_session_id, None
    
    return response_data, session_id, None

@app.route("/genai/<model_name>/chat", methods=["POST"])
def oci_chat(model_name):
    """
    Chat direto com agent com gerenciamento automático de sessão.
    
    Aceita dois modos:
    1. Com sessionId (modo manual): {"sessionId": "...", "userMessage": "..."}
    2. Com channel/cuid (modo automático): {"channel": "...", "cuid": "...", "userMessage": "..."}
    
    No modo automático, a sessão é gerenciada automaticamente com retry em caso de erro.
    Endpoint direto OCI (sem camada OpenAI/v1).
    """
    try:
        model_config = get_model_config(model_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
    model_type = model_config.get("type", "model")
    if model_type != "agent":
        return jsonify({"error": f"Modelo '{model_name}' não é um agent. Use type='agent' no JSON."}), 400
    
    data = request.get_json() or {}
    logger.debug(f">>> /genai/{model_name}/chat payload recebido:")
    logger.debug(json.dumps(data, ensure_ascii=False, indent=2))
    
    user_message = data.get("userMessage")
    if not user_message:
        return jsonify({"error": "Parâmetro 'userMessage' é obrigatório"}), 400
    
    model_region = model_config.get("region")
    agent_endpoint_id = model_config.get("id")
    
    # Modo 1: sessionId fornecido manualmente
    session_id = data.get("sessionId")
    
    # Modo 2: channel/cuid fornecidos (gerenciamento automático)
    channel = data.get("channel")
    cuid = data.get("cuid")
    
    # Valida que pelo menos um modo foi fornecido
    if not session_id and not (channel and cuid):
        return jsonify({
            "error": "Forneça 'sessionId' OU ('channel' E 'cuid')",
            "examples": {
                "modo_manual": {"sessionId": "ocid1...", "userMessage": "..."},
                "modo_automatico": {"channel": "web-app", "cuid": "user-123", "userMessage": "..."}
            }
        }), 400
    
    # Modo automático: gerencia sessão internamente com retry
    if channel and cuid:
        session_key = f"{channel}:{cuid}"
        
        # Obter/criar sessão
        sess = session_controller(model_region, agent_endpoint_id, channel, cuid)
        if "error" in sess:
            return jsonify({
                "error": f"Falha ao criar sessão: {sess.get('error')}",
                "details": sess
            }), 500
        
        session_id = sess.get("id")
        
        # Enviar mensagem com retry automático
        response_data, session_id, error = _chat_with_retry_on_session_expired(
            model_region, agent_endpoint_id, session_id, session_key, user_message
        )
        
        if error:
            return error
        
        # Extrair token usage e retornar
        usage = extract_agent_token_usage(response_data)
        return jsonify({
            "agentResponse": response_data,
            "sessionInfo": {
                "sessionId": session_id,
                "sessionKey": session_key,
                "reused": sess.get("reused", False)
            },
            "usage": usage
        })
    
    # Modo manual: usa sessionId fornecido
    else:
        response_data = ask_agent(model_region, agent_endpoint_id, session_id, user_message)
        
        # Se retornou erro 409, informa ao usuário
        if isinstance(response_data, dict) and response_data.get("_http_status") == 409:
            return jsonify({
                "error": "Sessão inválida ou expirada",
                "suggestion": "Use modo automático com 'channel' e 'cuid' para gerenciamento automático de sessão",
                "details": response_data
            }), 409
        
        # Extrair token usage da resposta do agente
        usage = extract_agent_token_usage(response_data)
        
        return jsonify({
            "agentResponse": response_data,
            "usage": usage
        })

@app.route("/genai/<model_name>/inference", methods=["POST"])
def oci_inference(model_name):
    """
    Inferência direta com modelo LLM (sem formato OpenAI).
    Endpoint direto OCI (sem camada OpenAI/v1).
    """
    try:
        model_config = get_model_config(model_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
    model_type = model_config.get("type", "model")
    if model_type == "agent":
        return jsonify({"error": f"'{model_name}' é um agent. Use /genai/{model_name}/chat ao invés de /inference."}), 400
    
    data = request.get_json() or {}
    logger.debug(f">>> /genai/{model_name}/inference payload recebido:")
    logger.debug(json.dumps(data, ensure_ascii=False, indent=2))
    
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400
    
    model_region = model_config.get("region")
    compartment_id = model_config.get("compartmentId")
    model_ocid = model_config.get("id")
    
    # Parâmetros opcionais
    temperature = data.get("temperature", 1)
    top_p = data.get("top_p", 1)
    top_k = data.get("top_k", 0)
    max_tokens = data.get("max_tokens", 50000)
    
    if TEST_MODE:
        return jsonify({
            "response": {
                "text": f"[TEST_MODE] Resposta simulada para: {prompt}",
                "finish_reason": "stop"
            }
        })
    
    try:
        client = get_oci_inference_client(model_region)
        
        # Cria mensagem
        content = oci.generative_ai_inference.models.TextContent()
        content.text = str(prompt)
        message = oci.generative_ai_inference.models.Message()
        message.role = "USER"
        message.content = [content]
        
        # Cria chat request
        chat_request = oci.generative_ai_inference.models.GenericChatRequest()
        chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
        chat_request.messages = [message]
        chat_request.max_tokens = max_tokens
        chat_request.temperature = temperature
        chat_request.top_p = top_p
        chat_request.top_k = top_k
        
        # Cria chat detail
        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_ocid)
        chat_detail.chat_request = chat_request
        chat_detail.compartment_id = compartment_id
        
        # Faz chamada
        chat_response = client.chat(chat_detail)
        chat_choices = chat_response.data.chat_response.choices
        
        # Extrair token usage da resposta do modelo
        usage = extract_token_usage(chat_response)
        
        chat_data = {
            "text": chat_choices[0].message.content[0].text,
            "finish_reason": chat_choices[0].finish_reason
        }
        
        return jsonify({
            "response": chat_data,
            "usage": usage
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================
# Main
# ==========================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("OCI GenAI Proxy v2.0.3")
    app.run(host='0.0.0.0', port=8000, debug=False)
