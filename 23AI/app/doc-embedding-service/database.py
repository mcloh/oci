"""
database.py - Integração com Oracle Autonomous Database (ADW 23AI)
Gerencia conexão, criação de tabelas e operações CRUD para documentos e chunks
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np


class DatabaseManager:
    """Gerenciador de banco de dados ADW 23AI"""
    
    def __init__(self, user: str = None, password: str = None, 
                 dsn: str = None):
        """
        Inicializa o gerenciador de banco de dados
        
        Args:
            user: Usuário do banco de dados
            password: Senha do banco de dados
            dsn: DSN de conexão
        """
        self.user = user or os.environ.get("DB_USER")
        self.password = password or os.environ.get("DB_PASSWORD")
        self.dsn = dsn or os.environ.get("DB_DSN")
        
        self.connection = None
        self.embedding_dimension = None
        
        # Importa oracledb
        try:
            import oracledb
            self.oracledb = oracledb
        except ImportError:
            raise RuntimeError(
                "oracledb não está instalado. "
                "Instale com: pip install oracledb"
            )
        
        # Valida configuração
        if not all([self.user, self.password, self.dsn]):
            raise ValueError(
                "Configuração de banco de dados incompleta. "
                "Defina DB_USER, DB_PASSWORD e DB_DSN"
            )
        
        print(f"[database] Configuração carregada:")
        print(f"[database] - User: {self.user}")
        print(f"[database] - DSN: {self.dsn[:50]}...")
    
    def connect(self) -> None:
        """Estabelece conexão com o banco de dados"""
        try:
            print("[database] Conectando ao ADW 23AI...")
            self.connection = self.oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            print("[database] Conexão estabelecida com sucesso")
            
            # Testa conexão
            cursor = self.connection.cursor()
            cursor.execute("SELECT 'OK' FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0] == 'OK':
                print("[database] Teste de conexão: OK")
            
        except Exception as e:
            raise RuntimeError(f"Erro ao conectar ao banco de dados: {str(e)}")
    
    def disconnect(self) -> None:
        """Fecha a conexão com o banco de dados"""
        if self.connection:
            try:
                self.connection.close()
                print("[database] Conexão fechada")
            except Exception as e:
                print(f"[database] Erro ao fechar conexão: {e}")
    
    def ensure_connection(self) -> None:
        """Garante que há uma conexão ativa"""
        if not self.connection:
            self.connect()
    
    def initialize_schema(self, embedding_dimension: int = 384) -> None:
        """
        Cria as tabelas necessárias se não existirem
        
        Args:
            embedding_dimension: Dimensão dos vetores de embedding
        """
        self.ensure_connection()
        self.embedding_dimension = embedding_dimension
        
        cursor = self.connection.cursor()
        
        try:
            # Tabela de documentos
            print("[database] Criando tabela DOCUMENTS...")
            cursor.execute("""
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE TABLE DOCUMENTS (
                        id VARCHAR2(36) PRIMARY KEY,
                        filename VARCHAR2(500) NOT NULL,
                        file_type VARCHAR2(50) NOT NULL,
                        file_size NUMBER NOT NULL,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        content_hash VARCHAR2(64),
                        metadata CLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE = -955 THEN
                            NULL; -- Tabela já existe
                        ELSE
                            RAISE;
                        END IF;
                END;
            """)
            
            # Tabela de chunks
            print(f"[database] Criando tabela DOCUMENT_CHUNKS (embedding dimension: {embedding_dimension})...")
            cursor.execute(f"""
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE TABLE DOCUMENT_CHUNKS (
                        id VARCHAR2(36) PRIMARY KEY,
                        document_id VARCHAR2(36) NOT NULL,
                        chunk_index NUMBER NOT NULL,
                        chunk_text CLOB NOT NULL,
                        chunk_size NUMBER NOT NULL,
                        embedding VECTOR({embedding_dimension}, FLOAT32),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_document FOREIGN KEY (document_id) 
                            REFERENCES DOCUMENTS(id) ON DELETE CASCADE
                    )';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE = -955 THEN
                            NULL; -- Tabela já existe
                        ELSE
                            RAISE;
                        END IF;
                END;
            """)
            
            # Índice para busca por documento
            print("[database] Criando índices...")
            cursor.execute("""
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE INDEX idx_chunks_document 
                        ON DOCUMENT_CHUNKS(document_id)';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE = -955 THEN
                            NULL; -- Índice já existe
                        ELSE
                            RAISE;
                        END IF;
                END;
            """)
            
            # Índice vetorial para busca semântica (Oracle 23AI)
            print("[database] Criando índice vetorial para busca semântica...")
            cursor.execute("""
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE VECTOR INDEX idx_chunks_embedding 
                        ON DOCUMENT_CHUNKS(embedding) 
                        ORGANIZATION NEIGHBOR PARTITIONS
                        WITH DISTANCE COSINE';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE = -955 THEN
                            NULL; -- Índice já existe
                        ELSE
                            RAISE;
                        END IF;
                END;
            """)
            
            self.connection.commit()
            print("[database] Schema inicializado com sucesso")
            
        except Exception as e:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao inicializar schema: {str(e)}")
        finally:
            cursor.close()
    
    def insert_document(self, filename: str, file_type: str, 
                       file_size: int, content_hash: str,
                       metadata: Dict[str, Any] = None) -> str:
        """
        Insere um novo documento
        
        Args:
            filename: Nome do arquivo
            file_type: Tipo MIME do arquivo
            file_size: Tamanho em bytes
            content_hash: Hash SHA-256 do conteúdo
            metadata: Metadados adicionais (opcional)
            
        Returns:
            ID do documento inserido
        """
        self.ensure_connection()
        
        document_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO DOCUMENTS 
                (id, filename, file_type, file_size, content_hash, metadata)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, (document_id, filename, file_type, file_size, content_hash, metadata_json))
            
            self.connection.commit()
            print(f"[database] Documento inserido: {document_id}")
            
            return document_id
            
        except Exception as e:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao inserir documento: {str(e)}")
        finally:
            cursor.close()
    
    def insert_chunks(self, document_id: str, chunks: List[Dict[str, Any]]) -> int:
        """
        Insere chunks de um documento
        
        Args:
            document_id: ID do documento
            chunks: Lista de chunks com texto e embedding
            
        Returns:
            Número de chunks inseridos
        """
        self.ensure_connection()
        
        if not chunks:
            return 0
        
        cursor = self.connection.cursor()
        
        try:
            inserted = 0
            
            for chunk in chunks:
                chunk_id = str(uuid.uuid4())
                chunk_index = chunk['index']
                chunk_text = chunk['text']
                chunk_size = chunk['size']
                embedding = chunk.get('embedding')
                
                # Converte embedding numpy para lista
                if isinstance(embedding, np.ndarray):
                    embedding_list = embedding.tolist()
                else:
                    embedding_list = embedding
                
                # Formata embedding como string para VECTOR type
                embedding_str = str(embedding_list)
                
                cursor.execute("""
                    INSERT INTO DOCUMENT_CHUNKS 
                    (id, document_id, chunk_index, chunk_text, chunk_size, embedding)
                    VALUES (:1, :2, :3, :4, :5, TO_VECTOR(:6))
                """, (chunk_id, document_id, chunk_index, chunk_text, 
                      chunk_size, embedding_str))
                
                inserted += 1
            
            self.connection.commit()
            print(f"[database] {inserted} chunks inseridos para documento {document_id}")
            
            return inserted
            
        except Exception as e:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao inserir chunks: {str(e)}")
        finally:
            cursor.close()
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca um documento por ID
        
        Args:
            document_id: ID do documento
            
        Returns:
            Dicionário com dados do documento ou None
        """
        self.ensure_connection()
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                SELECT id, filename, file_type, file_size, upload_date, 
                       content_hash, metadata, created_at
                FROM DOCUMENTS
                WHERE id = :1
            """, (document_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                'id': row[0],
                'filename': row[1],
                'file_type': row[2],
                'file_size': row[3],
                'upload_date': row[4].isoformat() if row[4] else None,
                'content_hash': row[5],
                'metadata': json.loads(row[6]) if row[6] else None,
                'created_at': row[7].isoformat() if row[7] else None
            }
            
        except Exception as e:
            raise RuntimeError(f"Erro ao buscar documento: {str(e)}")
        finally:
            cursor.close()
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Lista documentos
        
        Args:
            limit: Número máximo de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de documentos
        """
        self.ensure_connection()
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                SELECT d.id, d.filename, d.file_type, d.file_size, d.upload_date,
                       d.content_hash, d.metadata, d.created_at,
                       COUNT(c.id) as chunks_count
                FROM DOCUMENTS d
                LEFT JOIN DOCUMENT_CHUNKS c ON d.id = c.document_id
                GROUP BY d.id, d.filename, d.file_type, d.file_size, d.upload_date,
                         d.content_hash, d.metadata, d.created_at
                ORDER BY d.upload_date DESC
                OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY
            """, (offset, limit))
            
            documents = []
            
            for row in cursor:
                documents.append({
                    'id': row[0],
                    'filename': row[1],
                    'file_type': row[2],
                    'file_size': row[3],
                    'upload_date': row[4].isoformat() if row[4] else None,
                    'content_hash': row[5],
                    'metadata': json.loads(row[6]) if row[6] else None,
                    'created_at': row[7].isoformat() if row[7] else None,
                    'chunks_count': row[8]
                })
            
            return documents
            
        except Exception as e:
            raise RuntimeError(f"Erro ao listar documentos: {str(e)}")
        finally:
            cursor.close()
    
    def delete_document(self, document_id: str) -> bool:
        """
        Deleta um documento e seus chunks (CASCADE)
        
        Args:
            document_id: ID do documento
            
        Returns:
            True se deletado, False se não encontrado
        """
        self.ensure_connection()
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("DELETE FROM DOCUMENTS WHERE id = :1", (document_id,))
            
            deleted = cursor.rowcount > 0
            self.connection.commit()
            
            if deleted:
                print(f"[database] Documento deletado: {document_id}")
            
            return deleted
            
        except Exception as e:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao deletar documento: {str(e)}")
        finally:
            cursor.close()
    
    def search_similar_chunks(self, query_embedding: np.ndarray, 
                             top_k: int = 5,
                             threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Busca chunks similares usando busca vetorial
        
        Args:
            query_embedding: Embedding da query
            top_k: Número de resultados
            threshold: Threshold mínimo de similaridade
            
        Returns:
            Lista de chunks similares com metadados
        """
        self.ensure_connection()
        
        cursor = self.connection.cursor()
        
        try:
            # Converte embedding para string
            if isinstance(query_embedding, np.ndarray):
                embedding_list = query_embedding.tolist()
            else:
                embedding_list = query_embedding
            
            embedding_str = str(embedding_list)
            
            # Busca vetorial usando VECTOR_DISTANCE
            cursor.execute("""
                SELECT c.id, c.document_id, c.chunk_index, c.chunk_text, c.chunk_size,
                       d.filename, d.file_type,
                       VECTOR_DISTANCE(c.embedding, TO_VECTOR(:1), COSINE) as distance
                FROM DOCUMENT_CHUNKS c
                JOIN DOCUMENTS d ON c.document_id = d.id
                ORDER BY distance
                FETCH FIRST :2 ROWS ONLY
            """, (embedding_str, top_k))
            
            results = []
            
            for row in cursor:
                distance = float(row[7])
                # Converte distância cosseno para similaridade [0, 1]
                similarity = 1.0 - distance
                
                if similarity >= threshold:
                    results.append({
                        'chunk_id': row[0],
                        'document_id': row[1],
                        'chunk_index': row[2],
                        'chunk_text': row[3],
                        'chunk_size': row[4],
                        'document_filename': row[5],
                        'document_file_type': row[6],
                        'similarity': similarity,
                        'distance': distance
                    })
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Erro na busca vetorial: {str(e)}")
        finally:
            cursor.close()


# Instância global (será inicializada na aplicação principal)
_db_manager: Optional[DatabaseManager] = None


def initialize_database(user: str = None, password: str = None,
                       dsn: str = None,
                       embedding_dimension: int = 384) -> DatabaseManager:
    """
    Inicializa o gerenciador de banco de dados
    
    Args:
        user: Usuário do banco
        password: Senha
        dsn: DSN de conexão
        embedding_dimension: Dimensão dos embeddings
        
    Returns:
        Instância do DatabaseManager
    """
    global _db_manager
    
    _db_manager = DatabaseManager(
        user=user,
        password=password,
        dsn=dsn
    )
    
    _db_manager.connect()
    _db_manager.initialize_schema(embedding_dimension=embedding_dimension)
    
    return _db_manager


def get_database() -> Optional[DatabaseManager]:
    """
    Retorna a instância do gerenciador de banco de dados
    
    Returns:
        Instância do DatabaseManager ou None
    """
    return _db_manager
