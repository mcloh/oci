"""
Disclaimer:

Este código é fornecido como um exemplo open-source de contribuição comunitária para implementação de soluções utilizando a plataforma Oracle.
É distribuído "AS IS" (como está), sem garantias, responsabilidades ou suporte de qualquer natureza.
A Oracle Corporation não assume qualquer responsabilidade pelo conteúdo, precisão, funcionalidade ou forma deste material.
"""

"""
auth.py - Módulo de Autenticação OCI e HTTP
Implementa autenticação OCI Signer e validação de API Keys (X-API-Key e Bearer)
"""

import os
import hmac
import oci
from typing import Optional, Dict, Any
from flask import request, abort


class OCIAuthManager:
    """Gerenciador de autenticação OCI"""
    
    def __init__(self, config_file: str = None, test_mode: bool = False):
        """
        Inicializa o gerenciador de autenticação OCI
        
        Args:
            config_file: Caminho para arquivo de configuração OCI
            test_mode: Se True, executa em modo de teste sem OCI real
        """
        self.config_file = config_file or os.environ.get("OCI_CONFIG_FILE", "/home/app/credentials.conf")
        self.test_mode = test_mode or os.environ.get("TEST_MODE", "false").lower() == "true"
        self.config = {}
        self.signer = None
        
        if not self.test_mode:
            self._load_config()
            self._initialize_signer()
    
    def _load_config(self) -> None:
        """Carrega configuração OCI do arquivo"""
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            self.config[key.strip()] = value.strip()
            
            # Verifica se test_mode está configurado no arquivo
            if self.config.get("test_mode", "false").lower() == "true":
                self.test_mode = True
                print("[auth] Modo de teste ativado via arquivo de configuração")
                
        except FileNotFoundError:
            print(f"[auth] AVISO: Arquivo de configuração '{self.config_file}' não encontrado")
            print("[auth] Executando em modo de teste...")
            self.test_mode = True
        except Exception as e:
            print(f"[auth] Erro ao carregar configuração: {e}")
            print("[auth] Executando em modo de teste...")
            self.test_mode = True
    
    def _initialize_signer(self) -> None:
        """Inicializa o OCI Signer"""
        if self.test_mode:
            print("[auth] Modo de teste - OCI Signer não será inicializado")
            return
        
        try:
            self.signer = oci.signer.Signer(
                tenancy=self.config.get("tenancy"),
                user=self.config.get("user"),
                fingerprint=self.config.get("fingerprint"),
                private_key_file_location=self.config.get("key_file"),
                pass_phrase=self.config.get("pass_phrase"),
                private_key_content=self.config.get("key_content"),
            )
            print("[auth] OCI Signer inicializado com sucesso")
        except Exception as e:
            print(f"[auth] Erro ao inicializar OCI Signer: {e}")
            print("[auth] Executando em modo de teste...")
            self.test_mode = True
    
    def get_signer(self) -> Optional[oci.signer.Signer]:
        """Retorna o OCI Signer ou None se em modo de teste"""
        return self.signer
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna a configuração OCI"""
        return self.config
    
    def is_test_mode(self) -> bool:
        """Retorna True se estiver em modo de teste"""
        return self.test_mode


class HTTPAuthManager:
    """Gerenciador de autenticação HTTP via API Key"""
    
    def __init__(self, api_key: str = None, debug: bool = False):
        """
        Inicializa o gerenciador de autenticação HTTP
        
        Args:
            api_key: API Key esperada para autenticação
            debug: Se True, habilita logs de debug
        """
        self.api_key = api_key or os.environ.get("API_KEY")
        self.debug = debug or os.environ.get("DEBUG_AUTH", "false").lower() == "true"
        
        if not self.api_key:
            print("[auth] AVISO: API_KEY não configurada nas variáveis de ambiente")
            print("[auth] Autenticação HTTP estará desabilitada")
    
    @staticmethod
    def _safe_equals(a: str, b: str) -> bool:
        """
        Compara duas strings de forma segura contra timing attacks
        
        Args:
            a: Primeira string
            b: Segunda string
            
        Returns:
            True se as strings são iguais
        """
        if a is None or b is None:
            return False
        return hmac.compare_digest(a, b)
    
    @staticmethod
    def _parse_bearer_token(auth_header: str) -> str:
        """
        Extrai o token Bearer do header Authorization
        
        Args:
            auth_header: Valor do header Authorization
            
        Returns:
            Token extraído ou string vazia
        """
        if not auth_header:
            return ""
        
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() in ("bearer", "token"):
            return parts[1]
        
        return ""
    
    def validate_request(self) -> bool:
        """
        Valida a autenticação da requisição atual
        
        Returns:
            True se autenticado, False caso contrário
            
        Raises:
            401 Unauthorized se a autenticação falhar
        """
        # Se não há API key configurada, permite acesso
        if not self.api_key:
            if self.debug:
                print("[auth] API_KEY não configurada - permitindo acesso")
            return True
        
        # Extrai credenciais da requisição
        provided_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization")
        bearer_token = self._parse_bearer_token(auth_header)
        
        if self.debug:
            print(f"[auth] method={request.method} path={request.path}")
            print(f"[auth] X-API-Key={'<set>' if provided_key else '<none>'}")
            print(f"[auth] Authorization={'<set>' if auth_header else '<none>'}")
            print(f"[auth] Bearer Token={'<set>' if bearer_token else '<none>'}")
        
        # Valida credenciais
        if self._safe_equals(provided_key, self.api_key):
            if self.debug:
                print("[auth] Autenticação via X-API-Key bem-sucedida")
            return True
        
        if self._safe_equals(bearer_token, self.api_key):
            if self.debug:
                print("[auth] Autenticação via Bearer Token bem-sucedida")
            return True
        
        # Autenticação falhou
        if self.debug:
            print("[auth] Autenticação falhou - credenciais inválidas ou ausentes")
        
        abort(401, description="Credenciais inválidas ou ausentes. Use X-API-Key ou Authorization: Bearer.")
        return False
    
    def check_api_key(self) -> None:
        """
        Middleware para validar API key em requisições
        Deve ser usado com @app.before_request
        """
        # Permite requisições OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return
        
        # Permite health check sem autenticação
        if request.path == "/" or request.path == "/health":
            return
        
        self.validate_request()


# Instâncias globais (serão inicializadas na aplicação principal)
oci_auth: Optional[OCIAuthManager] = None
http_auth: Optional[HTTPAuthManager] = None


def initialize_auth(config_file: str = None, api_key: str = None, 
                   test_mode: bool = False, debug: bool = False) -> tuple:
    """
    Inicializa os gerenciadores de autenticação
    
    Args:
        config_file: Caminho para arquivo de configuração OCI
        api_key: API Key para autenticação HTTP
        test_mode: Se True, executa em modo de teste
        debug: Se True, habilita logs de debug
        
    Returns:
        Tupla (oci_auth, http_auth)
    """
    global oci_auth, http_auth
    
    oci_auth = OCIAuthManager(config_file=config_file, test_mode=test_mode)
    http_auth = HTTPAuthManager(api_key=api_key, debug=debug)
    
    return oci_auth, http_auth


def get_oci_auth() -> Optional[OCIAuthManager]:
    """Retorna a instância do gerenciador OCI"""
    return oci_auth


def get_http_auth() -> Optional[HTTPAuthManager]:
    """Retorna a instância do gerenciador HTTP"""
    return http_auth
