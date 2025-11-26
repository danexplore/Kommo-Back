"""
Componentes de métricas e cards
"""
import streamlit as st
from typing import Optional, Union


def metric_with_comparison(
    label: str,
    value: Union[int, float, str],
    previous_value: Union[int, float, None] = None,
    format_str: str = "{:,}",
    help_text: Optional[str] = None,
    inverse_delta: bool = False
) -> None:
    """
    Exibe métrica com comparação ao período anterior.
    
    Args:
        label: Título da métrica
        value: Valor atual
        previous_value: Valor do período anterior (opcional)
        format_str: Formato para exibição do número
        help_text: Texto de ajuda (tooltip)
        inverse_delta: Se True, delta negativo é bom (ex: no-shows)
    """
    # Formatar valor
    if isinstance(value, (int, float)):
        display_value = format_str.format(value).replace(",", ".")
    else:
        display_value = str(value)
    
    # Calcular delta
    delta = None
    delta_color = "normal"
    
    if previous_value is not None and previous_value > 0:
        diff_percent = ((value - previous_value) / previous_value) * 100
        delta = f"{diff_percent:+.1f}%"
        
        if inverse_delta:
            delta_color = "inverse"
    
    st.metric(
        label=label,
        value=display_value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def info_card(title: str, content: str, icon: str = "ℹ️") -> None:
    """
    Exibe card informativo com estilo customizado.
    
    Args:
        title: Título do card
        content: Conteúdo HTML do card
        icon: Emoji/ícone do card
    """
    html = f"""
    <div class="metric-card">
        <h4 style="margin-top: 0; color: #20B2AA;">{icon} {title}</h4>
        {content}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def progress_metric(
    label: str,
    current: int,
    target: int,
    color_success: str = "#48bb78",
    color_warning: str = "#ed8936"
) -> None:
    """
    Exibe métrica com barra de progresso em relação a meta.
    
    Args:
        label: Título da métrica
        current: Valor atual
        target: Valor da meta
        color_success: Cor quando meta atingida
        color_warning: Cor quando abaixo da meta
    """
    if target == 0:
        percentage = 0
    else:
        percentage = min((current / target) * 100, 100)
    
    color = color_success if current >= target else color_warning
    diff = current - target
    
    if diff >= 0:
        msg = f"✅ Meta Atingida! +{diff}"
    else:
        msg = f"📊 Faltam {abs(diff)}"
    
    html = f"""
    <div class="metric-card">
        <h4 style="margin-top: 0; color: #20B2AA;">{label}</h4>
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 15px;">
            <div>
                <span style="font-size: 2rem; font-weight: 800; color: #ffffff;">{current}</span>
                <span style="font-size: 0.9rem; color: #CBD5E0;"> / {target}</span>
            </div>
            <span style="font-size: 1.2rem; font-weight: 700; color: {color};">{percentage:.0f}%</span>
        </div>
        <div style="width: 100%; background-color: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; margin: 10px 0;">
            <div style="width: {percentage}%; background-color: {color}; height: 8px; border-radius: 4px;"></div>
        </div>
        <p style="font-size: 0.9rem; color: {color}; margin-bottom: 0; margin-top: 5px;">{msg}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def status_badge(status: str, color: str = "#20B2AA") -> str:
    """
    Retorna HTML de badge de status.
    
    Args:
        status: Texto do status
        color: Cor do badge
    
    Returns:
        HTML do badge
    """
    return f"""
    <span style="
        background-color: {color}20;
        color: {color};
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    ">{status}</span>
    """
