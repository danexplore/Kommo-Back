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
)

from core.helpers import (
    generate_kommo_link,
    format_dataframe_with_links,
)

__all__ = [
    # Metrics
    'calcular_demos_realizadas',
    'calcular_noshows',
    'calcular_vendas',
    'calcular_metricas_periodo',
    'calcular_metricas_chamadas',
    'classificar_ligacao',
    # Helpers
    'generate_kommo_link',
    'format_dataframe_with_links',
]
