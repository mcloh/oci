from flask import Flask, request, json, jsonify
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

def call_inference_model(region, compartment_id, model_id, prompt):
    if TEST_MODE:
        return {"response": f"Resposta simulada para o prompt: {prompt}"}

    try:
        endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"

        generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, service_endpoint=endpoint, retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
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
        #chat_request.frequency_penalty = 0
        #chat_request.presence_penalty = 0
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
        print(chat_data)

        return {"response": chat_data}
    except Exception as e:
        return {"error": str(e)}

def check_api_key():
    expected_key = os.environ.get("API_KEY")
    if not expected_key:
        print("AVISO: API_KEY não configurada nas variáveis de ambiente.")
        return  # passa sem autenticar (útil em dev, pode remover se quiser obrigar)
    provided_key = request.headers.get("X-API-Key")
    if provided_key != expected_key:
        abort(401, description="Chave de API inválida ou ausente.")

# Before all requests
@app.before_request
def before_all_requests():
    check_api_key()

# Endpoint para teste
@app.route("/", methods=["GET"])
def test():
    return jsonify({"test":"ok"})

@app.route("/test/<myvar>/copy", methods=["GET"])
def var_copy(myvar):
    try:
        print(f"myvar={myvar}")
        return jsonify({"myvar":myvar})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"error": str(e)}), 400

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

# Endpoint para inferencia direta com GenAI
@app.route("/genai/<region>/<compartment_id>/<model_id>/inference", methods=["POST"])
def inference(region, compartment_id, model_id):
    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Campo 'prompt' é obrigatório."}), 400
    try:
        response_data = call_inference_model(region, compartment_id, model_id, prompt)
        return jsonify(response_data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
