"""
Módulo de serviços do Dashboard Kommo
"""
from services.supabase_service import (
    init_supabase,
    get_supabase,
    get_leads_data,
    get_leads_by_criado_em,
    get_all_leads_for_summary,
    get_tempo_por_etapa,
    get_chamadas_vendedores,
    get_hour_noshow_analitycs,
)

from services.gemini_service import (
    init_gemini,
    get_gemini,
    gerar_insights_ia,
    chat_com_dados,
)

__all__ = [
    # Supabase
    'init_supabase',
    'get_supabase',
    'get_leads_data',
    'get_leads_by_criado_em',
    'get_all_leads_for_summary',
    'get_tempo_por_etapa',
    'get_chamadas_vendedores',
    'get_hour_noshow_analitycs',
    # Gemini
    'init_gemini',
    'get_gemini',
    'gerar_insights_ia',
    'chat_com_dados',
]
