"""
Funções auxiliares de links e URLs
"""
import pandas as pd
from typing import Optional

from config import KOMMO_BASE_URL


def generate_kommo_link(lead_id) -> str:
    """
    Gera link para o lead no Kommo CRM.
    
    Args:
        lead_id: ID do lead
    
    Returns:
        URL completa do lead
    """
    if pd.isna(lead_id):
        return ""
    return f"{KOMMO_BASE_URL}/leads/detail/{int(lead_id)}"


def format_dataframe_with_links(
    df: pd.DataFrame,
    id_column: str = 'id',
    name_column: str = 'lead_name'
) -> pd.DataFrame:
    """
    Formata DataFrame adicionando coluna de links clicáveis.
    
    Args:
        df: DataFrame original
        id_column: Nome da coluna com ID do lead
        name_column: Nome da coluna com nome do lead
    
    Returns:
        DataFrame com coluna de link adicionada
    """
    if df.empty:
        return df
    
    df_display = df.copy()
    
    if id_column in df_display.columns:
        df_display['Link Kommo'] = df_display[id_column].apply(
            lambda x: f'<a href="{generate_kommo_link(x)}" target="_blank">Abrir</a>' if pd.notna(x) else ''
        )
    
    return df_display
