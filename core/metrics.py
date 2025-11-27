"""
Funções de cálculo de métricas de negócio
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Any, Optional, List

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
    
    # Usar filtro vetorizado sem .copy() desnecessário
    mask = df['data_demo'].notna()
    
    if data_inicio is not None and data_fim is not None:
        mask &= (df['data_demo'] >= pd.Timestamp(data_inicio)) & (df['data_demo'] <= pd.Timestamp(data_fim))
    
    # Aplicar lógica de negócio vetorizada
    demos_mask = mask & (
        (
            (df['status'] == 'Desqualificados') &
            (df['data_noshow'].isna())
        ) |
        (
            df['status'].isin(['5 - Demonstração realizada', '6 - Lead quente', 'Venda ganha'])
        )
    )
    
    return demos_mask.sum()


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
    
    mask = df['data_noshow'].notna()
    
    if data_inicio is not None and data_fim is not None:
        mask &= (df['data_noshow'] >= pd.Timestamp(data_inicio)) & (df['data_noshow'] <= pd.Timestamp(data_fim))
    
    return mask.sum()


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
    
    mask = df['data_venda'].notna()
    
    if data_inicio is not None and data_fim is not None:
        mask &= (df['data_venda'] >= pd.Timestamp(data_inicio)) & (df['data_venda'] <= pd.Timestamp(data_fim))
    
    return mask.sum()


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
    
    ts_inicio = pd.Timestamp(data_inicio)
    ts_fim = pd.Timestamp(data_fim)
    
    # Total de leads criados no período
    total_leads = 0
    if 'criado_em' in df.columns:
        total_leads = ((df['criado_em'].notna()) & 
                       (df['criado_em'] >= ts_inicio) & 
                       (df['criado_em'] <= ts_fim)).sum()
    
    # Demos agendadas
    demos_agendadas = 0
    if 'data_demo' in df.columns:
        demos_agendadas = ((df['data_demo'].notna()) & 
                          (df['data_demo'] >= ts_inicio) & 
                          (df['data_demo'] <= ts_fim)).sum()
    
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
        'total_leads': int(total_leads),
        'demos_agendadas': int(demos_agendadas),
        'demos_realizadas': int(demos_realizadas),
        'noshows': int(noshows),
        'vendas': int(vendas),
        'taxa_conversao': taxa_conversao,
        'taxa_noshow': taxa_noshow,
    }


def calcular_resumo_diario_vetorizado(
    df: pd.DataFrame,
    data_inicio: date,
    data_fim: date,
    demo_completed_statuses: List[str]
) -> pd.DataFrame:
    """
    Calcula resumo diário usando vetorização com pandas groupby.
    Resolve problema 1.3 (loop manual para resumo diário).
    
    Args:
        df: DataFrame com os leads (deve ter colunas _date pré-computadas)
        data_inicio: Data inicial do período
        data_fim: Data final do período
        demo_completed_statuses: Lista de status que indicam demo realizada
    
    Returns:
        DataFrame com resumo diário
    """
    # Criar range de datas
    date_range = pd.date_range(start=data_inicio, end=data_fim, freq='D')
    df_resumo = pd.DataFrame({'Data': date_range.date})
    df_resumo['Dia'] = date_range.strftime('%A').str.lower()
    
    if df.empty:
        df_resumo['Novos Leads'] = 0
        df_resumo['Agendamentos'] = 0
        df_resumo['Demos no Dia'] = 0
        df_resumo['Noshow'] = 0
        df_resumo['Demos Realizadas'] = 0
        df_resumo['Porcentagem Demos'] = 0.0
        df_resumo['% Noshow'] = 0.0
        return df_resumo
    
    # Usar colunas _date pré-computadas se disponíveis, senão calcular
    def get_date_col(df: pd.DataFrame, col: str) -> pd.Series:
        date_col = f'{col}_date'
        if date_col in df.columns:
            return df[date_col]
        elif col in df.columns:
            return df[col].dt.date
        return pd.Series(dtype='object')
    
    # Novos Leads por dia (usando criado_em)
    if 'criado_em' in df.columns:
        criado_dates = get_date_col(df, 'criado_em')
        novos_leads = criado_dates.value_counts()
        df_resumo = df_resumo.merge(
            novos_leads.rename('Novos Leads').reset_index().rename(columns={'index': 'Data'}),
            on='Data', how='left'
        )
    else:
        df_resumo['Novos Leads'] = 0
    
    # Agendamentos por dia (usando data_agendamento)
    if 'data_agendamento' in df.columns:
        agend_dates = get_date_col(df, 'data_agendamento')
        agendamentos = agend_dates.value_counts()
        df_resumo = df_resumo.merge(
            agendamentos.rename('Agendamentos').reset_index().rename(columns={'index': 'Data'}),
            on='Data', how='left'
        )
    else:
        df_resumo['Agendamentos'] = 0
    
    # Demos no Dia por dia (usando data_demo)
    if 'data_demo' in df.columns:
        demo_dates = get_date_col(df, 'data_demo')
        demos_dia = demo_dates.value_counts()
        df_resumo = df_resumo.merge(
            demos_dia.rename('Demos no Dia').reset_index().rename(columns={'index': 'Data'}),
            on='Data', how='left'
        )
    else:
        df_resumo['Demos no Dia'] = 0
    
    # No-shows por dia (usando data_noshow)
    if 'data_noshow' in df.columns:
        noshow_dates = get_date_col(df, 'data_noshow')
        noshows = noshow_dates.value_counts()
        df_resumo = df_resumo.merge(
            noshows.rename('Noshow').reset_index().rename(columns={'index': 'Data'}),
            on='Data', how='left'
        )
    else:
        df_resumo['Noshow'] = 0
    
    # Demos Realizadas por dia (lógica mais complexa - precisa de filtro por status)
    if 'data_demo' in df.columns and 'status' in df.columns:
        demo_dates = get_date_col(df, 'data_demo')
        
        # Máscara para demos realizadas
        demos_realizadas_mask = (
            (df['data_demo'].notna()) &
            (
                (
                    (df['status'] == 'Desqualificados') &
                    (df['data_noshow'].isna())
                ) |
                (
                    df['status'].isin(demo_completed_statuses)
                )
            )
        )
        
        demos_realizadas = demo_dates[demos_realizadas_mask].value_counts()
        df_resumo = df_resumo.merge(
            demos_realizadas.rename('Demos Realizadas').reset_index().rename(columns={'index': 'Data'}),
            on='Data', how='left'
        )
    else:
        df_resumo['Demos Realizadas'] = 0
    
    # Preencher NaN com 0
    cols_numericas = ['Novos Leads', 'Agendamentos', 'Demos no Dia', 'Noshow', 'Demos Realizadas']
    for col in cols_numericas:
        if col in df_resumo.columns:
            df_resumo[col] = df_resumo[col].fillna(0).astype(int)
    
    # Calcular percentuais
    df_resumo['Porcentagem Demos'] = np.where(
        df_resumo['Demos no Dia'] > 0,
        (df_resumo['Demos Realizadas'] / df_resumo['Demos no Dia'] * 100).round(1),
        0.0
    )
    
    df_resumo['% Noshow'] = np.where(
        df_resumo['Demos no Dia'] > 0,
        (df_resumo['Noshow'] / df_resumo['Demos no Dia'] * 100).round(1),
        0.0
    )
    
    return df_resumo


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
