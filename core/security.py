"""
Módulo de Segurança para o Dashboard Kommo

Implementa:
- Sanitização de inputs
- Rate limiting
- Validação de configurações
- Proteção contra prompt injection
"""
import re
import time
import hashlib
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import streamlit as st

from core.logging import get_logger


logger = get_logger("security")


# ========================================
# SANITIZAÇÃO DE INPUTS
# ========================================

class InputSanitizer:
    """
    Sanitizador de inputs para prevenir injeções e dados maliciosos.
    
    Uso:
        sanitizer = InputSanitizer()
        clean_text = sanitizer.sanitize_text(user_input)
        clean_prompt = sanitizer.sanitize_ai_prompt(prompt)
    """
    
    # Padrões perigosos para prompts de IA
    DANGEROUS_PATTERNS = [
        r'ignore\s+(previous|all|above)\s+instructions?',
        r'disregard\s+(previous|all|above)',
        r'forget\s+(everything|all|previous)',
        r'new\s+instructions?:',
        r'system\s*:',
        r'assistant\s*:',
        r'</?(system|assistant|user)>',
        r'\[INST\]',
        r'<<SYS>>',
    ]
    
    # Caracteres a remover/escapar
    DANGEROUS_CHARS = ['<script>', '</script>', 'javascript:', 'onerror=', 'onclick=']
    
    def __init__(self, max_length: int = 5000):
        """
        Args:
            max_length: Tamanho máximo permitido para textos
        """
        self.max_length = max_length
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.DANGEROUS_PATTERNS
        ]
    
    def sanitize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitiza texto genérico removendo caracteres perigosos.
        
        Args:
            text: Texto a sanitizar
            max_length: Tamanho máximo (usa padrão se não especificado)
        
        Returns:
            Texto sanitizado
        """
        if not isinstance(text, str):
            return ""
        
        # Limitar tamanho
        limit = max_length or self.max_length
        if len(text) > limit:
            text = text[:limit]
            logger.warning("Texto truncado por exceder limite", original_length=len(text), limit=limit)
        
        # Remover caracteres perigosos para HTML/JS
        for char in self.DANGEROUS_CHARS:
            text = text.replace(char, '')
        
        # Normalizar espaços em branco
        text = ' '.join(text.split())
        
        return text.strip()
    
    def sanitize_ai_prompt(self, prompt: str) -> str:
        """
        Sanitiza prompt para IA, removendo tentativas de injeção.
        
        Args:
            prompt: Prompt do usuário
        
        Returns:
            Prompt sanitizado
        """
        if not isinstance(prompt, str):
            return ""
        
        # Sanitização básica primeiro
        clean_prompt = self.sanitize_text(prompt, max_length=2000)
        
        # Verificar padrões de injeção
        injection_found = False
        for pattern in self._compiled_patterns:
            if pattern.search(clean_prompt):
                injection_found = True
                # Remover o padrão perigoso
                clean_prompt = pattern.sub('', clean_prompt)
        
        if injection_found:
            logger.warning("Tentativa de prompt injection detectada e removida")
        
        return clean_prompt.strip()
    
    def sanitize_sql_param(self, value: Any) -> Any:
        """
        Sanitiza parâmetro para uso em queries (não substitui prepared statements!).
        
        Args:
            value: Valor a sanitizar
        
        Returns:
            Valor sanitizado
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            # Remover caracteres de SQL injection comuns
            dangerous = ["'", '"', ';', '--', '/*', '*/', 'DROP', 'DELETE', 'UPDATE', 'INSERT']
            sanitized = value
            for char in dangerous:
                sanitized = sanitized.replace(char, '')
            return sanitized
        
        return value


# Instância global do sanitizador
_sanitizer = InputSanitizer()


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """Função de conveniência para sanitizar texto"""
    return _sanitizer.sanitize_text(text, max_length)


def sanitize_ai_prompt(prompt: str) -> str:
    """Função de conveniência para sanitizar prompts de IA"""
    return _sanitizer.sanitize_ai_prompt(prompt)


# ========================================
# RATE LIMITING
# ========================================

@dataclass
class RateLimitConfig:
    """Configuração de rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Máximo de requisições em 1 segundo


class RateLimiter:
    """
    Rate limiter em memória para controlar frequência de operações.
    
    Uso:
        limiter = RateLimiter()
        if limiter.is_allowed("api_gemini"):
            # fazer chamada
        else:
            st.warning("Aguarde um momento antes de tentar novamente")
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        # Armazena timestamps de requisições por chave
        self._requests: Dict[str, List[float]] = defaultdict(list)
    
    def _cleanup_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requisições antigas da janela de tempo"""
        cutoff = time.time() - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
    
    def is_allowed(self, key: str) -> bool:
        """
        Verifica se uma nova requisição é permitida.
        
        Args:
            key: Identificador da operação/recurso
        
        Returns:
            True se permitido, False se bloqueado
        """
        now = time.time()
        
        # Limpar requisições antigas (janela de 1 hora)
        self._cleanup_old_requests(key, 3600)
        
        requests = self._requests[key]
        
        # Verificar burst (último segundo)
        recent_second = [ts for ts in requests if ts > now - 1]
        if len(recent_second) >= self.config.burst_limit:
            logger.warning("Rate limit: burst excedido", key=key)
            return False
        
        # Verificar limite por minuto
        recent_minute = [ts for ts in requests if ts > now - 60]
        if len(recent_minute) >= self.config.requests_per_minute:
            logger.warning("Rate limit: limite por minuto excedido", key=key)
            return False
        
        # Verificar limite por hora
        if len(requests) >= self.config.requests_per_hour:
            logger.warning("Rate limit: limite por hora excedido", key=key)
            return False
        
        # Registrar requisição
        self._requests[key].append(now)
        return True
    
    def get_wait_time(self, key: str) -> float:
        """
        Retorna tempo de espera sugerido em segundos.
        
        Args:
            key: Identificador da operação
        
        Returns:
            Segundos para aguardar (0 se não precisar)
        """
        now = time.time()
        requests = self._requests.get(key, [])
        
        if not requests:
            return 0
        
        # Verificar quando a requisição mais antiga no último minuto expira
        recent_minute = [ts for ts in requests if ts > now - 60]
        if len(recent_minute) >= self.config.requests_per_minute:
            oldest = min(recent_minute)
            return max(0, 60 - (now - oldest))
        
        return 0


# Instância global do rate limiter
_rate_limiter = RateLimiter()


def rate_limit(key: str):
    """
    Decorator para aplicar rate limiting a funções.
    
    Args:
        key: Identificador único para o rate limit
    
    Exemplo:
        @rate_limit("gemini_api")
        def call_gemini(prompt):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _rate_limiter.is_allowed(key):
                wait_time = _rate_limiter.get_wait_time(key)
                st.warning(f"⏳ Muitas requisições. Aguarde {wait_time:.0f} segundos.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_rate_limit(key: str) -> bool:
    """Verifica rate limit sem consumir uma requisição"""
    # Temporariamente verifica sem adicionar
    return _rate_limiter.is_allowed(key)


# ========================================
# VALIDAÇÃO DE CONFIGURAÇÃO
# ========================================

@dataclass
class ConfigValidationResult:
    """Resultado da validação de configuração"""
    is_valid: bool
    missing_keys: List[str] = field(default_factory=list)
    invalid_values: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def validate_secrets() -> ConfigValidationResult:
    """
    Valida se todas as secrets necessárias estão configuradas.
    
    Returns:
        Resultado da validação
    """
    result = ConfigValidationResult(is_valid=True)
    
    required_keys = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]
    
    optional_keys = [
        "GEMINI_API_KEY",
    ]
    
    for key in required_keys:
        value = st.secrets.get(key, "")
        if not value:
            result.is_valid = False
            result.missing_keys.append(key)
        elif len(value) < 10:
            result.is_valid = False
            result.invalid_values[key] = "Valor muito curto, possivelmente inválido"
    
    for key in optional_keys:
        value = st.secrets.get(key, "")
        if not value:
            result.warnings.append(f"Chave opcional '{key}' não configurada")
    
    if not result.is_valid:
        logger.error("Validação de secrets falhou", missing=result.missing_keys)
    
    return result


def require_valid_config() -> None:
    """
    Verifica configuração e interrompe execução se inválida.
    Deve ser chamado no início da aplicação.
    """
    result = validate_secrets()
    
    if not result.is_valid:
        st.error("❌ **Configuração Incompleta**")
        
        if result.missing_keys:
            st.error(f"Chaves faltando: {', '.join(result.missing_keys)}")
        
        if result.invalid_values:
            for key, msg in result.invalid_values.items():
                st.error(f"{key}: {msg}")
        
        st.info("💡 Configure as variáveis em `.streamlit/secrets.toml` ou como variáveis de ambiente.")
        st.stop()
    
    for warning in result.warnings:
        logger.warning(warning)


# ========================================
# HASH E SEGURANÇA DE DADOS
# ========================================

def hash_sensitive_data(data: str) -> str:
    """
    Cria hash de dados sensíveis para logging seguro.
    
    Args:
        data: Dado sensível
    
    Returns:
        Hash SHA-256 truncado
    """
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def mask_sensitive_string(value: str, visible_chars: int = 4) -> str:
    """
    Mascara string sensível mantendo alguns caracteres visíveis.
    
    Args:
        value: String a mascarar
        visible_chars: Número de caracteres visíveis no final
    
    Returns:
        String mascarada (ex: "****abcd")
    """
    if not value or len(value) <= visible_chars:
        return "*" * len(value)
    
    hidden_length = len(value) - visible_chars
    return "*" * hidden_length + value[-visible_chars:]
