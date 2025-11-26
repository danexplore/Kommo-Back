"""
Módulo de configurações do Dashboard Kommo
"""
from config.settings import (
    DEMO_COMPLETED_STATUSES,
    FUNNEL_CLOSED_STATUSES,
    COMPLETED_STATUSES,
    STATUS_POS_DEMO,
    CACHE_TTL_LEADS,
    CACHE_TTL_IA,
    CACHE_TTL_CHAMADAS,
    CACHE_TTL_TEMPO,
    PAGE_CONFIG,
    DIAS_PT,
    COLORS,
    CHART_COLORS,
    META_CONVERSAO_EFETIVAS,
    DURACAO_MINIMA_EFETIVA,
    KOMMO_BASE_URL,
    VENDEDORES_RAMAIS,
)

from config.styles import (
    get_main_css,
    get_metric_card_html,
    get_insight_card_html,
)

__all__ = [
    # Status
    'DEMO_COMPLETED_STATUSES',
    'FUNNEL_CLOSED_STATUSES',
    'COMPLETED_STATUSES',
    'STATUS_POS_DEMO',
    # Cache
    'CACHE_TTL_LEADS',
    'CACHE_TTL_IA',
    'CACHE_TTL_CHAMADAS',
    'CACHE_TTL_TEMPO',
    # UI
    'PAGE_CONFIG',
    'DIAS_PT',
    'COLORS',
    'CHART_COLORS',
    # Metas
    'META_CONVERSAO_EFETIVAS',
    'DURACAO_MINIMA_EFETIVA',
    # Kommo
    'KOMMO_BASE_URL',
    'VENDEDORES_RAMAIS',
    # Styles
    'get_main_css',
    'get_metric_card_html',
    'get_insight_card_html',
]
