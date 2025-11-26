"""
Funções de cálculo de métricas de negócio
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

from config import (
    DEMO_COMPLETED_STATUSES,
    FUNNEL_CLOSED_STATUSES,
    DURACAO_MINIMA_EFETIVA,
)
from utils import safe_divide


def calcular_demos_realizadas(
    df: pd.DataFrame,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None
) -> int:
    """
    Calcula o número de demos realizadas com base na lógica de negócio.
    
    Lógica:
    - Leads com data_demo preenchida E:
      1) Status = "Desqualificados" AND data_demo preenchida AND data_noshow vazia
      OU
      2) data_demo preenchida AND status IN ("5 - Demonstração realizada", "6 - Lead quente", "Venda ganha")
    
    Args:
        df: DataFrame com os leads
        data_inicio: Data inicial do período (opcional)
        data_fim: Data final do período (opcional)
    
    Returns:
        Número de demos realizadas
    """
    if df.empty or 'data_demo' not in df.columns or 'status' not in df.columns:
        return 0
    
    # Aplicar filtro de período se fornecido
    df_filtrado = df.copy()
    
    if data_inicio is not None and data_fim is not None:
        df_filtrado = df_filtrado[
            (df_filtrado['data_demo'].notna()) &
            (df_filtrado['data_demo'] >= pd.Timestamp(data_inicio)) &
            (df_filtrado['data_demo'] <= pd.Timestamp(data_fim))
        ]
    
    # Aplicar lógica de negócio
    demos_realizadas = len(df_filtrado[
        (df_filtrado['data_demo'].notna()) &
        (
            (
                (df_filtrado['status'] == 'Desqualificados') &
                (df_filtrado['data_demo'].notna()) &
                (df_filtrado['data_noshow'].isna())
            ) |
            (
                (df_filtrado['data_demo'].notna()) &
                (df_filtrado['status'].isin(['5 - Demonstração realizada', '6 - Lead quente', 'Venda ganha']))
            )
        )
    ])
    
    return demos_realizadas


def calcular_noshows(
    df: pd.DataFrame,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None
) -> int:
    """
    Calcula o número de no-shows no período.
    
    Args:
        df: DataFrame com os leads
        data_inicio: Data inicial do período (opcional)
        data_fim: Data final do período (opcional)
    
    Returns:
        Número de no-shows
    """
    if df.empty or 'data_noshow' not in df.columns:
        return 0
    
    df_filtrado = df.copy()
    
    if data_inicio is not None and data_fim is not None:
        df_filtrado = df_filtrado[
            (df_filtrado['data_noshow'].notna()) &
            (df_filtrado['data_noshow'] >= pd.Timestamp(data_inicio)) &
            (df_filtrado['data_noshow'] <= pd.Timestamp(data_fim))
        ]
    else:
        df_filtrado = df_filtrado[df_filtrado['data_noshow'].notna()]
    
    return len(df_filtrado)


def calcular_vendas(
    df: pd.DataFrame,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None
) -> int:
    """
    Calcula o número de vendas no período.
    
    Args:
        df: DataFrame com os leads
        data_inicio: Data inicial do período (opcional)
        data_fim: Data final do período (opcional)
    
    Returns:
        Número de vendas
    """
    if df.empty or 'data_venda' not in df.columns:
        return 0
    
    df_filtrado = df.copy()
    
    if data_inicio is not None and data_fim is not None:
        df_filtrado = df_filtrado[
            (df_filtrado['data_venda'].notna()) &
            (df_filtrado['data_venda'] >= pd.Timestamp(data_inicio)) &
            (df_filtrado['data_venda'] <= pd.Timestamp(data_fim))
        ]
    else:
        df_filtrado = df_filtrado[df_filtrado['data_venda'].notna()]
    
    return len(df_filtrado)


def calcular_metricas_periodo(
    df: pd.DataFrame,
    data_inicio: datetime,
    data_fim: datetime
) -> Dict[str, Any]:
    """
    Calcula todas as métricas principais de um período.
    
    Args:
        df: DataFrame com os leads
        data_inicio: Data inicial do período
        data_fim: Data final do período
    
    Returns:
        Dicionário com todas as métricas
    """
    if df.empty:
        return {
            'total_leads': 0,
            'demos_agendadas': 0,
            'demos_realizadas': 0,
            'noshows': 0,
            'vendas': 0,
            'taxa_conversao': 0,
            'taxa_noshow': 0,
        }
    
    # Total de leads criados no período
    total_leads = len(df[
        (df['criado_em'].notna()) &
        (df['criado_em'] >= pd.Timestamp(data_inicio)) &
        (df['criado_em'] <= pd.Timestamp(data_fim))
    ]) if 'criado_em' in df.columns else 0
    
    # Demos agendadas
    demos_agendadas = len(df[
        (df['data_demo'].notna()) &
        (df['data_demo'] >= pd.Timestamp(data_inicio)) &
        (df['data_demo'] <= pd.Timestamp(data_fim))
    ]) if 'data_demo' in df.columns else 0
    
    # Demos realizadas
    demos_realizadas = calcular_demos_realizadas(df, data_inicio, data_fim)
    
    # No-shows
    noshows = calcular_noshows(df, data_inicio, data_fim)
    
    # Vendas
    vendas = calcular_vendas(df, data_inicio, data_fim)
    
    # Taxas
    taxa_conversao = safe_divide(vendas, total_leads) * 100
    taxa_noshow = safe_divide(noshows, demos_agendadas) * 100
    
    return {
        'total_leads': total_leads,
        'demos_agendadas': demos_agendadas,
        'demos_realizadas': demos_realizadas,
        'noshows': noshows,
        'vendas': vendas,
        'taxa_conversao': taxa_conversao,
        'taxa_noshow': taxa_noshow,
    }


def calcular_metricas_chamadas(df_chamadas: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula métricas de chamadas telefônicas.
    
    Args:
        df_chamadas: DataFrame com as chamadas
    
    Returns:
        Dicionário com métricas de chamadas
    """
    if df_chamadas.empty:
        return {
            'total_discagens': 0,
            'total_atendidas': 0,
            'total_efetivas': 0,
            'taxa_atendimento': 0,
            'taxa_efetividade': 0,
            'taxa_conversao_geral': 0,
            'tmd_atendidas': 0,
            'tmd_efetivas': 0,
        }
    
    total_discagens = len(df_chamadas)
    total_atendidas = len(df_chamadas[df_chamadas['causa_desligamento'] == 'Atendida'])
    
    # Ligações efetivas: atendidas com duração > DURACAO_MINIMA_EFETIVA segundos
    if 'efetiva' in df_chamadas.columns:
        total_efetivas = df_chamadas['efetiva'].sum()
    else:
        total_efetivas = len(df_chamadas[
            (df_chamadas['causa_desligamento'] == 'Atendida') &
            (df_chamadas['duration'] > DURACAO_MINIMA_EFETIVA)
        ])
    
    # Taxas
    taxa_atendimento = safe_divide(total_atendidas, total_discagens) * 100
    taxa_efetividade = safe_divide(total_efetivas, total_atendidas) * 100
    taxa_conversao_geral = safe_divide(total_efetivas, total_discagens) * 100
    
    # Tempo médio de duração
    tmd_atendidas = df_chamadas[df_chamadas['causa_desligamento'] == 'Atendida']['duration_minutos'].mean() if 'duration_minutos' in df_chamadas.columns else 0
    
    if 'efetiva' in df_chamadas.columns:
        tmd_efetivas = df_chamadas[df_chamadas['efetiva']]['duration_minutos'].mean() if 'duration_minutos' in df_chamadas.columns else 0
    else:
        tmd_efetivas = 0
    
    return {
        'total_discagens': int(total_discagens),
        'total_atendidas': int(total_atendidas),
        'total_efetivas': int(total_efetivas),
        'taxa_atendimento': taxa_atendimento,
        'taxa_efetividade': taxa_efetividade,
        'taxa_conversao_geral': taxa_conversao_geral,
        'tmd_atendidas': tmd_atendidas if pd.notna(tmd_atendidas) else 0,
        'tmd_efetivas': tmd_efetivas if pd.notna(tmd_efetivas) else 0,
    }


def classificar_ligacao(df_chamadas: pd.DataFrame) -> pd.DataFrame:
    """
    Classifica ligações e adiciona colunas de tipo e efetividade.
    
    Args:
        df_chamadas: DataFrame com as chamadas
    
    Returns:
        DataFrame com colunas adicionais
    """
    if df_chamadas.empty:
        return df_chamadas
    
    df = df_chamadas.copy()
    
    # Classificar tipo de ligação
    df['tipo_ligacao'] = df['causa_desligamento'].apply(
        lambda x: 'Atendida' if x == 'Atendida' else 'Não Atendida'
    )
    
    # Definir ligações efetivas
    df['efetiva'] = (
        (df['causa_desligamento'] == 'Atendida') &
        (df['duration'] > DURACAO_MINIMA_EFETIVA)
    )
    
    return df
