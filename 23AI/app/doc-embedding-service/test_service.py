"""
test_service.py - Script de Teste do Document Embedding Service
Testa os principais endpoints da aplicação
"""

import requests
import json
import sys
import os
from pathlib import Path

# Configuração
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "test-api-key")

# Headers de autenticação
HEADERS = {
    "X-API-Key": API_KEY
}

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def test_health_check():
    """Testa o endpoint de health check"""
    print_info("Testando health check...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check OK: {data}")
            return True
        else:
            print_error(f"Health check falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro no health check: {e}")
        return False

def test_upload_document(file_path: str):
    """Testa o upload de documento"""
    print_info(f"Testando upload de documento: {file_path}")
    
    if not os.path.exists(file_path):
        print_error(f"Arquivo não encontrado: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            data = {
                'metadata': json.dumps({
                    "description": "Documento de teste",
                    "source": "test_service.py"
                })
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/documents/upload",
                headers=HEADERS,
                files=files,
                data=data
            )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"Upload bem-sucedido!")
            print_info(f"  Document ID: {data['document_id']}")
            print_info(f"  Chunks criados: {data['chunks_created']}")
            print_info(f"  Tempo de processamento: {data['processing_time']}s")
            return data['document_id']
        else:
            print_error(f"Upload falhou: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Erro no upload: {e}")
        return None

def test_list_documents():
    """Testa a listagem de documentos"""
    print_info("Testando listagem de documentos...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/documents",
            headers=HEADERS,
            params={"limit": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Listagem bem-sucedida!")
            print_info(f"  Total de documentos: {data['total']}")
            
            for doc in data['documents'][:3]:
                print_info(f"  - {doc['filename']} ({doc['chunks_count']} chunks)")
            
            return True
        else:
            print_error(f"Listagem falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro na listagem: {e}")
        return False

def test_get_document(document_id: str):
    """Testa a busca de documento por ID"""
    print_info(f"Testando busca de documento: {document_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/documents/{document_id}",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Documento encontrado!")
            print_info(f"  Filename: {data['filename']}")
            print_info(f"  File type: {data['file_type']}")
            print_info(f"  Upload date: {data['upload_date']}")
            return True
        else:
            print_error(f"Busca falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro na busca: {e}")
        return False

def test_search(query: str):
    """Testa a busca semântica"""
    print_info(f"Testando busca semântica: '{query}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/search",
            headers=HEADERS,
            json={
                "query": query,
                "top_k": 5,
                "threshold": 0.0
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Busca bem-sucedida!")
            print_info(f"  Resultados encontrados: {data['total_results']}")
            
            for i, result in enumerate(data['results'][:3], 1):
                print_info(f"  {i}. {result['document_filename']} "
                          f"(similaridade: {result['similarity']:.3f})")
                print_info(f"     Texto: {result['chunk_text'][:100]}...")
            
            return True
        else:
            print_error(f"Busca falhou: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Erro na busca: {e}")
        return False

def test_stats():
    """Testa o endpoint de estatísticas"""
    print_info("Testando estatísticas...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/stats",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Estatísticas obtidas!")
            print_info(f"  Total de documentos: {data['total_documents']}")
            print_info(f"  Total de chunks: {data['total_chunks']}")
            print_info(f"  Modelo de embedding: {data['embedding_model']}")
            print_info(f"  Dimensão: {data['embedding_dimension']}")
            return True
        else:
            print_error(f"Estatísticas falharam: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro nas estatísticas: {e}")
        return False

def test_delete_document(document_id: str):
    """Testa a deleção de documento"""
    print_info(f"Testando deleção de documento: {document_id}")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v1/documents/{document_id}",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            print_success(f"Documento deletado com sucesso!")
            return True
        else:
            print_error(f"Deleção falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro na deleção: {e}")
        return False

def create_test_document():
    """Cria um documento de teste"""
    test_file = "/tmp/test_document.txt"
    
    content = """
    Document Embedding Service - Documento de Teste
    
    Este é um documento de teste para o serviço de embeddings.
    
    O serviço permite fazer upload de documentos em diversos formatos:
    - PDF (com texto nativo ou escaneado)
    - Word (.docx)
    - Imagens (PNG, JPG, TIFF) com OCR
    
    Os documentos são processados automaticamente:
    1. Extração de texto
    2. Divisão em chunks
    3. Geração de embeddings vetoriais
    4. Armazenamento no Oracle ADW 23AI
    
    A busca semântica permite encontrar documentos relevantes
    mesmo quando as palavras exatas não aparecem no texto.
    
    Este é um exemplo de tecnologia de Retrieval-Augmented Generation (RAG).
    """
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_info(f"Documento de teste criado: {test_file}")
    return test_file

def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("Document Embedding Service - Suite de Testes")
    print("="*60 + "\n")
    
    print_info(f"URL base: {BASE_URL}")
    print_info(f"API Key: {API_KEY[:10]}...")
    print()
    
    results = {}
    
    # 1. Health Check
    results['health'] = test_health_check()
    print()
    
    # 2. Criar documento de teste
    test_file = create_test_document()
    print()
    
    # 3. Upload de documento
    document_id = test_upload_document(test_file)
    results['upload'] = document_id is not None
    print()
    
    if document_id:
        # 4. Listar documentos
        results['list'] = test_list_documents()
        print()
        
        # 5. Buscar documento por ID
        results['get'] = test_get_document(document_id)
        print()
        
        # 6. Busca semântica
        results['search'] = test_search("como fazer upload de documentos")
        print()
        
        # 7. Estatísticas
        results['stats'] = test_stats()
        print()
        
        # 8. Deletar documento (opcional - comentado para manter dados)
        # results['delete'] = test_delete_document(document_id)
        # print()
    
    # Resumo
    print("\n" + "="*60)
    print("Resumo dos Testes")
    print("="*60 + "\n")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "PASSOU" if result else "FALHOU"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{test_name.upper()}: {status}{Colors.END}")
    
    print()
    print(f"Total: {passed}/{total} testes passaram")
    
    if passed == total:
        print_success("Todos os testes passaram! ✓")
        return 0
    else:
        print_error(f"{total - passed} teste(s) falharam")
        return 1

if __name__ == "__main__":
    sys.exit(main())
