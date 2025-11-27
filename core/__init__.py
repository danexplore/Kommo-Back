"""
Módulo core do Dashboard Kommo - Lógica de negócio
"""
from core.metrics import (
    calcular_demos_realizadas,
    calcular_noshows,
    calcular_vendas,
    calcular_metricas_periodo,
    calcular_metricas_chamadas,
    classificar_ligacao,
    calcular_resumo_diario_vetorizado,
)

from core.helpers import (
    generate_kommo_link,
    format_dataframe_with_links,
)

from core.logging import (
    get_logger,
    DashboardLogger,
    LogLevel,
    log_execution,
)

from core.exceptions import (
    DashboardError,
    ConnectionError,
    DataError,
    ValidationError,
    APIError,
    ErrorCode,
    ErrorContext,
    handle_error,
    safe_execute,
)

from core.security import (
    InputSanitizer,
    sanitize_text,
    sanitize_ai_prompt,
    RateLimiter,
    RateLimitConfig,
    rate_limit,
    check_rate_limit,
    validate_secrets,
    require_valid_config,
    hash_sensitive_data,
    mask_sensitive_string,
)

from core.marketing_analytics import (
    MarketingAnalyzer,
    UTMDimension,
    MarketingInsight,
    InsightType,
    CampaignMetrics,
    PeriodComparison,
)

__all__ = [
    # Metrics
    'calcular_demos_realizadas',
    'calcular_noshows',
    'calcular_vendas',
    'calcular_metricas_periodo',
    'calcular_metricas_chamadas',
    'classificar_ligacao',
    'calcular_resumo_diario_vetorizado',
    # Helpers
    'generate_kommo_link',
    'format_dataframe_with_links',
    # Logging
    'get_logger',
    'DashboardLogger',
    'LogLevel',
    'log_execution',
    # Exceptions
    'DashboardError',
    'ConnectionError',
    'DataError',
    'ValidationError',
    'APIError',
    'ErrorCode',
    'ErrorContext',
    'handle_error',
    'safe_execute',
    # Security
    'InputSanitizer',
    'sanitize_text',
    'sanitize_ai_prompt',
    'RateLimiter',
    'RateLimitConfig',
    'rate_limit',
    'check_rate_limit',
    'validate_secrets',
    'require_valid_config',
    'hash_sensitive_data',
    'mask_sensitive_string',
    # Marketing Analytics
    'MarketingAnalyzer',
    'UTMDimension',
    'MarketingInsight',
    'InsightType',
    'CampaignMetrics',
    'PeriodComparison',
]
