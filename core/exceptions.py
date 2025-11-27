"""
Sistema de Tratamento de Erros para o Dashboard Kommo

Implementa exceções customizadas, handlers e decorators para
tratamento consistente de erros em toda a aplicação.
"""
from enum import Enum
from typing import Optional, Any, Callable, TypeVar, Dict
from functools import wraps
from dataclasses import dataclass
import streamlit as st

from core.logging import get_logger


# Type var para decorators
T = TypeVar('T')


class ErrorCode(Enum):
    """Códigos de erro padronizados"""
    # Conexão (1xx)
    CONNECTION_FAILED = 100
    CONNECTION_TIMEOUT = 101
    AUTHENTICATION_FAILED = 102
    
    # Dados (2xx)
    DATA_NOT_FOUND = 200
    DATA_INVALID = 201
    DATA_EMPTY = 202
    QUERY_FAILED = 203
    
    # Validação (3xx)
    VALIDATION_FAILED = 300
    INVALID_DATE_RANGE = 301
    INVALID_INPUT = 302
    
    # API Externa (4xx)
    API_ERROR = 400
    API_RATE_LIMITED = 401
    API_TIMEOUT = 402
    
    # Sistema (5xx)
    INTERNAL_ERROR = 500
    CONFIGURATION_ERROR = 501
    RESOURCE_EXHAUSTED = 502


@dataclass
class ErrorContext:
    """Contexto adicional para erros"""
    operation: str
    details: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None
    retry_possible: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "details": self.details or {},
            "user_message": self.user_message,
            "retry_possible": self.retry_possible
        }


class DashboardError(Exception):
    """
    Exceção base para erros do Dashboard.
    
    Attributes:
        code: Código do erro
        message: Mensagem técnica
        context: Contexto adicional
        original_exception: Exceção original que causou este erro
    """
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        context: Optional[ErrorContext] = None,
        original_exception: Optional[Exception] = None
    ):
        self.code = code
        self.message = message
        self.context = context
        self.original_exception = original_exception
        super().__init__(self.message)
    
    @property
    def user_message(self) -> str:
        """Mensagem amigável para o usuário"""
        if self.context and self.context.user_message:
            return self.context.user_message
        return self._default_user_message()
    
    def _default_user_message(self) -> str:
        """Mensagens padrão baseadas no código de erro"""
        messages = {
            ErrorCode.CONNECTION_FAILED: "Não foi possível conectar ao servidor. Tente novamente em alguns instantes.",
            ErrorCode.CONNECTION_TIMEOUT: "A conexão demorou muito. Verifique sua internet e tente novamente.",
            ErrorCode.AUTHENTICATION_FAILED: "Falha na autenticação. Verifique as credenciais.",
            ErrorCode.DATA_NOT_FOUND: "Os dados solicitados não foram encontrados.",
            ErrorCode.DATA_INVALID: "Os dados recebidos estão em formato inválido.",
            ErrorCode.DATA_EMPTY: "Nenhum dado disponível para os filtros selecionados.",
            ErrorCode.QUERY_FAILED: "Erro ao buscar dados. Tente novamente.",
            ErrorCode.VALIDATION_FAILED: "Dados inválidos. Verifique os campos preenchidos.",
            ErrorCode.INVALID_DATE_RANGE: "O período selecionado é inválido.",
            ErrorCode.INVALID_INPUT: "Entrada inválida. Verifique os dados informados.",
            ErrorCode.API_ERROR: "Erro ao acessar serviço externo.",
            ErrorCode.API_RATE_LIMITED: "Muitas requisições. Aguarde um momento e tente novamente.",
            ErrorCode.API_TIMEOUT: "O serviço não respondeu a tempo. Tente novamente.",
            ErrorCode.INTERNAL_ERROR: "Erro interno. Nossa equipe foi notificada.",
            ErrorCode.CONFIGURATION_ERROR: "Erro de configuração do sistema.",
            ErrorCode.RESOURCE_EXHAUSTED: "Recursos do sistema esgotados temporariamente.",
        }
        return messages.get(self.code, "Ocorreu um erro inesperado.")
    
    def __str__(self) -> str:
        return f"[{self.code.name}] {self.message}"


class ConnectionError(DashboardError):
    """Erro de conexão com serviços externos"""
    def __init__(self, message: str, service: str = "unknown", **kwargs):
        context = ErrorContext(
            operation=f"connect_{service}",
            details={"service": service},
            retry_possible=True
        )
        super().__init__(ErrorCode.CONNECTION_FAILED, message, context, **kwargs)


class DataError(DashboardError):
    """Erro relacionado a dados"""
    def __init__(self, code: ErrorCode, message: str, **kwargs):
        super().__init__(code, message, **kwargs)


class ValidationError(DashboardError):
    """Erro de validação de entrada"""
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        context = ErrorContext(
            operation="validation",
            details={"field": field} if field else None,
            retry_possible=False
        )
        super().__init__(ErrorCode.VALIDATION_FAILED, message, context, **kwargs)


class APIError(DashboardError):
    """Erro de API externa"""
    def __init__(self, message: str, service: str, status_code: Optional[int] = None, **kwargs):
        code = ErrorCode.API_ERROR
        if status_code == 429:
            code = ErrorCode.API_RATE_LIMITED
        elif status_code == 408:
            code = ErrorCode.API_TIMEOUT
        
        context = ErrorContext(
            operation=f"api_{service}",
            details={"service": service, "status_code": status_code},
            retry_possible=code != ErrorCode.API_RATE_LIMITED
        )
        super().__init__(code, message, context, **kwargs)


def handle_error(
    default_return: Any = None,
    show_user_error: bool = True,
    log_error: bool = True,
    reraise: bool = False
):
    """
    Decorator para tratamento padronizado de erros.
    
    Args:
        default_return: Valor a retornar em caso de erro
        show_user_error: Se deve mostrar erro ao usuário via Streamlit
        log_error: Se deve logar o erro
        reraise: Se deve re-lançar a exceção após tratamento
    
    Exemplo:
        @handle_error(default_return=pd.DataFrame(), show_user_error=True)
        def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = get_logger(func.__module__ or "dashboard")
            
            try:
                return func(*args, **kwargs)
            
            except DashboardError as e:
                # Erro já tratado pela aplicação
                if log_error:
                    logger.error(
                        str(e),
                        code=e.code.name,
                        operation=e.context.operation if e.context else None
                    )
                
                if show_user_error:
                    _show_streamlit_error(e)
                
                if reraise:
                    raise
                
                return default_return
            
            except Exception as e:
                # Erro não tratado - converter para DashboardError
                dashboard_error = DashboardError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Erro em {func.__name__}: {str(e)}",
                    context=ErrorContext(
                        operation=func.__name__,
                        details={"original_error": type(e).__name__}
                    ),
                    original_exception=e
                )
                
                if log_error:
                    logger.error(
                        str(dashboard_error),
                        exception=e,
                        function=func.__name__
                    )
                
                if show_user_error:
                    _show_streamlit_error(dashboard_error)
                
                if reraise:
                    raise dashboard_error from e
                
                return default_return
        
        return wrapper
    return decorator


def _show_streamlit_error(error: DashboardError) -> None:
    """Exibe erro formatado no Streamlit"""
    icon = "⚠️" if error.code.value < 400 else "❌"
    
    if error.context and error.context.retry_possible:
        st.error(f"{icon} {error.user_message}")
        st.caption("💡 Você pode tentar novamente clicando no botão de atualizar.")
    else:
        st.error(f"{icon} {error.user_message}")


def safe_execute(
    operation: Callable[..., T],
    *args,
    default: T = None,
    error_message: str = "Operação falhou",
    **kwargs
) -> T:
    """
    Executa uma operação de forma segura com tratamento de erros.
    
    Args:
        operation: Função a executar
        *args: Argumentos posicionais
        default: Valor padrão em caso de erro
        error_message: Mensagem de erro personalizada
        **kwargs: Argumentos nomeados
    
    Returns:
        Resultado da operação ou valor padrão
    
    Exemplo:
        result = safe_execute(fetch_data, start_date, end_date, default=[])
    """
    logger = get_logger("safe_execute")
    
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        logger.warning(error_message, exception=e, operation=operation.__name__)
        return default
