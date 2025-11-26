"""
Componentes de gráficos Plotly
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List, Dict

from config import COLORS, CHART_COLORS


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: Optional[str] = None,
    title: str = "",
    height: int = 400,
    show_markers: bool = True,
    category_orders: Optional[Dict] = None
) -> go.Figure:
    """
    Cria gráfico de linhas com estilo ecosys.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        color: Coluna para cores (opcional)
        title: Título do gráfico
        height: Altura em pixels
        show_markers: Mostrar marcadores nos pontos
        category_orders: Ordem das categorias
    
    Returns:
        Figura Plotly
    """
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        markers=show_markers,
        color_discrete_sequence=CHART_COLORS,
        category_orders=category_orders
    )
    
    fig.update_layout(
        height=height,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color='#ffffff'),
            bgcolor='rgba(0,0,0,0)'
        ),
        xaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            zeroline=False
        ),
        margin=dict(l=20, r=20, t=60, b=40)
    )
    
    if show_markers:
        fig.update_traces(
            line=dict(width=2.5),
            marker=dict(size=8, line=dict(width=1, color='#1a1f2e'))
        )
    
    return fig


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    height: int = 400,
    horizontal: bool = False,
    color_scale: str = "Blues",
    show_text: bool = True
) -> go.Figure:
    """
    Cria gráfico de barras com estilo ecosys.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        title: Título do gráfico
        height: Altura em pixels
        horizontal: Se True, barras horizontais
        color_scale: Escala de cores
        show_text: Mostrar valores nas barras
    
    Returns:
        Figura Plotly
    """
    if horizontal:
        fig = px.bar(
            df, x=y, y=x, title=title,
            orientation='h',
            color=y,
            color_continuous_scale=color_scale,
            text=y if show_text else None
        )
    else:
        fig = px.bar(
            df, x=x, y=y, title=title,
            color=y,
            color_continuous_scale=color_scale,
            text=y if show_text else None
        )
    
    fig.update_layout(
        height=height,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        margin=dict(l=20, r=20, t=60, b=40)
    )
    
    if show_text:
        fig.update_traces(textposition='outside', textfont_size=12)
    
    return fig


def create_funnel_chart(
    stages: List[str],
    values: List[int],
    title: str = "",
    height: int = 400,
    colors: Optional[List[str]] = None
) -> go.Figure:
    """
    Cria gráfico de funil.
    
    Args:
        stages: Lista de nomes das etapas
        values: Lista de valores
        title: Título do gráfico
        height: Altura em pixels
        colors: Lista de cores (opcional)
    
    Returns:
        Figura Plotly
    """
    if colors is None:
        colors = [COLORS['primary'], COLORS['warning'], COLORS['success']]
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        marker=dict(color=colors),
        textfont=dict(size=14, color='white'),
        textposition='inside'
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    )
    
    return fig


def create_histogram(
    df: pd.DataFrame,
    x: str,
    title: str = "",
    height: int = 400,
    nbins: int = 20,
    color: str = "#4A9FFF"
) -> go.Figure:
    """
    Cria histograma com estilo ecosys.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para o histograma
        title: Título do gráfico
        height: Altura em pixels
        nbins: Número de bins
        color: Cor das barras
    
    Returns:
        Figura Plotly
    """
    fig = px.histogram(
        df, x=x, nbins=nbins, title=title,
        color_discrete_sequence=[color],
        text_auto=True
    )
    
    fig.update_layout(
        height=height,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.1,
        xaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)',
            showticklabels=False
        )
    )
    
    fig.update_traces(
        textposition='outside',
        textfont_size=12,
        marker_line_width=1.5
    )
    
    return fig


def create_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: Optional[str] = None,
    size: Optional[str] = None,
    title: str = "",
    height: int = 400,
    hover_data: Optional[List[str]] = None
) -> go.Figure:
    """
    Cria gráfico de dispersão com estilo ecosys.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        color: Coluna para cores (opcional)
        size: Coluna para tamanho (opcional)
        title: Título do gráfico
        height: Altura em pixels
        hover_data: Colunas extras no hover
    
    Returns:
        Figura Plotly
    """
    fig = px.scatter(
        df, x=x, y=y,
        color=color, size=size,
        title=title,
        hover_data=hover_data,
        color_discrete_sequence=CHART_COLORS
    )
    
    fig.update_layout(
        height=height,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True if color else False,
        xaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            tickfont=dict(size=11, color='#CBD5E0'),
            gridcolor='rgba(255,255,255,0.1)'
        )
    )
    
    return fig
