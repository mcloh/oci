"""
embedding_service.py - Serviço de Geração de Embeddings
Gera embeddings vetoriais para chunks de texto usando Sentence Transformers
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
import time


class EmbeddingService:
    """Serviço para geração de embeddings vetoriais"""
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Inicializa o serviço de embeddings
        
        Args:
            model_name: Nome do modelo Sentence Transformers
            device: Dispositivo para execução ('cpu', 'cuda', etc.)
        """
        self.model_name = model_name or os.environ.get(
            "EMBEDDING_MODEL", 
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.device = device or os.environ.get("EMBEDDING_DEVICE", "cpu")
        self.model = None
        self.dimension = None
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Carrega o modelo de embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            
            print(f"[embedding] Carregando modelo {self.model_name}...")
            start_time = time.time()
            
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Determina a dimensão do embedding
            test_embedding = self.model.encode(["test"], convert_to_numpy=True)
            self.dimension = test_embedding.shape[1]
            
            load_time = time.time() - start_time
            print(f"[embedding] Modelo carregado em {load_time:.2f}s")
            print(f"[embedding] Dimensão dos embeddings: {self.dimension}")
            
        except ImportError:
            raise RuntimeError(
                "sentence-transformers não está instalado. "
                "Instale com: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar modelo de embeddings: {str(e)}")
    
    def get_dimension(self) -> int:
        """
        Retorna a dimensão dos embeddings
        
        Returns:
            Dimensão do vetor de embedding
        """
        return self.dimension
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Gera embedding para um único texto
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Array numpy com o embedding
        """
        if not text or not text.strip():
            raise ValueError("Texto vazio não pode ser processado")
        
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embedding
            
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar embedding: {str(e)}")
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Gera embeddings para múltiplos textos em batch
        
        Args:
            texts: Lista de textos
            batch_size: Tamanho do batch para processamento
            
        Returns:
            Array numpy com os embeddings (shape: [n_texts, dimension])
        """
        if not texts:
            raise ValueError("Lista de textos vazia")
        
        # Remove textos vazios
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("Nenhum texto válido para processar")
        
        try:
            print(f"[embedding] Gerando embeddings para {len(valid_texts)} textos...")
            start_time = time.time()
            
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(valid_texts) > 10
            )
            
            elapsed = time.time() - start_time
            print(f"[embedding] Embeddings gerados em {elapsed:.2f}s "
                  f"({len(valid_texts)/elapsed:.1f} textos/s)")
            
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar embeddings em batch: {str(e)}")
    
    def encode_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gera embeddings para uma lista de chunks
        
        Args:
            chunks: Lista de dicionários com chunks (deve conter chave 'text')
            
        Returns:
            Lista de chunks com embeddings adicionados
        """
        if not chunks:
            return []
        
        # Extrai textos dos chunks
        texts = [chunk['text'] for chunk in chunks]
        
        # Gera embeddings
        embeddings = self.encode_batch(texts)
        
        # Adiciona embeddings aos chunks
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            enriched_chunk = chunk.copy()
            enriched_chunk['embedding'] = embeddings[i]
            enriched_chunk['embedding_dimension'] = self.dimension
            enriched_chunks.append(enriched_chunk)
        
        return enriched_chunks
    
    def calculate_similarity(self, embedding1: np.ndarray, 
                           embedding2: np.ndarray) -> float:
        """
        Calcula similaridade de cosseno entre dois embeddings
        
        Args:
            embedding1: Primeiro embedding
            embedding2: Segundo embedding
            
        Returns:
            Similaridade de cosseno (0 a 1)
        """
        # Normaliza os vetores
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calcula similaridade de cosseno
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # Garante que está no intervalo [0, 1]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))
    
    def find_similar(self, query_embedding: np.ndarray, 
                    embeddings: np.ndarray, 
                    top_k: int = 5,
                    threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Encontra os embeddings mais similares a uma query
        
        Args:
            query_embedding: Embedding da query
            embeddings: Array de embeddings para comparar
            top_k: Número de resultados a retornar
            threshold: Threshold mínimo de similaridade
            
        Returns:
            Lista de dicionários com índices e similaridades
        """
        if len(embeddings) == 0:
            return []
        
        # Normaliza query
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        
        # Normaliza embeddings
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Calcula similaridades
        similarities = np.dot(embeddings_norm, query_norm)
        
        # Converte para [0, 1]
        similarities = (similarities + 1) / 2
        
        # Filtra por threshold
        valid_indices = np.where(similarities >= threshold)[0]
        
        if len(valid_indices) == 0:
            return []
        
        # Ordena por similaridade
        sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])]
        
        # Retorna top_k
        results = []
        for idx in sorted_indices[:top_k]:
            results.append({
                'index': int(idx),
                'similarity': float(similarities[idx])
            })
        
        return results


# Instância global (será inicializada na aplicação principal)
_embedding_service: Optional[EmbeddingService] = None


def initialize_embedding_service(model_name: str = None, 
                                device: str = None) -> EmbeddingService:
    """
    Inicializa o serviço de embeddings
    
    Args:
        model_name: Nome do modelo
        device: Dispositivo de execução
        
    Returns:
        Instância do EmbeddingService
    """
    global _embedding_service
    _embedding_service = EmbeddingService(model_name=model_name, device=device)
    return _embedding_service


def get_embedding_service() -> Optional[EmbeddingService]:
    """
    Retorna a instância do serviço de embeddings
    
    Returns:
        Instância do EmbeddingService ou None
    """
    return _embedding_service


def create_embedding_service(model_name: str = None, 
                            device: str = None) -> EmbeddingService:
    """
    Factory function para criar um EmbeddingService
    
    Args:
        model_name: Nome do modelo
        device: Dispositivo de execução
        
    Returns:
        Nova instância de EmbeddingService
    """
    return EmbeddingService(model_name=model_name, device=device)
