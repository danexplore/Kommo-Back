"""
Componentes Streamlit para Análise de Marketing

Fornece componentes visuais para exibir:
- Dashboard de métricas de marketing
- Gráficos de performance de campanhas
- Tabelas comparativas
- Cards de insights
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional, Dict, Any
from datetime import date

from core.marketing_analytics import (
    MarketingAnalyzer,
    UTMDimension,
    MarketingInsight,
    InsightType,
    CampaignMetrics,
    PeriodComparison
)
from config import CHART_COLORS, COLORS


def render_marketing_summary_cards(analyzer: MarketingAnalyzer) -> None:
    """
    Renderiza cards com métricas resumidas de marketing.
    
    Args:
        analyzer: Instância do MarketingAnalyzer
    """
    summary = analyzer.get_summary_metrics()
    
    if not summary:
        st.info("📊 Sem dados de marketing para exibir.")
        return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "🎯 Campanhas Ativas",
            summary.get('campanhas_ativas', 0),
            help="Campanhas com UTM rastreada"
        )
    
    with col2:
        st.metric(
            "🌐 Fontes",
            summary.get('fontes_ativas', 0),
            help="Fontes de tráfego distintas"
        )
    
    with col3:
        pct = summary.get('pct_rastreamento', 0)
        st.metric(
            "📊 % Rastreado",
            f"{pct:.1f}%",
            help="Percentual de leads com UTM"
        )
    
    with col4:
        st.metric(
            "💰 Total Vendas",
            summary.get('total_vendas', 0),
            help="Vendas no período"
        )
    
    with col5:
        taxa = summary.get('taxa_conversao_geral', 0)
        st.metric(
            "📈 Conversão Geral",
            f"{taxa:.2f}%",
            help="Vendas / Total de Leads"
        )


def render_insights_cards(insights: List[MarketingInsight]) -> None:
    """
    Renderiza cards de insights.
    
    Args:
        insights: Lista de MarketingInsight
    """
    if not insights:
        st.info("💡 Nenhum insight disponível para os dados atuais.")
        return
    
    st.markdown("#### 💡 Insights Automáticos")
    
    # Separar por tipo
    critical = [i for i in insights if i.type == InsightType.CRITICAL]
    warnings = [i for i in insights if i.type == InsightType.WARNING]
    positives = [i for i in insights if i.type == InsightType.POSITIVE]
    opportunities = [i for i in insights if i.type == InsightType.OPPORTUNITY]
    infos = [i for i in insights if i.type == InsightType.INFO]
    
    # Críticos primeiro
    for insight in critical:
        st.error(f"{insight.icon} **{insight.title}**\n\n{insight.description}")
        if insight.recommendation:
            st.caption(f"💡 Recomendação: {insight.recommendation}")
    
    # Alertas
    for insight in warnings:
        st.warning(f"{insight.icon} **{insight.title}**\n\n{insight.description}")
        if insight.recommendation:
            st.caption(f"💡 {insight.recommendation}")
    
    # Positivos e oportunidades em colunas
    if positives or opportunities:
        col1, col2 = st.columns(2)
        
        with col1:
            for insight in positives:
                st.success(f"{insight.icon} **{insight.title}**\n\n{insight.description}")
        
        with col2:
            for insight in opportunities:
                st.info(f"{insight.icon} **{insight.title}**\n\n{insight.description}")
                if insight.recommendation:
                    st.caption(f"💡 {insight.recommendation}")
    
    # Informativos
    for insight in infos:
        st.info(f"{insight.icon} {insight.description}")


def render_campaign_performance_chart(
    analyzer: MarketingAnalyzer,
    dimension: UTMDimension,
    top_n: int = 10
) -> None:
    """
    Renderiza gráfico de performance de campanhas.
    
    Args:
        analyzer: MarketingAnalyzer
        dimension: Dimensão UTM
        top_n: Número de campanhas a exibir
    """
    metrics = analyzer.get_campaign_metrics(dimension, min_leads=1)
    
    if not metrics:
        st.info("📊 Sem dados de campanhas para exibir.")
        return
    
    # Limitar ao top N
    metrics = metrics[:top_n]
    
    # Preparar dados
    data = {
        'Campanha': [m.name[:30] + '...' if len(m.name) > 30 else m.name for m in metrics],
        'Total Leads': [m.total_leads for m in metrics],
        'Demos': [m.demos_realizadas for m in metrics],
        'Vendas': [m.vendas for m in metrics],
        'Desqualificados': [m.desqualificados for m in metrics],
    }
    df = pd.DataFrame(data)
    
    # Gráfico de barras agrupadas
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Total Leads',
        x=df['Campanha'],
        y=df['Total Leads'],
        marker_color=CHART_COLORS[0],
        text=df['Total Leads'],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Demos Realizadas',
        x=df['Campanha'],
        y=df['Demos'],
        marker_color=CHART_COLORS[2],
        text=df['Demos'],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Vendas',
        x=df['Campanha'],
        y=df['Vendas'],
        marker_color=CHART_COLORS[8],
        text=df['Vendas'],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=f'📊 Performance por {dimension.display_name} (Top {top_n})',
        barmode='group',
        height=450,
        xaxis_tickangle=-45,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(b=120)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_conversion_funnel_chart(
    analyzer: MarketingAnalyzer,
    dimension: UTMDimension,
    campaign_name: Optional[str] = None
) -> None:
    """
    Renderiza funil de conversão para uma campanha específica ou geral.
    
    Args:
        analyzer: MarketingAnalyzer
        dimension: Dimensão UTM
        campaign_name: Nome da campanha (None para geral)
    """
    metrics_list = analyzer.get_campaign_metrics(dimension)
    
    if campaign_name:
        metrics = next((m for m in metrics_list if m.name == campaign_name), None)
        if not metrics:
            st.warning(f"Campanha '{campaign_name}' não encontrada.")
            return
        title = f"Funil: {campaign_name}"
    else:
        # Agregar todas
        metrics = CampaignMetrics(name="Geral")
        for m in metrics_list:
            metrics.total_leads += m.total_leads
            metrics.demos_agendadas += m.demos_agendadas
            metrics.demos_realizadas += m.demos_realizadas
            metrics.desqualificados += m.desqualificados
            metrics.vendas += m.vendas
            metrics.noshows += m.noshows
        title = "Funil Geral de Marketing"
    
    # Dados do funil
    stages = ['Leads', 'Demos Agendadas', 'Demos Realizadas', 'Aproveitados', 'Vendas']
    values = [
        metrics.total_leads,
        metrics.demos_agendadas,
        metrics.demos_realizadas,
        metrics.demos_realizadas - metrics.desqualificados,
        metrics.vendas
    ]
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(
            color=[CHART_COLORS[0], CHART_COLORS[2], CHART_COLORS[4], CHART_COLORS[6], CHART_COLORS[8]]
        )
    ))
    
    fig.update_layout(
        title=title,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_desqualification_analysis(
    analyzer: MarketingAnalyzer,
    dimension: UTMDimension
) -> None:
    """
    Renderiza análise detalhada de desqualificação.
    
    Args:
        analyzer: MarketingAnalyzer
        dimension: Dimensão UTM
    """
    metrics = analyzer.get_campaign_metrics(dimension, min_leads=3)
    
    # Filtrar campanhas com desqualificação
    with_desq = [m for m in metrics if m.taxa_desqualificacao > 0]
    
    if not with_desq:
        st.info("✅ Nenhuma desqualificação encontrada no período.")
        return
    
    st.markdown("#### ❌ Análise de Desqualificação por Campanha")
    
    # Gráfico de barras horizontal
    data = {
        'Campanha': [m.name[:25] + '...' if len(m.name) > 25 else m.name for m in with_desq[:10]],
        'Taxa Desqualificação': [m.taxa_desqualificacao for m in with_desq[:10]],
        'Desqualificados': [m.desqualificados for m in with_desq[:10]],
        'Total Demos': [m.demos_realizadas for m in with_desq[:10]]
    }
    df = pd.DataFrame(data)
    df = df.sort_values('Taxa Desqualificação', ascending=True)
    
    fig = px.bar(
        df,
        y='Campanha',
        x='Taxa Desqualificação',
        orientation='h',
        color='Taxa Desqualificação',
        color_continuous_scale='Reds',
        text=df['Taxa Desqualificação'].apply(lambda x: f'{x:.1f}%'),
        hover_data=['Desqualificados', 'Total Demos']
    )
    
    fig.update_layout(
        height=max(300, len(df) * 40),
        showlegend=False,
        xaxis_title="Taxa de Desqualificação (%)",
        yaxis_title=""
    )
    fig.update_traces(textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela com motivos (se disponível)
    df_motivos = analyzer.get_desqualification_analysis(dimension)
    if not df_motivos.empty:
        with st.expander("📋 Ver Motivos de Desqualificação por Campanha"):
            st.dataframe(
                df_motivos,
                column_config={
                    dimension.value: st.column_config.TextColumn(dimension.display_name),
                    'motivos_desqualificacao': st.column_config.TextColumn("Motivo"),
                    'quantidade': st.column_config.NumberColumn("Quantidade"),
                    'percentual': st.column_config.NumberColumn("% do Total", format="%.1f%%")
                },
                hide_index=True,
                height=400
            )


def render_period_comparison(
    analyzer: MarketingAnalyzer,
    dimension: UTMDimension
) -> None:
    """
    Renderiza comparação entre períodos.
    
    Args:
        analyzer: MarketingAnalyzer
        dimension: Dimensão UTM
    """
    comparisons = analyzer.compare_periods(dimension)
    
    if not comparisons:
        st.info("📊 Selecione um período anterior para comparação.")
        return
    
    st.markdown("#### 📈 Comparação com Período Anterior")
    
    # Filtrar campanhas relevantes (existem em ambos os períodos)
    relevant = {k: v for k, v in comparisons.items() if any(c.previous_value > 0 for c in v)}
    
    if not relevant:
        st.info("Não há campanhas com dados em ambos os períodos para comparação.")
        return
    
    # Seletor de campanha
    campaign_names = list(relevant.keys())[:10]  # Top 10
    selected = st.selectbox(
        f"Selecione a {dimension.display_name}:",
        options=campaign_names,
        key=f"comparison_select_{dimension.value}"
    )
    
    if selected:
        comps = relevant[selected]
        
        # Cards de comparação
        cols = st.columns(len(comps))
        
        for i, comp in enumerate(comps):
            with cols[i]:
                delta = f"{comp.percentage_change:+.1f}%"
                delta_color = "normal" if comp.percentage_change >= 0 else "inverse"
                
                # Para desqualificação, inverter a lógica de cor
                if 'Desqualificação' in comp.metric_name:
                    delta_color = "inverse" if comp.percentage_change >= 0 else "normal"
                
                st.metric(
                    label=comp.metric_name,
                    value=f"{comp.current_value:.1f}" if isinstance(comp.current_value, float) and comp.current_value < 100 else f"{int(comp.current_value)}",
                    delta=delta,
                    delta_color=delta_color
                )
                st.caption(f"Anterior: {comp.previous_value:.1f}" if isinstance(comp.previous_value, float) and comp.previous_value < 100 else f"Anterior: {int(comp.previous_value)}")


def render_campaign_ranking(
    analyzer: MarketingAnalyzer,
    dimension: UTMDimension,
    metric: str = "taxa_conversao"
) -> None:
    """
    Renderiza ranking de campanhas por métrica.
    
    Args:
        analyzer: MarketingAnalyzer
        dimension: Dimensão UTM
        metric: Métrica para ordenar
    """
    metrics = analyzer.get_campaign_metrics(dimension, min_leads=5)
    
    if not metrics:
        st.info("📊 Sem dados suficientes para ranking.")
        return
    
    # Filtrar não rastreados
    metrics = [m for m in metrics if '(não rastreado)' not in m.name.lower()]
    
    st.markdown("#### 🏆 Ranking de Campanhas")
    
    # Seletor de métrica
    metric_options = {
        'taxa_conversao': '💰 Taxa de Conversão',
        'taxa_desqualificacao': '❌ Taxa de Desqualificação',
        'total_leads': '👥 Volume de Leads',
        'vendas': '💵 Total de Vendas',
        'eficiencia_funil': '📊 Eficiência do Funil'
    }
    
    selected_metric = st.selectbox(
        "Ordenar por:",
        options=list(metric_options.keys()),
        format_func=lambda x: metric_options[x],
        key=f"ranking_metric_{dimension.value}"
    )
    
    # Ordenar
    reverse = selected_metric not in ['taxa_desqualificacao']
    sorted_metrics = sorted(metrics, key=lambda x: getattr(x, selected_metric, 0), reverse=reverse)
    
    # Exibir top 10
    for i, m in enumerate(sorted_metrics[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        value = getattr(m, selected_metric, 0)
        
        if selected_metric in ['taxa_conversao', 'taxa_desqualificacao', 'eficiencia_funil']:
            value_str = f"{value:.1f}%"
        else:
            value_str = str(int(value))
        
        col1, col2, col3 = st.columns([0.5, 3, 1])
        with col1:
            st.write(medal)
        with col2:
            st.write(m.name[:40] + '...' if len(m.name) > 40 else m.name)
        with col3:
            st.write(f"**{value_str}**")


def render_metrics_table(
    analyzer: MarketingAnalyzer,
    dimension: UTMDimension
) -> None:
    """
    Renderiza tabela completa de métricas.
    
    Args:
        analyzer: MarketingAnalyzer
        dimension: Dimensão UTM
    """
    df = analyzer.get_metrics_dataframe(dimension)
    
    if df.empty:
        st.info("📊 Sem dados para exibir na tabela.")
        return
    
    st.markdown("#### 📋 Tabela Detalhada de Métricas")
    
    # Configuração de colunas
    column_config = {
        dimension.display_name: st.column_config.TextColumn(dimension.display_name, width="large"),
        'Total Leads': st.column_config.NumberColumn("Leads", format="%d"),
        'Demos Agendadas': st.column_config.NumberColumn("Agend.", format="%d"),
        'Demos Realizadas': st.column_config.NumberColumn("Demos", format="%d"),
        'Desqualificados': st.column_config.NumberColumn("Desq.", format="%d"),
        'Vendas': st.column_config.NumberColumn("Vendas", format="%d"),
        'No-shows': st.column_config.NumberColumn("No-show", format="%d"),
        '% Agendamento': st.column_config.NumberColumn("% Agend.", format="%.1f%%"),
        '% Realização': st.column_config.NumberColumn("% Real.", format="%.1f%%"),
        '% Desqualificação': st.column_config.NumberColumn("% Desq.", format="%.1f%%"),
        '% Conversão': st.column_config.NumberColumn("% Conv.", format="%.1f%%"),
        '% No-show': st.column_config.NumberColumn("% N.S.", format="%.1f%%"),
        '% Aproveitamento': st.column_config.NumberColumn("% Aprov.", format="%.1f%%"),
        'Eficiência Funil': st.column_config.NumberColumn("Efic.", format="%.2f%%")
    }
    
    st.dataframe(
        df,
        column_config=column_config,
        hide_index=True,
        height=min(600, len(df) * 35 + 50)
    )
    
    # Botão de download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar CSV",
        data=csv,
        file_name=f"metricas_marketing_{dimension.value}.csv",
        mime="text/csv",
        key=f"download_{dimension.value}"
    )


def render_trend_chart(
    analyzer: MarketingAnalyzer,
    dimension: UTMDimension,
    top_n: int = 5
) -> None:
    """
    Renderiza gráfico de tendência temporal.
    
    Args:
        analyzer: MarketingAnalyzer
        dimension: Dimensão UTM
        top_n: Top N campanhas
    """
    df = analyzer.get_trend_data(dimension, top_n)
    
    if df.empty:
        st.info("📊 Sem dados de tendência disponíveis.")
        return
    
    st.markdown(f"#### 📈 Tendência de Leads por {dimension.display_name} (Top {top_n})")
    
    fig = px.line(
        df,
        x='data',
        y='leads',
        color=dimension.value,
        markers=True,
        labels={
            'data': 'Data',
            'leads': 'Leads',
            dimension.value: dimension.display_name
        }
    )
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_marketing_dashboard(
    df_leads: pd.DataFrame,
    df_leads_anterior: Optional[pd.DataFrame] = None,
    demo_completed_statuses: Optional[List[str]] = None
) -> None:
    """
    Renderiza dashboard completo de marketing.
    
    Args:
        df_leads: DataFrame com leads do período atual
        df_leads_anterior: DataFrame com leads do período anterior
        demo_completed_statuses: Lista de status de demo completada
    """
    st.markdown("### 📣 Análise Avançada de Marketing")
    st.caption("Insights detalhados sobre performance de campanhas, fontes e ROI")
    
    # Criar analyzer
    analyzer = MarketingAnalyzer(
        df_leads=df_leads,
        df_leads_anterior=df_leads_anterior,
        demo_completed_statuses=demo_completed_statuses
    )
    
    # Verificar dimensões disponíveis
    available_dims = analyzer.get_available_dimensions()
    
    if not available_dims:
        st.warning("⚠️ Nenhuma coluna UTM encontrada nos dados. Configure o rastreamento de campanhas.")
        st.info("""
        **Para rastrear campanhas, adicione parâmetros UTM aos seus links:**
        - `utm_campaign` - Nome da campanha
        - `utm_source` - Fonte do tráfego (google, facebook, etc)
        - `utm_medium` - Mídia (cpc, email, social, etc)
        """)
        return
    
    # Seletor de dimensão
    col_dim, col_info = st.columns([1, 2])
    
    with col_dim:
        selected_dim = st.selectbox(
            "📊 Analisar por:",
            options=available_dims,
            format_func=lambda x: f"{x.icon} {x.display_name}",
            key="marketing_dimension_select"
        )
    
    with col_info:
        st.info(f"Mostrando análise por **{selected_dim.display_name}** ({selected_dim.value})")
    
    st.markdown("---")
    
    # Cards resumo
    render_marketing_summary_cards(analyzer)
    
    st.markdown("---")
    
    # Insights automáticos
    insights = analyzer.generate_insights(selected_dim)
    render_insights_cards(insights)
    
    st.markdown("---")
    
    # Abas de análise
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Performance",
        "🔄 Funil",
        "❌ Desqualificação",
        "📈 Comparativo",
        "📋 Dados"
    ])
    
    with tab1:
        render_campaign_performance_chart(analyzer, selected_dim)
        st.markdown("")
        render_trend_chart(analyzer, selected_dim)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            render_conversion_funnel_chart(analyzer, selected_dim)
        
        with col2:
            # Funil de campanha específica
            metrics = analyzer.get_campaign_metrics(selected_dim, min_leads=5)
            campaigns = [m.name for m in metrics if '(não rastreado)' not in m.name.lower()][:10]
            
            if campaigns:
                selected_campaign = st.selectbox(
                    f"Ver funil de {selected_dim.display_name} específica:",
                    options=[''] + campaigns,
                    key="funnel_campaign_select"
                )
                
                if selected_campaign:
                    render_conversion_funnel_chart(analyzer, selected_dim, selected_campaign)
    
    with tab3:
        render_desqualification_analysis(analyzer, selected_dim)
    
    with tab4:
        if df_leads_anterior is not None and not df_leads_anterior.empty:
            render_period_comparison(analyzer, selected_dim)
        else:
            st.info("📊 Para ver a comparação entre períodos, selecione um período com dados históricos disponíveis.")
        
        st.markdown("")
        render_campaign_ranking(analyzer, selected_dim)
    
    with tab5:
        render_metrics_table(analyzer, selected_dim)
