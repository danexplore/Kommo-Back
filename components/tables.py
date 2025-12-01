"""
Componentes de tabelas formatadas
"""
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List


def styled_dataframe(
    df: pd.DataFrame,
    column_config: Optional[Dict[str, Any]] = None,
    hide_index: bool = True,
    height: Optional[int] = None,
    width: str = "stretch"
) -> None:
    """
    Exibe DataFrame com estilo padronizado.
    
    Args:
        df: DataFrame a exibir
        column_config: Configuração de colunas do Streamlit
        hide_index: Ocultar índice
        height: Altura fixa (opcional)
        width: Largura do componente ('stretch' ou 'content')
    """
    if df.empty:
        st.info("Nenhum dado disponível")
        return
    
    # Calcular altura automática se não especificada
    if height is None:
        height = min(500, len(df) * 35 + 100)
    
    st.dataframe(
        df,
        column_config=column_config,
        hide_index=hide_index,
        height=height,
        width=width
    )


def paginated_dataframe(
    df: pd.DataFrame,
    page_size: int = 20,
    column_config: Optional[Dict[str, Any]] = None,
    key: str = "paginated_df"
) -> None:
    """
    Exibe DataFrame com paginação.
    
    Args:
        df: DataFrame a exibir
        page_size: Itens por página
        column_config: Configuração de colunas
        key: Chave única para o componente
    """
    if df.empty:
        st.info("Nenhum dado disponível")
        return
    
    total_rows = len(df)
    total_pages = (total_rows - 1) // page_size + 1
    
    # Seletor de página
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        page = st.selectbox(
            f"Página (Total: {total_rows} registros)",
            range(1, total_pages + 1),
            key=f"{key}_page"
        )
    
    # Calcular slice
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    # Exibir slice
    st.dataframe(
        df.iloc[start_idx:end_idx],
        column_config=column_config,
        hide_index=True,
        width='stretch'
    )
    
    # Info de paginação
    st.caption(f"Exibindo {start_idx + 1} a {end_idx} de {total_rows}")


def ranking_table(
    df: pd.DataFrame,
    rank_column: str,
    value_column: str,
    title: str = "Ranking",
    show_medals: bool = True,
    top_n: int = 10
) -> None:
    """
    Exibe tabela de ranking com medalhas.
    
    Args:
        df: DataFrame com os dados
        rank_column: Coluna para identificar itens
        value_column: Coluna com valores para ranking
        title: Título da tabela
        show_medals: Mostrar medalhas nos top 3
        top_n: Número de itens a exibir
    """
    if df.empty:
        st.info("Nenhum dado disponível")
        return
    
    # Ordenar e pegar top N
    df_sorted = df.sort_values(value_column, ascending=False).head(top_n).copy()
    df_sorted = df_sorted.reset_index(drop=True)
    
    # Adicionar posição
    if show_medals:
        medals = ['🥇', '🥈', '🥉']
        df_sorted['Posição'] = df_sorted.index.map(
            lambda x: medals[x] if x < 3 else str(x + 1)
        )
    else:
        df_sorted['Posição'] = range(1, len(df_sorted) + 1)
    
    # Reorganizar colunas
    cols = ['Posição'] + [c for c in df_sorted.columns if c != 'Posição']
    df_sorted = df_sorted[cols]
    
    st.markdown(f"**{title}**")
    st.dataframe(df_sorted, hide_index=True, width='stretch')


def summary_table(
    df: pd.DataFrame,
    group_by: str,
    agg_columns: Dict[str, str],
    sort_by: Optional[str] = None,
    ascending: bool = False
) -> pd.DataFrame:
    """
    Cria tabela de resumo agregada.
    
    Args:
        df: DataFrame original
        group_by: Coluna para agrupar
        agg_columns: Dict {coluna: função de agregação}
        sort_by: Coluna para ordenar (opcional)
        ascending: Ordem ascendente
    
    Returns:
        DataFrame agregado
    """
    if df.empty:
        return pd.DataFrame()
    
    df_summary = df.groupby(group_by).agg(agg_columns).reset_index()
    
    if sort_by and sort_by in df_summary.columns:
        df_summary = df_summary.sort_values(sort_by, ascending=ascending)
    
    return df_summary
