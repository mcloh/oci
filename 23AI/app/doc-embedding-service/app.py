"""
app.py - Aplicação Flask Principal
Web service para upload de documentos, geração de chunks e embeddings
"""

import os
import time
import json
from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Importa módulos locais
from auth import initialize_auth, get_http_auth
from document_processor import create_document_processor
from embedding_service import initialize_embedding_service, get_embedding_service
from database import initialize_database, get_database

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa Flask
app = Flask(__name__)

# Configurações
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_SIZE', 52428800))  # 50MB default
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/home/ubuntu/doc-embedding-service/uploads')

# ==========================
# CORS
# ==========================

try:
    from flask_cors import CORS
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        expose_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "DELETE", "OPTIONS"]
    )
except Exception as e:
    print(f"AVISO: flask-cors não instalado; CORS mínimo será aplicado via after_request: {e}")

@app.after_request
def add_cors_headers(resp):
    resp.headers.setdefault("Access-Control-Allow-Origin", "*")
    resp.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
    resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key")
    return resp

# ==========================
# Inicialização de Serviços
# ==========================

def initialize_services():
    """Inicializa todos os serviços da aplicação"""
    print("\n" + "="*60)
    print("Inicializando Document Embedding Service")
    print("="*60 + "\n")
    
    # Autenticação
    print("[init] Inicializando autenticação...")
    oci_auth, http_auth = initialize_auth(
        config_file=os.environ.get('OCI_CONFIG_FILE'),
        api_key=os.environ.get('API_KEY'),
        test_mode=os.environ.get('TEST_MODE', 'false').lower() == 'true',
        debug=os.environ.get('DEBUG_AUTH', 'false').lower() == 'true'
    )
    
    # Embedding Service
    print("[init] Inicializando serviço de embeddings...")
    embedding_service = initialize_embedding_service(
        model_name=os.environ.get('EMBEDDING_MODEL'),
        device=os.environ.get('EMBEDDING_DEVICE', 'cpu')
    )
    
    embedding_dim = embedding_service.get_dimension()
    print(f"[init] Dimensão dos embeddings: {embedding_dim}")
    
    # Database
    print("[init] Inicializando banco de dados...")
    db = initialize_database(
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        dsn=os.environ.get('DB_DSN'),
        embedding_dimension=embedding_dim
    )
    
    print("\n" + "="*60)
    print("Serviços inicializados com sucesso!")
    print("="*60 + "\n")

# Inicializa serviços ao iniciar a aplicação
initialize_services()

# ==========================
# Middleware de Autenticação
# ==========================

@app.before_request
def before_all_requests():
    """Middleware executado antes de cada requisição"""
    if request.method == "OPTIONS":
        return "", 204
    
    # Valida autenticação
    http_auth = get_http_auth()
    if http_auth:
        http_auth.check_api_key()

# ==========================
# Endpoints
# ==========================

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "service": "document-embedding-service"
    })

@app.route("/api/v1/documents/upload", methods=["POST"])
def upload_document():
    """
    Upload de documento para processamento
    
    Aceita: multipart/form-data
    - file: arquivo (obrigatório)
    - metadata: JSON com metadados (opcional)
    
    Retorna: informações do documento e chunks criados
    """
    start_time = time.time()
    
    # Valida arquivo
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo fornecido"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    
    # Metadados opcionais
    metadata = None
    if 'metadata' in request.form:
        try:
            metadata = json.loads(request.form['metadata'])
        except json.JSONDecodeError:
            return jsonify({"error": "Metadados inválidos (JSON esperado)"}), 400
    
    try:
        # Lê conteúdo do arquivo
        filename = secure_filename(file.filename)
        file_content = file.read()
        file_size = len(file_content)
        file_type = file.content_type or 'application/octet-stream'
        
        print(f"\n[upload] Processando arquivo: {filename}")
        print(f"[upload] Tipo: {file_type}, Tamanho: {file_size} bytes")
        
        # Processa documento
        doc_processor = create_document_processor()
        
        if not doc_processor.is_supported_file(filename, file_type):
            return jsonify({
                "error": f"Tipo de arquivo não suportado: {filename}",
                "supported_types": doc_processor.SUPPORTED_EXTENSIONS
            }), 400
        
        # Extrai texto e cria chunks
        process_result = doc_processor.process_document(
            content=file_content,
            filename=filename,
            mime_type=file_type
        )
        
        # Gera embeddings
        embedding_service = get_embedding_service()
        chunks_with_embeddings = embedding_service.encode_chunks(process_result['chunks'])
        
        # Salva no banco de dados
        db = get_database()
        
        # Insere documento
        document_id = db.insert_document(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            content_hash=process_result['content_hash'],
            metadata=metadata
        )
        
        # Insere chunks
        chunks_inserted = db.insert_chunks(document_id, chunks_with_embeddings)
        
        processing_time = time.time() - start_time
        
        print(f"[upload] Documento processado com sucesso em {processing_time:.2f}s")
        
        return jsonify({
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "text_length": process_result['text_length'],
            "chunks_created": chunks_inserted,
            "embedding_dimension": embedding_service.get_dimension(),
            "processing_time": round(processing_time, 2)
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"[upload] Erro inesperado: {e}")
        return jsonify({"error": f"Erro ao processar documento: {str(e)}"}), 500

@app.route("/api/v1/documents", methods=["GET"])
def list_documents():
    """
    Lista documentos
    
    Query params:
    - limit: número máximo de resultados (padrão: 100)
    - offset: offset para paginação (padrão: 0)
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Valida parâmetros
        if limit < 1 or limit > 1000:
            return jsonify({"error": "Limit deve estar entre 1 e 1000"}), 400
        
        if offset < 0:
            return jsonify({"error": "Offset deve ser >= 0"}), 400
        
        db = get_database()
        documents = db.list_documents(limit=limit, offset=offset)
        
        return jsonify({
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        })
        
    except ValueError as e:
        return jsonify({"error": f"Parâmetros inválidos: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/documents/<document_id>", methods=["GET"])
def get_document(document_id):
    """
    Busca documento por ID
    
    Path params:
    - document_id: ID do documento
    """
    try:
        db = get_database()
        document = db.get_document(document_id)
        
        if not document:
            return jsonify({"error": "Documento não encontrado"}), 404
        
        return jsonify(document)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/documents/<document_id>", methods=["DELETE"])
def delete_document(document_id):
    """
    Deleta documento e seus chunks
    
    Path params:
    - document_id: ID do documento
    """
    try:
        db = get_database()
        deleted = db.delete_document(document_id)
        
        if not deleted:
            return jsonify({"error": "Documento não encontrado"}), 404
        
        return jsonify({
            "message": "Documento deletado com sucesso",
            "document_id": document_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/search", methods=["POST"])
def search_documents():
    """
    Busca semântica em documentos
    
    Body (JSON):
    - query: texto de busca (obrigatório)
    - top_k: número de resultados (padrão: 5)
    - threshold: threshold mínimo de similaridade 0-1 (padrão: 0.0)
    """
    try:
        body = request.get_json(force=True, silent=False) or {}
        
        query = body.get('query')
        if not query or not query.strip():
            return jsonify({"error": "Campo 'query' é obrigatório"}), 400
        
        top_k = body.get('top_k', 5)
        threshold = body.get('threshold', 0.0)
        
        # Valida parâmetros
        if not isinstance(top_k, int) or top_k < 1 or top_k > 100:
            return jsonify({"error": "top_k deve estar entre 1 e 100"}), 400
        
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            return jsonify({"error": "threshold deve estar entre 0 e 1"}), 400
        
        print(f"\n[search] Query: {query[:100]}...")
        print(f"[search] top_k={top_k}, threshold={threshold}")
        
        # Gera embedding da query
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.encode_text(query)
        
        # Busca no banco de dados
        db = get_database()
        results = db.search_similar_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=threshold
        )
        
        print(f"[search] Encontrados {len(results)} resultados")
        
        return jsonify({
            "results": results,
            "query": query,
            "total_results": len(results),
            "top_k": top_k,
            "threshold": threshold
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[search] Erro: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/stats", methods=["GET"])
def get_stats():
    """
    Retorna estatísticas do serviço
    """
    try:
        db = get_database()
        documents = db.list_documents(limit=10000)
        
        total_documents = len(documents)
        total_chunks = sum(doc.get('chunks_count', 0) for doc in documents)
        total_size = sum(doc.get('file_size', 0) for doc in documents)
        
        embedding_service = get_embedding_service()
        
        return jsonify({
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "total_size_bytes": total_size,
            "embedding_model": embedding_service.model_name,
            "embedding_dimension": embedding_service.get_dimension()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================
# Error Handlers
# ==========================

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Não autorizado", "message": str(e)}), 401

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Não encontrado", "message": str(e)}), 404

@app.errorhandler(413)
def request_entity_too_large(e):
    max_size = app.config['MAX_CONTENT_LENGTH']
    return jsonify({
        "error": "Arquivo muito grande",
        "max_size_bytes": max_size,
        "max_size_mb": round(max_size / (1024 * 1024), 2)
    }), 413

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Erro interno do servidor", "message": str(e)}), 500

# ==========================
# Main
# ==========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"\n{'='*60}")
    print(f"Iniciando servidor na porta {port}")
    print(f"Debug mode: {debug}")
    print(f"{'='*60}\n")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
