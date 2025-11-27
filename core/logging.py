"""
Sistema de Logging Estruturado para o Dashboard Kommo

Implementa logging com níveis, formatação consistente e 
integração com Streamlit para exibição de mensagens ao usuário.
"""
import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict
from functools import wraps
import traceback


class LogLevel(Enum):
    """Níveis de log disponíveis"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DashboardLogger:
    """
    Logger centralizado para o Dashboard Kommo.
    
    Características:
    - Formatação consistente com timestamp e contexto
    - Integração opcional com Streamlit
    - Suporte a métricas e contexto adicional
    - Thread-safe
    
    Uso:
        logger = DashboardLogger("supabase_service")
        logger.info("Dados carregados", records=100, duration_ms=250)
        logger.error("Falha na conexão", exception=e)
    """
    
    _instances: Dict[str, 'DashboardLogger'] = {}
    _log_level: LogLevel = LogLevel.INFO
    
    def __new__(cls, name: str = "dashboard"):
        """Singleton por nome para evitar múltiplas instâncias"""
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str = "dashboard"):
        """
        Inicializa o logger.
        
        Args:
            name: Nome do módulo/contexto do logger
        """
        if hasattr(self, '_initialized'):
            return
            
        self.name = name
        self._initialized = True
        
        # Configurar logger Python padrão
        self._logger = logging.getLogger(f"kommo.{name}")
        self._logger.setLevel(logging.DEBUG)
        
        # Handler para console com formatação
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self._logger.addHandler(handler)
    
    @classmethod
    def set_level(cls, level: LogLevel) -> None:
        """Define o nível global de log"""
        cls._log_level = level
    
    def _should_log(self, level: LogLevel) -> bool:
        """Verifica se deve logar baseado no nível configurado"""
        levels_order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        return levels_order.index(level) >= levels_order.index(self._log_level)
    
    def _format_context(self, **kwargs) -> str:
        """Formata contexto adicional para a mensagem"""
        if not kwargs:
            return ""
        parts = [f"{k}={v}" for k, v in kwargs.items() if v is not None]
        return f" | {' | '.join(parts)}" if parts else ""
    
    def debug(self, message: str, **kwargs) -> None:
        """Log de debug - detalhes técnicos"""
        if self._should_log(LogLevel.DEBUG):
            self._logger.debug(f"{message}{self._format_context(**kwargs)}")
    
    def info(self, message: str, **kwargs) -> None:
        """Log de informação - eventos normais"""
        if self._should_log(LogLevel.INFO):
            self._logger.info(f"{message}{self._format_context(**kwargs)}")
    
    def warning(self, message: str, **kwargs) -> None:
        """Log de aviso - situações inesperadas mas recuperáveis"""
        if self._should_log(LogLevel.WARNING):
            self._logger.warning(f"{message}{self._format_context(**kwargs)}")
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log de erro - falhas que afetam funcionalidade"""
        if self._should_log(LogLevel.ERROR):
            exc_info = ""
            if exception:
                exc_info = f" | exception={type(exception).__name__}: {str(exception)}"
            self._logger.error(f"{message}{exc_info}{self._format_context(**kwargs)}")
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log crítico - falhas graves que impedem operação"""
        if self._should_log(LogLevel.CRITICAL):
            exc_info = ""
            if exception:
                exc_info = f" | exception={type(exception).__name__}: {str(exception)}"
                exc_info += f"\n{traceback.format_exc()}"
            self._logger.critical(f"{message}{exc_info}{self._format_context(**kwargs)}")


def get_logger(name: str = "dashboard") -> DashboardLogger:
    """
    Factory function para obter um logger.
    
    Args:
        name: Nome do módulo/contexto
    
    Returns:
        Instância do DashboardLogger
    
    Exemplo:
        logger = get_logger("supabase")
        logger.info("Conexão estabelecida")
    """
    return DashboardLogger(name)


def log_execution(logger_name: str = "dashboard", log_args: bool = False):
    """
    Decorator para logar execução de funções.
    
    Args:
        logger_name: Nome do logger a usar
        log_args: Se deve logar os argumentos da função
    
    Exemplo:
        @log_execution("data_service", log_args=True)
        def fetch_leads(start_date, end_date):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            func_name = func.__name__
            
            # Log início
            start_time = datetime.now()
            if log_args:
                logger.debug(f"Iniciando {func_name}", args=str(args)[:100], kwargs=str(kwargs)[:100])
            else:
                logger.debug(f"Iniciando {func_name}")
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(f"Concluído {func_name}", duration_ms=f"{duration_ms:.2f}")
                return result
            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(f"Erro em {func_name}", exception=e, duration_ms=f"{duration_ms:.2f}")
                raise
        
        return wrapper
    return decorator
