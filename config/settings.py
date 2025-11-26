"""
Configurações centralizadas do Dashboard Kommo
"""
from typing import List, Dict

# ========================================
# CONFIGURAÇÃO DE STATUS DO KOMMO
# ========================================

# Status que indicam que a demo foi concluída
DEMO_COMPLETED_STATUSES: List[str] = [
    "5 - Demonstração realizada",
    "6 - Lead quente",
    "5 - VISITA REALIZADA",
    "6 - EM Negociação",
]

# Status que indicam que o lead saiu do funil (conclusão/encerramento)
FUNNEL_CLOSED_STATUSES: List[str] = [
    "Venda Ganha",
    "Desqualificados",
]

# Todos os status que indicam que o lead não precisa mais de ação
COMPLETED_STATUSES: List[str] = DEMO_COMPLETED_STATUSES + FUNNEL_CLOSED_STATUSES

# Manter compatibilidade com código existente
STATUS_POS_DEMO: List[str] = COMPLETED_STATUSES

# ========================================
# CONFIGURAÇÕES DE CACHE
# ========================================

CACHE_TTL_LEADS: int = 1800      # 30 minutos
CACHE_TTL_IA: int = 3600         # 1 hora
CACHE_TTL_CHAMADAS: int = 1800   # 30 minutos
CACHE_TTL_TEMPO: int = 1800      # 30 minutos

# ========================================
# CONFIGURAÇÕES DE UI
# ========================================

PAGE_CONFIG = {
    "page_title": "Painel de Acompanhamento de Leads - ecosys AUTO",
    "page_icon": "🚗",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Tradução de dias da semana
DIAS_PT: Dict[str, str] = {
    'monday': 'segunda-feira',
    'tuesday': 'terça-feira',
    'wednesday': 'quarta-feira',
    'thursday': 'quinta-feira',
    'friday': 'sexta-feira',
    'saturday': 'sábado',
    'sunday': 'domingo'
}

# ========================================
# PALETA DE CORES
# ========================================

COLORS: Dict[str, str] = {
    'primary': '#20B2AA',       # Teal (ecosys)
    'secondary': '#008B8B',     # Dark Cyan
    'success': '#48bb78',       # Green
    'warning': '#ed8936',       # Orange
    'danger': '#f56565',        # Red
    'info': '#4299e1',          # Blue
    'text': '#ffffff',          # White
    'text_muted': '#CBD5E0',    # Gray
    'background': '#1a1f2e',    # Dark Blue
    'surface': '#2d3748',       # Dark Gray
}

# Cores para gráficos de vendedores
CHART_COLORS: List[str] = [
    '#4A9FFF',  # Azul
    '#FF6B6B',  # Vermelho coral
    '#4ECDC4',  # Teal
    '#FFE66D',  # Amarelo
    '#95E1D3',  # Verde menta
    '#F38181',  # Rosa salmão
    '#AA96DA',  # Roxo lavanda
    '#FF9F43',  # Laranja
    '#26DE81',  # Verde limão
    '#FD79A8',  # Rosa pink
    '#A29BFE',  # Lilás
    '#00CEC9',  # Ciano
]

# ========================================
# CONFIGURAÇÕES DE METAS
# ========================================

META_CONVERSAO_EFETIVAS: float = 0.15  # 15% de conversão
DURACAO_MINIMA_EFETIVA: int = 50       # segundos

# ========================================
# CONFIGURAÇÕES DO KOMMO
# ========================================

KOMMO_BASE_URL: str = "https://atendimentoecosysauto.kommo.com"

# Ramais dos vendedores
VENDEDORES_RAMAIS: Dict[int, int] = {
    14164344: 1012,
    14164336: 1011,
    12476067: 1006,
    14164332: 1013,
}
