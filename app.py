import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import plotly.express as px

# Timezone de Brasília (GMT-03:00)
TZ_BRASILIA = timezone(timedelta(hours=-3))

# Importar módulos refatorados
from config import (
    DEMO_COMPLETED_STATUSES,
    FUNNEL_CLOSED_STATUSES,
    COMPLETED_STATUSES,
    STATUS_POS_DEMO,
    COLORS,
    CHART_COLORS,
    DIAS_PT,
    PAGE_CONFIG,
    META_CONVERSAO_EFETIVAS,
    DURACAO_MINIMA_EFETIVA,
    get_main_css,
)
from services import (
    init_supabase,
    get_supabase,
    init_gemini,
    get_gemini,
    get_leads_data as service_get_leads_data,
    get_all_leads_for_summary,
    get_chamadas_vendedores as service_get_chamadas,
    get_tempo_por_etapa,
)
from core import (
    generate_kommo_link,
    calcular_demos_realizadas,
    calcular_noshows,
    calcular_vendas,
    calcular_metricas_chamadas,
    classificar_ligacao,
)
from utils import safe_divide, format_number, format_percentage

# Configuração da página
st.set_page_config(**PAGE_CONFIG)

# Inicializar serviços
supabase = get_supabase()
gemini_client = get_gemini()

# Aplicar CSS customizado
st.markdown(get_main_css(), unsafe_allow_html=True)

# CSS adicional específico do app (extensões do tema base)
st.markdown("""
    <style>
    /* Métricas - Teal e Silver */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(45, 55, 72, 0.8) 0%, rgba(26, 31, 46, 0.8) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(32, 178, 170, 0.3);
        box-shadow: 0 8px 32px 0 rgba(32, 178, 170, 0.15);
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        color: #20B2AA;
        text-shadow: 0 2px 8px rgba(32, 178, 170, 0.3);
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: #CBD5E0;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 0.9rem;
        color: #20B2AA;
    }
    
    /* Tabelas - Silver e Teal */
    .stDataFrame {
        background: linear-gradient(135deg, rgba(45, 55, 72, 0.95) 0%, rgba(26, 31, 46, 0.95) 100%) !important;
        border-radius: 12px;
        border: 2px solid rgba(32, 178, 170, 0.3) !important;
        box-shadow: 0 8px 32px 0 rgba(32, 178, 170, 0.15);
        overflow: hidden;
    }
    
    .stDataFrame th {
        background: linear-gradient(135deg, rgba(32, 178, 170, 0.25) 0%, rgba(0, 139, 139, 0.15) 100%) !important;
        color: #C0C0C0 !important;
        font-weight: 700;
        border: none !important;
        border-bottom: 2px solid rgba(32, 178, 170, 0.3) !important;
        padding: 12px !important;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.5px;
    }
    
    .stDataFrame td {
        border-color: rgba(32, 178, 170, 0.15) !important;
        color: #ffffff !important;
        padding: 10px 12px !important;
        border-bottom: 1px solid rgba(32, 178, 170, 0.08) !important;
    }
    
    .stDataFrame tr {
        background-color: transparent !important;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: rgba(32, 178, 170, 0.12) !important;
        border-left: 3px solid #20B2AA !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background-color: rgba(32, 178, 170, 0.03) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# get_leads_data e get_chamadas_vendedores importados de services
# Alias para manter compatibilidade com código existente
get_leads_data = service_get_leads_data

def format_dataframe_with_links(df, id_column='id', name_column='lead_name'):
    """Formata DataFrame com links clicáveis"""
    if df.empty:
        return df
    
    df_display = df.copy()
    
    # Criar coluna de link
    if id_column in df_display.columns:
        df_display['Link Kommo'] = df_display[id_column].apply(
            lambda x: f'<a href="{generate_kommo_link(x)}" target="_blank">Abrir</a>' if pd.notna(x) else ''
        )
    
    return df_display

@st.cache_data(ttl=3600)  # Cache de 1 hora
def gerar_insights_ia(metricas_atual, metricas_anterior, periodo_descricao):
    """Gera insights usando IA do Google Gemini"""
    
    if not gemini_client:
        return None
    
    try:
        # Calcular variações
        var_leads = metricas_atual['total_leads'] - metricas_anterior['total_leads']
        var_leads_pct = ((metricas_atual['total_leads'] - metricas_anterior['total_leads']) / metricas_anterior['total_leads'] * 100) if metricas_anterior['total_leads'] > 0 else 0
        
        var_demo = metricas_atual['leads_com_demo'] - metricas_anterior['leads_com_demo']
        var_demo_pct = ((metricas_atual['leads_com_demo'] - metricas_anterior['leads_com_demo']) / metricas_anterior['leads_com_demo'] * 100) if metricas_anterior['leads_com_demo'] > 0 else 0
        
        var_demos_real = metricas_atual['demos_realizadas'] - metricas_anterior['demos_realizadas']
        var_demos_real_pct = ((metricas_atual['demos_realizadas'] - metricas_anterior['demos_realizadas']) / metricas_anterior['demos_realizadas'] * 100) if metricas_anterior['demos_realizadas'] > 0 else 0
        
        var_noshow = metricas_atual['noshow_count'] - metricas_anterior['noshow_count']
        var_noshow_pct = ((metricas_atual['noshow_count'] - metricas_anterior['noshow_count']) / metricas_anterior['noshow_count'] * 100) if metricas_anterior['noshow_count'] > 0 else 0
        
        var_convertidos = metricas_atual['leads_convertidos'] - metricas_anterior['leads_convertidos']
        var_convertidos_pct = ((metricas_atual['leads_convertidos'] - metricas_anterior['leads_convertidos']) / metricas_anterior['leads_convertidos'] * 100) if metricas_anterior['leads_convertidos'] > 0 else 0
        
        # Preparar dados para análise
        prompt = f"""Você é um analista de dados especializado em vendas e CRM. Analise os seguintes dados de performance de leads e forneça insights acionáveis em português do Brasil.

PERÍODO ANALISADO: {periodo_descricao}

MÉTRICAS DO PERÍODO ATUAL:
- Total de Leads: {metricas_atual['total_leads']}
- Leads com Demo Agendada: {metricas_atual['leads_com_demo']} ({metricas_atual['pct_com_demo']:.1f}% dos leads)
- Demos Realizadas: {metricas_atual['demos_realizadas']}
- No-shows: {metricas_atual['noshow_count']}
- Leads Convertidos: {metricas_atual['leads_convertidos']} ({metricas_atual['taxa_conversao']:.1f}% dos leads)

COMPARAÇÃO COM PERÍODO ANTERIOR:
- Total de Leads: {metricas_anterior['total_leads']} (Variação: {var_leads:+d}, {var_leads_pct:+.1f}%)
- Leads com Demo: {metricas_anterior['leads_com_demo']} (Variação: {var_demo:+d}, {var_demo_pct:+.1f}%)
- Demos Realizadas: {metricas_anterior['demos_realizadas']} (Variação: {var_demos_real:+d}, {var_demos_real_pct:+.1f}%)
- No-shows: {metricas_anterior['noshow_count']} (Variação: {var_noshow:+d})
- Convertidos: {metricas_anterior['leads_convertidos']} (Variação: {var_convertidos:+d}, {var_convertidos_pct:+.1f}%)

Por favor, forneça:
1. Um resumo executivo (2-3 frases) sobre a performance geral
2. Identifique o principal gargalo no funil de vendas
3. Liste 3 recomendações práticas e acionáveis para melhorar os resultados

Utilize um markdown leve para formatação da resposta.
Seja direto, objetivo e use linguagem de negócios. Foque em insights que gerem ação."""

        # Combinar system prompt com user prompt para Gemini
        full_prompt = f"""Você é um analista de vendas experiente. Forneça insights diretos e acionáveis.

{prompt}"""
        
        response = gemini_client.generate_content(full_prompt)
        
        return response.text
        
    except Exception as e:
        return f"❌ **Erro ao gerar insights:** {str(e)}"

def chat_com_dados(mensagem_usuario, metricas_atual, metricas_anterior, periodo_descricao, historico_chat):
    """Realiza conversa com IA sobre os dados"""
    
    if not gemini_client:
        return "Erro: Google Gemini não configurado"
    
    try:
        # Preparar contexto dos dados
        contexto_dados = f"""
CONTEXTO DOS DADOS (Período: {periodo_descricao}):
- Total de Leads: {metricas_atual['total_leads']} (variação: {metricas_atual['total_leads'] - metricas_anterior['total_leads']:+d})
- Leads com Demo: {metricas_atual['leads_com_demo']} (variação: {metricas_atual['leads_com_demo'] - metricas_anterior['leads_com_demo']:+d})
- Demos Realizadas: {metricas_atual['demos_realizadas']} (variação: {metricas_atual['demos_realizadas'] - metricas_anterior['demos_realizadas']:+d})
- No-shows: {metricas_atual['noshow_count']} (variação: {metricas_atual['noshow_count'] - metricas_anterior['noshow_count']:+d})
- Leads Convertidos: {metricas_atual['leads_convertidos']} ({metricas_atual['taxa_conversao']:.1f}%)
- Leads com Demo Anterior: {metricas_anterior['leads_com_demo']}
- Demos Realizadas Anterior: {metricas_anterior['demos_realizadas']}
- No-shows Anterior: {metricas_anterior['noshow_count']}
- Leads Convertidos Anterior: {metricas_anterior['leads_convertidos']}
"""
        
        # Construir prompt completo com contexto e histórico
        prompt_completo = f"""Você é um assistente especializado em análise de vendas e CRM. 
Você tem acesso aos dados atuais de performance de leads e pode responder perguntas sobre tendências, 
recomendações e análises dos dados.

{contexto_dados}

Responda em português do Brasil, de forma conversacional e profissional.

"""
        
        # Adicionar histórico de chat ao prompt
        if historico_chat:
            prompt_completo += "\n--- HISTÓRICO DA CONVERSA ---\n"
            for msg_hist in historico_chat:
                role_label = "Assistente" if msg_hist["role"] == "assistant" else "Usuário"
                prompt_completo += f"{role_label}: {msg_hist['content']}\n\n"
        
        # Adicionar mensagem atual
        prompt_completo += f"\nUsuário: {mensagem_usuario}\n\nAssistente:"
        
        # Chamar API do Gemini
        response = gemini_client.generate_content(prompt_completo)
        
        return response.text
        
    except Exception as e:
        return f"Erro ao processar sua pergunta: {str(e)}"

# Header
st.title("🚗 Painel de Acompanhamento de Leads - ecosys AUTO")
st.markdown("---")

# Sidebar - Logo e Filtros Globais
# Adicionar logo no sidebar
try:
    st.sidebar.image("logo_ecosys_auto.png", use_container_width=True)
    st.sidebar.markdown("---")
except:
    pass  # Se a logo não existir, apenas pular

st.sidebar.header("🔍 Filtros Globais")

# Filtro de Período
st.sidebar.subheader("📅 Período")

# Seletor rápido de período
periodo_rapido = st.sidebar.selectbox(
    "Período rápido",
    ["Últimos 7 dias", "Esse mês", "Mês passado", "Personalizado"],
    index=0
)

# Calcular datas baseado no período selecionado
hoje = datetime.now(TZ_BRASILIA).date()

if periodo_rapido == "Últimos 7 dias":
    data_inicio = hoje - timedelta(days=7)
    data_fim = hoje
elif periodo_rapido == "Esse mês":
    data_inicio = hoje.replace(day=1)
    data_fim = hoje
elif periodo_rapido == "Mês passado":
    primeiro_dia_mes_atual = hoje.replace(day=1)
    ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)
    data_inicio = ultimo_dia_mes_passado.replace(day=1)
    data_fim = ultimo_dia_mes_passado
else:  # Personalizado
    # Para modo personalizado, usar inputs de data
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        data_inicio = st.date_input(
            "De",
            value=hoje - timedelta(days=30),
            max_value=datetime.now(TZ_BRASILIA),
            format="DD/MM/YYYY",
            key="data_inicio_custom"
        )
    
    with col2:
        data_fim = st.date_input(
            "Até",
            value=hoje,
            max_value=datetime.now(TZ_BRASILIA),
            format="DD/MM/YYYY",
            key="data_fim_custom"
        )
    
    if data_inicio > data_fim:
        st.sidebar.error("⚠️ Data inicial não pode ser maior que data final!")
        st.stop()

# Carregar todos os dados primeiro (sem filtro de vendedor)
with st.spinner("⏳ Carregando dados..."):
    df_leads_all = get_leads_data(
        datetime.combine(data_inicio, datetime.min.time()),
        datetime.combine(data_fim, datetime.max.time()),
        None  # Sem filtro de vendedor inicialmente
    )

# Filtro de Vendedor - baseado nos dados carregados
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Vendedores")

if not df_leads_all.empty and 'vendedor' in df_leads_all.columns:
    vendedores_disponiveis = sorted(df_leads_all['vendedor'].dropna().unique().tolist())
    
    if vendedores_disponiveis:
        vendedores_selecionados = st.sidebar.multiselect(
            "Selecione os vendedores",
            options=vendedores_disponiveis,
            default=vendedores_disponiveis,
            key="vendedores_filter"
        )
    else:
        vendedores_selecionados = []
        st.sidebar.info("Nenhum vendedor encontrado na base")
else:
    vendedores_selecionados = []
    st.sidebar.info("Nenhum vendedor encontrado na base")

# Filtro de Pipeline - baseado nos dados carregados
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Pipelines")

if not df_leads_all.empty and 'pipeline' in df_leads_all.columns:
    pipelines_disponiveis = sorted(df_leads_all['pipeline'].dropna().unique().tolist())
    
    if pipelines_disponiveis:
        st.sidebar.write("Selecione os pipelines:")
        pipelines_selecionados = []
        for pipeline in pipelines_disponiveis:
            if st.sidebar.checkbox(pipeline, value=True, key=f"pipeline_{pipeline}"):
                pipelines_selecionados.append(pipeline)
    else:
        pipelines_selecionados = []
        st.sidebar.info("Nenhum pipeline encontrado na base")
else:
    pipelines_selecionados = []
    st.sidebar.info("Nenhum pipeline encontrado na base")

# Botão de atualizar
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar Dados", use_container_width=True, key="refresh_btn"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"📅 Última atualização: {datetime.now(TZ_BRASILIA).strftime('%d/%m/%Y %H:%M')}")

# Aplicar filtros aos dados carregados
df_leads = df_leads_all.copy()

# Filtrar por vendedor
if vendedores_selecionados:
    df_leads = df_leads[df_leads['vendedor'].isin(vendedores_selecionados)]

if df_leads.empty:
    st.warning("⚠️ Nenhum lead encontrado para os filtros selecionados.")
    st.stop()

# Aplicar filtro de pipeline
if pipelines_selecionados:
    df_leads = df_leads[df_leads['pipeline'].isin(pipelines_selecionados)]
    
    if df_leads.empty:
        st.warning("⚠️ Nenhum lead encontrado para os pipelines selecionados.")
        st.stop()

# Aplicar lógica de negócio
hoje = pd.Timestamp(datetime.now(TZ_BRASILIA).date())

# ========================================
# BUSCAR DADOS DO MÊS ANTERIOR PARA COMPARAÇÃO
# ========================================
# Calcular período do mês anterior (mesmo intervalo de dias)
dias_periodo = (data_fim - data_inicio).days
data_inicio_anterior = data_inicio - timedelta(days=dias_periodo + 1)
data_fim_anterior = data_fim - timedelta(days=dias_periodo + 1)

# Buscar dados do período anterior
with st.spinner("⏳ Calculando comparações..."):
    df_leads_anterior = get_leads_data(
        datetime.combine(data_inicio_anterior, datetime.min.time()),
        datetime.combine(data_fim_anterior, datetime.max.time()),
        None  # Sem filtro de vendedor para comparação geral
    )
    
    # Aplicar mesmos filtros de vendedor e pipeline
    if vendedores_selecionados and not df_leads_anterior.empty:
        df_leads_anterior = df_leads_anterior[df_leads_anterior['vendedor'].isin(vendedores_selecionados)]
    
    if pipelines_selecionados and not df_leads_anterior.empty:
        df_leads_anterior = df_leads_anterior[df_leads_anterior['pipeline'].isin(pipelines_selecionados)]

# ========================================
# MÉTRICAS PRINCIPAIS (KPIs)
# ========================================
st.markdown("### 📊 Visão Geral do Período")

col1, col2, col25, col4 = st.columns(4)

with col1:
    # Período atual
    total_leads = len(df_leads.loc[(df_leads['criado_em'] >= pd.Timestamp(datetime.combine(data_inicio, datetime.min.time()))) & (df_leads['criado_em'] <= pd.Timestamp(datetime.combine(data_fim, datetime.max.time())))])
    leads_convertidos = len(df_leads[df_leads['data_venda'].notna() &
                                  (df_leads['data_venda'] >= pd.Timestamp(datetime.combine(data_inicio, datetime.min.time()))) &
                                  (df_leads['data_venda'] <= pd.Timestamp(datetime.combine(data_fim, datetime.max.time())))])
    
    # Período anterior
    total_leads_anterior = len(df_leads_anterior.loc[(df_leads_anterior['criado_em'] >= pd.Timestamp(datetime.combine(data_inicio_anterior, datetime.min.time()))) & (df_leads_anterior['criado_em'] <= pd.Timestamp(datetime.combine(data_fim_anterior, datetime.max.time())))]) if not df_leads_anterior.empty else 0
    
    # Calcular diferença
    if total_leads_anterior > 0:
        diferenca_leads = total_leads - total_leads_anterior
        pct_diferenca = ((total_leads - total_leads_anterior) / total_leads_anterior) * 100
        delta_text = f"{diferenca_leads:+d} leads ({pct_diferenca:+.1f}%)"
        st.metric("📥 Total de Leads", f"{total_leads:,}".replace(",", "."), delta=delta_text)
    else:
        st.metric("📥 Total de Leads", f"{total_leads:,}".replace(",", "."), delta="Sem comparação")
    
    if total_leads > 0:
        taxa_conversao_total = (leads_convertidos / total_leads) * 100

with col2:
    # Período atual
    leads_com_demo = len(df_leads[df_leads['data_demo'].notna() &
                                 (df_leads['data_demo'] >= pd.Timestamp(datetime.combine(data_inicio, datetime.min.time()))) &
                                 (df_leads['data_demo'] <= pd.Timestamp(datetime.combine(data_fim, datetime.max.time())))])
    
    # Período anterior
    leads_com_demo_anterior = len(df_leads_anterior[df_leads_anterior['data_demo'].notna() &
                                 (df_leads_anterior['data_demo'] >= pd.Timestamp(datetime.combine(data_inicio_anterior, datetime.min.time()))) &
                                 (df_leads_anterior['data_demo'] <= pd.Timestamp(datetime.combine(data_fim_anterior, datetime.max.time())))]) if not df_leads_anterior.empty else 0
    
    # Calcular diferença
    if leads_com_demo_anterior > 0:
        diferenca_demo = leads_com_demo - leads_com_demo_anterior
        pct_diferenca_demo = ((leads_com_demo - leads_com_demo_anterior) / leads_com_demo_anterior) * 100
        delta_text_demo = f"{diferenca_demo:+d} ({pct_diferenca_demo:+.1f}%)"
        st.metric("📅 Com Demo", f"{leads_com_demo:,}".replace(",", "."), delta=delta_text_demo)
    else:
        st.metric("📅 Com Demo", f"{leads_com_demo:,}".replace(",", "."), delta="Sem comparação")

with col25:
    # Período atual - Reuniões Realizadas (usando função centralizada)
    demos_realizadas = calcular_demos_realizadas(
        df_leads,
        datetime.combine(data_inicio, datetime.min.time()),
        datetime.combine(data_fim, datetime.max.time())
    )
    
    # Período anterior - Demos Realizadas
    demos_realizadas_anterior = calcular_demos_realizadas(
        df_leads_anterior,
        datetime.combine(data_inicio_anterior, datetime.min.time()),
        datetime.combine(data_fim_anterior, datetime.max.time())
    ) if not df_leads_anterior.empty else 0
    
    # Calcular diferença demos realizadas
    if demos_realizadas_anterior > 0:
        diferenca_demos_real = demos_realizadas - demos_realizadas_anterior
        pct_diferenca_demos = ((demos_realizadas - demos_realizadas_anterior) / demos_realizadas_anterior) * 100
        delta_text_demos = f"{diferenca_demos_real:+d} ({pct_diferenca_demos:+.1f}%)"
        st.metric("🎯 Demos Realizadas", f"{demos_realizadas:,}".replace(",", "."), delta=delta_text_demos)
    else:
        st.metric("🎯 Demos Realizadas", f"{demos_realizadas:,}".replace(",", "."), delta="Sem comparação")
    
    # Calcular taxa de noshow período atual (usando função centralizada)
    noshow_count = calcular_noshows(
        df_leads,
        datetime.combine(data_inicio, datetime.min.time()),
        datetime.combine(data_fim, datetime.max.time())
    )
    
    # Calcular taxa de noshow período anterior
    noshow_count_anterior = calcular_noshows(
        df_leads_anterior,
        datetime.combine(data_inicio_anterior, datetime.min.time()),
        datetime.combine(data_fim_anterior, datetime.max.time())
    ) if not df_leads_anterior.empty else 0
    
    # Calcular diferença no-show
    if noshow_count_anterior > 0 or noshow_count > 0:
        diferenca_noshow = noshow_count - noshow_count_anterior
        if noshow_count_anterior > 0:
            pct_diferenca_noshow = ((noshow_count - noshow_count_anterior) / noshow_count_anterior) * 100
            delta_text_noshow = f"{diferenca_noshow:+d} ({pct_diferenca_noshow:+.1f}%)"
        else:
            delta_text_noshow = f"{diferenca_noshow:+d}"
        st.metric("📉 No-show", f"{noshow_count:,}".replace(",", "."), delta=delta_text_noshow, delta_color="inverse")
    else:
        st.metric("📉 No-show", f"{noshow_count:,}".replace(",", "."), delta="0")

with col4:
    # Período anterior - Convertidos
    leads_convertidos_anterior = len(df_leads_anterior[df_leads_anterior['data_venda'].notna() &
                                  (df_leads_anterior['data_venda'] >= pd.Timestamp(datetime.combine(data_inicio_anterior, datetime.min.time()))) &
                                  (df_leads_anterior['data_venda'] <= pd.Timestamp(datetime.combine(data_fim_anterior, datetime.max.time())))]) if not df_leads_anterior.empty else 0
    
    # Calcular diferença convertidos
    if leads_convertidos_anterior > 0:
        diferenca_convertidos = leads_convertidos - leads_convertidos_anterior
        pct_diferenca_convertidos = ((leads_convertidos - leads_convertidos_anterior) / leads_convertidos_anterior) * 100
        delta_text_convertidos = f"{diferenca_convertidos:+d} ({pct_diferenca_convertidos:+.1f}%)"
        st.metric("✅ Convertidos", f"{leads_convertidos:,}".replace(",", "."), delta=delta_text_convertidos)
    else:
        st.metric("✅ Convertidos", f"{leads_convertidos:,}".replace(",", "."), delta="Sem comparação")

st.markdown("---")

# ========================================
# ABAS PRINCIPAIS
# ========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🚨 Leads com Atenção",
    "🤖 Insights IA",
    "📆 Demos de Hoje",
    "📅 Resumo Diário",
    "🔍 Detalhes dos Leads",
    "⏱️ Tempo por Etapa",
    "📞 Produtividade do Vendedor",
    "💰 Mural de Vendas",
    "✅ Demos Realizadas"
])

# ========================================
# ABA 1: LEADS QUE EXIGEM ATUALIZAÇÃO
# ========================================
with tab1:
    # Calcular leads que exigem atualização
    leads_atualizacao = df_leads[
        (df_leads['data_demo'] < hoje) &
        (df_leads['data_noshow'].isna()) &
        (df_leads['data_venda'].isna()) &
        (~df_leads['status'].isin(STATUS_POS_DEMO))
    ].copy()
    leads_atualizacao_count = len(leads_atualizacao)
    
    st.markdown(f"### 🚨 Leads que Exigem Atualização ({leads_atualizacao_count})")
    st.caption("Leads com demo vencida que precisam ter o status atualizado")
    
    if not leads_atualizacao.empty:
        # Ordenar por data_demo (mais antiga primeiro)
        leads_atualizacao = leads_atualizacao.sort_values('data_demo')
        
        # Preparar DataFrame para exibição
        df_atualizacao_display = leads_atualizacao[[
            'id', 'lead_name', 'vendedor', 'status', 'data_demo'
        ]].copy()
        
        df_atualizacao_display.columns = ['ID', 'Lead', 'Vendedor', 'Status Atual', 'Data da Demo']
        
        # Formatar data
        df_atualizacao_display['Data da Demo'] = df_atualizacao_display['Data da Demo'].dt.strftime('%d/%m/%Y')
        
        # Adicionar link
        df_atualizacao_display['Link'] = df_atualizacao_display['ID'].apply(generate_kommo_link)
        
        st.markdown("")
        
        # Exibir tabela com links clicáveis
        st.dataframe(
            df_atualizacao_display[['Lead', 'Vendedor', 'Status Atual', 'Data da Demo', 'Link']],
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link Kommo",
                    display_text="Abrir"
                )
            },
            hide_index=True,
            width='stretch',
            height=min(450, len(df_atualizacao_display) * 35 + 100)
        )
    else:
        st.success("✅ Não há leads que exigem atualização no momento!")

# ========================================
# ABA 2: INSIGHTS COM IA
# ========================================
with tab2:
    st.markdown("### 🤖 Insights Inteligentes com IA")
    st.caption("Análise automatizada dos dados do período com recomendações estratégicas")
    
    if gemini_client:
        # Botão para gerar insights
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 2])
        
        with col_btn1:
            gerar_insight = st.button("🔄 Gerar Análise", use_container_width=True, key="btn_gerar_insights", type="primary")
        
        with col_btn2:
            if 'insights_gerados' in st.session_state:
                if st.button("🗑️ Limpar Cache", use_container_width=True, key="btn_limpar_insights"):
                    del st.session_state['insights_gerados']
                    st.rerun()
        
        st.markdown("")
        
        # Preparar métricas uma única vez (fora do if para usar no chat também)
        metricas_atual = {
            'total_leads': total_leads,
            'leads_com_demo': leads_com_demo,
            'pct_com_demo': (leads_com_demo / total_leads * 100) if total_leads > 0 else 0,
            'demos_realizadas': demos_realizadas,
            'noshow_count': noshow_count,
            'leads_convertidos': leads_convertidos,
            'taxa_conversao': (leads_convertidos / total_leads * 100) if total_leads > 0 else 0
        }
        
        metricas_anterior = {
            'total_leads': total_leads_anterior,
            'leads_com_demo': leads_com_demo_anterior,
            'demos_realizadas': demos_realizadas_anterior,
            'noshow_count': noshow_count_anterior,
            'leads_convertidos': leads_convertidos_anterior
        }
        
        # Descrição do período
        periodo_descricao = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        
        if gerar_insight or 'insights_gerados' not in st.session_state:
            with st.spinner("🤖 Analisando dados e gerando insights estratégicos..."):
                # Gerar insights
                insights = gerar_insights_ia(metricas_atual, metricas_anterior, periodo_descricao)
                
                if insights:
                    st.session_state['insights_gerados'] = insights
        
        # Exibir insights
        if 'insights_gerados' in st.session_state:
            # Container com estilo usando st.container
            with st.container():
                st.markdown(
                    f"""<div style="
                        background: linear-gradient(135deg, rgba(32, 178, 170, 0.15) 0%, rgba(0, 139, 139, 0.08) 100%);
                        border-left: 4px solid #20B2AA;
                        border-radius: 12px;
                        padding: 1.5rem;
                        color: #ffffff;
                        margin-top: 1rem;
                    ">
                        {st.session_state['insights_gerados']}
                    </div>""",
                    unsafe_allow_html=True
                )
            
            # Informações adicionais
            st.markdown("")
            st.caption(f"🕐 Análise gerada em: {datetime.now(TZ_BRASILIA).strftime('%d/%m/%Y às %H:%M')} | 🤖 Powered by OpenAI GPT-4o-mini")
            
            # ========================================
            # SEÇÃO DE CHAT CONVERSACIONAL
            # ========================================
            st.markdown("---")
            st.markdown("### 💬 Chat com os Dados")
            st.caption("Faça perguntas sobre os insights e dados atuais")
            
            # Inicializar histórico de chat
            if 'chat_historico' not in st.session_state:
                st.session_state['chat_historico'] = []
            
            # Exibir histórico de chat
            chat_container = st.container(height=400, border=True)
            with chat_container:
                for msg in st.session_state['chat_historico']:
                    with st.chat_message(msg['role']):
                        st.markdown(msg['content'])
            
            # Input do usuário
            col_input, col_send = st.columns([0.9, 0.1])
            
            with col_input:
                user_input = st.text_input(
                    "Sua pergunta:",
                    placeholder="Ex: Por que o no-show aumentou? Como posso melhorar a conversão?",
                    label_visibility="collapsed",
                    key="chat_input"
                )
            
            with col_send:
                enviar_msg = st.button("📤", use_container_width=True, key="btn_enviar_chat")
            
            # Processar mensagem
            if enviar_msg and user_input:
                # Adicionar mensagem do usuário ao histórico
                st.session_state['chat_historico'].append({
                    'role': 'user',
                    'content': user_input
                })
                
                # Gerar resposta da IA
                with st.spinner("🤖 Processando sua pergunta..."):
                    resposta = chat_com_dados(
                        user_input,
                        metricas_atual,
                        metricas_anterior,
                        periodo_descricao,
                        st.session_state['chat_historico'][:-1]  # Histórico sem a mensagem atual
                    )
                    
                    # Adicionar resposta ao histórico
                    st.session_state['chat_historico'].append({
                        'role': 'assistant',
                        'content': resposta
                    })
                
                # Limpar input e fazer refresh
                st.rerun()
        else:
            st.info("👆 Clique no botão 'Gerar Análise' para obter insights inteligentes sobre seus dados.")
    else:
        st.warning("⚠️ **Insights com IA não configurados**")
        st.markdown("""
        Para habilitar a análise inteligente com IA, siga os passos:
        
        1. 🔑 Obtenha uma chave API do Google Gemini em: https://aistudio.google.com/app/apikey
        2. 📝 Adicione a chave no arquivo `.streamlit/secrets.toml`:
           ```toml
           GEMINI_API_KEY = "AIza..."
           ```
        3. 🔄 Reinicie a aplicação
        
        **Custo:** Gratuito até 15 requisições/minuto (Gemini 1.5 Flash)
        """)

# ========================================
# PREPARAR DADOS PARA RESUMO DIÁRIO
# ========================================

# get_all_leads_for_summary e get_tempo_por_etapa importados de services
# get_chamadas_vendedores importado de services (alias)
get_chamadas_vendedores = service_get_chamadas

df_all_leads = get_all_leads_for_summary(
    datetime.combine(data_inicio, datetime.min.time()),
    datetime.combine(data_fim, datetime.max.time()),
    vendedores_selecionados if vendedores_selecionados else None
)

# Aplicar filtro de pipeline ao resumo diário
if pipelines_selecionados and not df_all_leads.empty:
    df_all_leads = df_all_leads[df_all_leads['pipeline'].isin(pipelines_selecionados)]

# Gerar range de datas
date_range = pd.date_range(start=data_inicio, end=data_fim, freq='D')
resumo_daily = []

for data in date_range:
    data_date = data.date()
    
    if df_all_leads.empty:
        resumo_daily.append({
            'Data': data_date,
            'Dia': data.strftime('%A').lower(),
            'Novos Leads': 0,
            'Agendamentos': 0,
            'Demos no Dia': 0,
            'Noshow': 0,
            'Demos Realizadas': 0
        })
        continue
    
    # Novos Leads Período - usando criado_em
    novos_leads = len(df_all_leads[
        df_all_leads['criado_em'].dt.date == data_date
    ])
    
    # Agendamentos - usando data_agendamento (converter para date se for datetime)
    agendamentos = len(df_all_leads[
        df_all_leads['data_agendamento'].dt.date == data_date
    ]) if 'data_agendamento' in df_all_leads.columns else 0
    
    # Demos no Dia - usando data_demo (converter para date se for datetime)
    demos_dia = len(df_all_leads[
        df_all_leads['data_demo'].dt.date == data_date
    ]) if 'data_demo' in df_all_leads.columns else 0
    
    # Noshow - usando data_noshow (converter para date se for datetime)
    noshow = len(df_all_leads[
        df_all_leads['data_noshow'].dt.date == data_date
    ]) if 'data_noshow' in df_all_leads.columns else 0
    
    # Reuniões Realizadas - lógica do BI (usando constante DEMO_COMPLETED_STATUSES)
    if 'data_demo' in df_all_leads.columns and 'status' in df_all_leads.columns:
        demos_realizadas = len(df_all_leads[
            (df_all_leads['data_demo'].dt.date == data_date) &
            (
                (
                    (df_all_leads['status'] == 'Desqualificados') &
                    (df_all_leads['data_demo'].notna()) &
                    (df_all_leads['data_noshow'].isna())
                ) |
                (
                    (df_all_leads['data_demo'].notna()) &
                    (df_all_leads['status'].isin(DEMO_COMPLETED_STATUSES))
                )
            )
        ])
    else:
        demos_realizadas = 0
        
    # Percentual de demos realizadas em relação ao total de demos agendadas no dia
    porcentagem_demos = (demos_realizadas / demos_dia * 100) if demos_dia > 0 else 0
    
    # Percentual de noshow em relação ao total de demos agendadas no dia
    porcentagem_noshow = (noshow / demos_dia * 100) if demos_dia > 0 else 0
        
    resumo_daily.append({
        'Data': data_date,
        'Dia': data_date.strftime('%A').lower(),
        'Novos Leads': novos_leads,
        'Agendamentos': agendamentos,
        'Demos no Dia': demos_dia,
        'Noshow': noshow,
        'Demos Realizadas': demos_realizadas,
        'Porcentagem Demos': porcentagem_demos,
        '% Noshow': porcentagem_noshow,
    })

df_resumo = pd.DataFrame(resumo_daily)

# Ordenar por data decrescente
df_resumo = df_resumo.sort_values('Data', ascending=False)

# Formatar data
df_resumo_display = df_resumo.copy()
df_resumo_display['Data'] = df_resumo_display['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))

# Adicionar linha de total
total_row = {
    'Data': 'TOTAL',
    'Dia': '',
    'Novos Leads': df_resumo['Novos Leads'].sum(),
    'Agendamentos': df_resumo['Agendamentos'].sum(),
    'Demos no Dia': df_resumo['Demos no Dia'].sum(),
    'Noshow': df_resumo['Noshow'].sum(),
    'Demos Realizadas': df_resumo['Demos Realizadas'].sum(),
    'Porcentagem Demos': (df_resumo['Demos Realizadas'].sum() / df_resumo['Demos no Dia'].sum() * 100) if df_resumo['Demos no Dia'].sum() > 0 else 0,
    '% Noshow': (df_resumo['Noshow'].sum() / df_resumo['Demos no Dia'].sum() * 100) if df_resumo['Demos no Dia'].sum() > 0 else 0
}
df_resumo_display = pd.concat([df_resumo_display, pd.DataFrame([total_row])], ignore_index=True)

# ========================================
# ABA 3: DEMONSTRAÇÕES DE HOJE
# ========================================
with tab3:
    st.markdown("### 📆 Demonstrações Agendadas para Hoje")
    st.caption("Demos pendentes de realização para o dia de hoje")

    # Filtrar demos de hoje que ainda não foram realizadas
    demos_hoje = df_all_leads[
        (df_all_leads['data_demo'].dt.date == hoje.date()) &  # Demo agendada para hoje
        (df_all_leads['data_noshow'].isna()) &  # Não marcado como no-show
        (~df_all_leads['status'].isin(DEMO_COMPLETED_STATUSES + FUNNEL_CLOSED_STATUSES))  # Status não indica demo realizada
    ].copy()
    
    if not demos_hoje.empty:
        # Ordenar por vendedor
        demos_hoje = demos_hoje.sort_values('vendedor')
        
        # Preparar DataFrame para exibição
        df_demos_hoje = demos_hoje[[
            'id', 'lead_name', 'vendedor', 'status', 'data_demo', 'data_hora_demo'
        ]].copy()
        
        # Criar coluna Horário usando data_hora_demo prioritariamente, senão data_demo
        df_demos_hoje['Horário'] = df_demos_hoje['data_hora_demo']
        
        # Garantir que a coluna seja datetime e converter para GMT-3
        df_demos_hoje['Horário'] = pd.to_datetime(df_demos_hoje['Horário'], errors='coerce')
        
        # Converter para GMT-3 se já tiver timezone, senão assumir UTC e converter
        if df_demos_hoje['Horário'].dt.tz is not None:
            df_demos_hoje['Horário'] = df_demos_hoje['Horário'].dt.tz_convert('America/Sao_Paulo')
        else:
            df_demos_hoje['Horário'] = df_demos_hoje['Horário'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
                        
        df_demos_hoje = df_demos_hoje[['id', 'lead_name', 'vendedor', 'status', 'Horário', 'data_demo']].copy()
        df_demos_hoje.columns = ['ID', 'Lead', 'Vendedor', 'Status', 'Horário da Demo', 'Data Demo']
        
        # Ordenar por horário ANTES de formatar para string
        df_demos_hoje = df_demos_hoje.sort_values('Horário da Demo')
        
        # Formatar horário
        df_demos_hoje['Horário da Demo'] = df_demos_hoje['Horário da Demo'].dt.strftime('%d/%m/%Y %H:%M')
        df_demos_hoje['Data Demo'] = df_demos_hoje['Data Demo'].dt.strftime('%d/%m/%Y %H:%M')
        df_demos_hoje['Horário da Demo'] = df_demos_hoje['Horário da Demo'].fillna(df_demos_hoje['Data Demo'])
        
        # Adicionar link
        df_demos_hoje['Link'] = df_demos_hoje['ID'].apply(generate_kommo_link)
        
        # Contar demos por vendedor
        demos_por_vendedor = demos_hoje.groupby('vendedor').size().reset_index(name='Total')
        
        # Exibir métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Demos Hoje", len(demos_hoje))
        
        with col2:
            st.metric("Vendedores Ativos", demos_hoje['vendedor'].nunique())
        
        with col3:
            # Calcular média de demos por vendedor
            media_demos = len(demos_hoje) / demos_hoje['vendedor'].nunique()
            st.metric("Média por Vendedor", f"{media_demos:.1f}")
        
        st.markdown("")
        st.markdown("#### 📋 Lista de Demonstrações")
        
        # Exibir tabela
        st.dataframe(
            df_demos_hoje[['Lead', 'Vendedor', 'Status', 'Horário da Demo', 'Link']],
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link Kommo",
                    display_text="Abrir"
                )
            },
            hide_index=True,
            width='stretch',
            height=min(400, len(df_demos_hoje) * 35 + 100)
        )
        
        st.markdown("")
        st.markdown("#### 👥 Demos por Vendedor")
        
        col_charts = st.columns([2, 1])
        
        with col_charts[0]:
            # Gráfico de barras
            fig = px.bar(
                demos_por_vendedor,
                x='vendedor',
                y='Total',
                title='Quantidade de Demos por Vendedor Hoje',
                labels={'vendedor': 'Vendedor', 'Total': 'Quantidade'},
                color='Total',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="demos_by_vendor_chart")
        
        with col_charts[1]:
            # Tabela resumo
            st.dataframe(
                demos_por_vendedor,
                column_config={
                    "vendedor": "Vendedor",
                    "Total": st.column_config.NumberColumn("Demos", format="%d")
                },
                hide_index=True,
                width='stretch'
            )
    else:
        st.info("ℹ️ Não há demonstrações agendadas para hoje.")

# ========================================
# ABA 4: RESUMO DIÁRIO
# ========================================
with tab4:
    st.markdown("### 📅 Resumo Diário da Equipe")
    st.caption("Análise das atividades diárias no período selecionado")
        
    # Seletor de visualização
    view_type = st.radio(
        "Visualização",
        ["📊 Visão Geral", "👥 Por Vendedor"],
        horizontal=True
    )
    
    st.markdown("")
    
    if view_type == "📊 Visão Geral":
        # Exibir tabela consolidada
        st.dataframe(
            df_resumo_display,
            hide_index=True,
            width='stretch',
            column_config={
                "Data": st.column_config.TextColumn("Data", width="small"),
                "Dia": st.column_config.TextColumn("Dia", width="medium"),
                "Novos Leads": st.column_config.NumberColumn("Novos Leads", format="%d"),
                "Agendamentos": st.column_config.NumberColumn("Agendamentos", format="%d"),
                "Demos no Dia": st.column_config.NumberColumn("Demos no Dia", format="%d"),
                "Noshow": st.column_config.NumberColumn("Noshow", format="%d"),
                "Demos Realizadas": st.column_config.NumberColumn("Demos Realizadas", format="%d"),
                "Porcentagem Demos": st.column_config.NumberColumn("% Realizadas", format="%.1f%%"),
                "% Noshow": st.column_config.NumberColumn("% Noshow", format="%.1f%%"),
            },
            height=min(500, len(df_resumo_display) * 35 + 100)
        )
    
    else:  # Por Vendedor
        st.info("💡 Dica: Selecione um vendedor específico nos filtros da barra lateral para análise individual")
        
        # Criar resumo por vendedor e data
        if not df_all_leads.empty and 'vendedor' in df_all_leads.columns:
            resumo_vendedor_list = []
            
            for vendedor in sorted(df_all_leads['vendedor'].dropna().unique()):
                df_vendedor = df_all_leads[df_all_leads['vendedor'] == vendedor]
                
                for data in date_range:
                    data_date = data.date()
                    
                    # Novos Leads
                    novos_leads = len(df_vendedor[df_vendedor['criado_em'].dt.date == data_date])
                    
                    # Agendamentos
                    agendamentos = len(df_vendedor[df_vendedor['data_agendamento'].dt.date == data_date]) if 'data_agendamento' in df_vendedor.columns else 0
                    
                    # Demos no Dia
                    demos_dia = len(df_vendedor[df_vendedor['data_demo'].dt.date == data_date]) if 'data_demo' in df_vendedor.columns else 0
                    
                    # Noshow
                    noshow = len(df_vendedor[df_vendedor['data_noshow'].dt.date == data_date]) if 'data_noshow' in df_vendedor.columns else 0
                    
                    # Reuniões Realizadas (usando constante DEMO_COMPLETED_STATUSES)
                    if 'data_demo' in df_vendedor.columns and 'status' in df_vendedor.columns:
                        demos_realizadas = len(df_vendedor[
                            (df_vendedor['data_demo'].dt.date == data_date) &
                            (
                                (
                                    (df_vendedor['status'] == 'Desqualificados') &
                                    (df_vendedor['data_demo'].notna()) &
                                    (df_vendedor['data_noshow'].isna())
                                ) |
                                (
                                    (df_vendedor['data_demo'].notna()) &
                                    (df_vendedor['status'].isin(DEMO_COMPLETED_STATUSES))
                                )
                            )
                        ])
                    else:
                        demos_realizadas = 0
                    
                    # Só adicionar se houver alguma atividade
                    if any([novos_leads, agendamentos, demos_dia, noshow, demos_realizadas]):
                        resumo_vendedor_list.append({
                            'Vendedor': vendedor,
                            'Data': data_date,
                            'Dia': DIAS_PT.get(data.strftime('%A').lower(), data.strftime('%A')),
                            'Novos Leads': novos_leads,
                            'Agendamentos': agendamentos,
                            'Demos no Dia': demos_dia,
                            'Noshow': noshow,
                            'Demos Realizadas': demos_realizadas
                        })
            
            if resumo_vendedor_list:
                df_resumo_vendedor = pd.DataFrame(resumo_vendedor_list)
                
                # Ordenar por vendedor e data
                df_resumo_vendedor = df_resumo_vendedor.sort_values(['Vendedor', 'Data'], ascending=[True, False])
                
                # Formatar data
                df_resumo_vendedor['Data'] = df_resumo_vendedor['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
                
                # Exibir tabela
                st.dataframe(
                    df_resumo_vendedor,
                    hide_index=True,
                    width='stretch',
                    column_config={
                        "Vendedor": st.column_config.TextColumn("Vendedor", width="medium"),
                        "Data": st.column_config.TextColumn("Data", width="small"),
                        "Dia": st.column_config.TextColumn("Dia", width="medium"),
                        "Novos Leads": st.column_config.NumberColumn("Novos Leads", format="%d"),
                        "Agendamentos": st.column_config.NumberColumn("Agendamentos", format="%d"),
                        "Demos no Dia": st.column_config.NumberColumn("Demos no Dia", format="%d"),
                        "Noshow": st.column_config.NumberColumn("Noshow", format="%d"),
                        "Demos Realizadas": st.column_config.NumberColumn("Demos Realizadas", format="%d"),
                    },
                    height=min(500, len(df_resumo_vendedor) * 35 + 100)
                )
            else:
                st.info("Nenhuma atividade registrada no período selecionado")
        else:
            st.warning("Não há dados de vendedores disponíveis")

# ========================================
# ABA 5: DETALHES DOS LEADS
# ========================================
with tab5:
    st.markdown("### 🔍 Detalhes dos Leads no Período")
    st.caption("Visualização completa e pesquisável de todos os leads")
    
    # Filtro de pesquisa
    search_term = st.text_input("🔎 Pesquisar por nome do lead", "", key="search_leads")
    
    # Filtrar por termo de pesquisa
    if search_term:
        df_detalhes = df_leads[
            df_leads['lead_name'].str.contains(search_term, case=False, na=False)
        ].copy()
    else:
        df_detalhes = df_leads.copy()
    
    if not df_detalhes.empty:
        # Preparar DataFrame para exibição
        colunas_exibir = [
            'id', 'lead_name', 'vendedor', 'status', 'pipeline',
            'criado_em', 'data_agendamento', 'data_demo', 'data_noshow'
        ]
        
        # Verificar quais colunas existem
        colunas_existentes = [col for col in colunas_exibir if col in df_detalhes.columns]
        
        df_detalhes_display = df_detalhes[colunas_existentes].copy()
        
        # Renomear colunas
        rename_map = {
            'id': 'ID',
            'lead_name': 'Lead',
            'vendedor': 'Vendedor',
            'status': 'Status Atual',
            'pipeline': 'Pipeline',
            'criado_em': 'Data Criação',
            'data_agendamento': 'Data Agendamento',
            'data_demo': 'Data Demo',
            'data_noshow': 'Data Noshow'
        }
        df_detalhes_display.columns = [rename_map.get(col, col) for col in df_detalhes_display.columns]
        
        # Ordenar por Data Criação ANTES de formatar (mais recente primeiro)
        if 'Data Criação' in df_detalhes_display.columns:
            df_detalhes_display = df_detalhes_display.sort_values('Data Criação', ascending=False)
        
        # Formatar datas DEPOIS de ordenar
        date_cols = ['Data Criação', 'Data Agendamento', 'Data Demo', 'Data Noshow']
        for col in date_cols:
            if col in df_detalhes_display.columns:
                df_detalhes_display[col] = df_detalhes_display[col].dt.strftime('%d/%m/%Y')
        
        # Adicionar link
        df_detalhes_display['Link'] = df_detalhes_display['ID'].apply(generate_kommo_link)
        
        st.info(f"📊 Exibindo **{len(df_detalhes_display)} leads**")
        
        # Exibir tabela
        st.dataframe(
            df_detalhes_display,
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link Kommo",
                    display_text="Abrir"
                )
            },
            hide_index=True,
            width='stretch',
            height=min(600, len(df_detalhes_display) * 35 + 100)
        )
    else:
        st.info("Nenhum lead encontrado com o termo pesquisado.")

# ========================================
# ABA 6: TEMPO POR ETAPA
# ========================================
with tab6:
    st.markdown("### ⏱️ Tempo Médio por Etapa")
    st.caption("Visualize quanto tempo os leads ficam em média em cada etapa do funil")
    
    # Buscar dados de tempo por etapa
    df_tempo = get_tempo_por_etapa()
    
    if not df_tempo.empty:
        # Renomear colunas se necessário
        if 'status_name' in df_tempo.columns:
            df_tempo = df_tempo.rename(columns={
                'status_name': 'Etapa',
                'media_tempo_horas': 'Tempo Médio (horas)',
                'status_id': 'ID Status'
            })
        
        # Selecionar quais status exibir
        if 'Etapa' in df_tempo.columns:
            # Filtrar apenas status que possuem leads (removendo valores nulos e vazios)
            df_tempo = df_tempo[df_tempo['Etapa'].notna() & (df_tempo['Etapa'] != '')]
            etapas_disponiveis = sorted(df_tempo['Etapa'].unique().tolist())
            
            col_filter1, col_filter2 = st.columns([1, 3])
            
            with col_filter1:
                st.write("**Filtrar Etapas:**")
                etapas_selecionadas = st.multiselect(
                    "Selecione as etapas",
                    options=etapas_disponiveis,
                    default=etapas_disponiveis[:10] if len(etapas_disponiveis) > 10 else etapas_disponiveis,
                    key="etapas_filter"
                )
            
            if etapas_selecionadas:
                df_tempo_filtrado = df_tempo[df_tempo['Etapa'].isin(etapas_selecionadas)].copy()
                
                # Converter tempo de horas para dias
                if 'Tempo Médio (horas)' in df_tempo_filtrado.columns:
                    df_tempo_filtrado['Tempo Médio (dias)'] = df_tempo_filtrado['Tempo Médio (horas)'] / 24
                
                # Ordenar por tempo médio decrescente
                if 'Tempo Médio (dias)' in df_tempo_filtrado.columns:
                    df_tempo_filtrado = df_tempo_filtrado.sort_values('Tempo Médio (dias)', ascending=False)
                
                st.markdown("")
                
                # Exibir gráfico de barras
                col_chart, col_table = st.columns([2, 1])
                
                with col_chart:
                    if 'Tempo Médio (dias)' in df_tempo_filtrado.columns:
                        fig = px.bar(
                            df_tempo_filtrado,
                            x='Etapa',
                            y='Tempo Médio (dias)',
                            title='Tempo Médio por Etapa',
                            labels={'Etapa': 'Etapa do Funil', 'Tempo Médio (dias)': 'Dias'},
                            color='Tempo Médio (dias)',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(height=400, xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True, key="tempo_etapa_chart")
                
                with col_table:
                    st.markdown("**Ranking de Etapas**")
                    
                    # Criar ranking
                    df_ranking = df_tempo_filtrado[['Etapa', 'Tempo Médio (dias)']].copy()
                    df_ranking['Ranking'] = range(1, len(df_ranking) + 1)
                    df_ranking = df_ranking[['Ranking', 'Etapa', 'Tempo Médio (dias)']]
                    
                    st.dataframe(
                        df_ranking,
                        column_config={
                            "Ranking": st.column_config.NumberColumn("Pos", format="%d"),
                            "Etapa": st.column_config.TextColumn("Etapa", width="medium"),
                            "Tempo Médio (dias)": st.column_config.NumberColumn("Dias", format="%.1f")
                        },
                        hide_index=True,
                        width='stretch',
                        height=min(400, len(df_ranking) * 35 + 100)
                    )
                
                st.markdown("")
                
                # Tabela detalhada
                st.markdown("#### 📊 Dados Completos")
                
                # Preparar dataframe para exibição com colunas úteis
                df_exibicao = df_tempo_filtrado[['ID Status', 'Etapa', 'Tempo Médio (dias)']].copy() if 'ID Status' in df_tempo_filtrado.columns else df_tempo_filtrado[['Etapa', 'Tempo Médio (dias)']].copy()
                
                st.dataframe(
                    df_exibicao,
                    column_config={
                        "ID Status": st.column_config.NumberColumn("ID", format="%d"),
                        "Etapa": st.column_config.TextColumn("Etapa"),
                        "Tempo Médio (dias)": st.column_config.NumberColumn("Tempo (dias)", format="%.1f")
                    },
                    hide_index=True,
                    width='stretch',
                    height=min(500, len(df_exibicao) * 35 + 100)
                )
            else:
                st.info("Selecione pelo menos uma etapa para visualizar")
        else:
            st.warning("Estrutura de dados inesperada. Verifique a query.")
    else:
        st.info("⚠️ Dados de tempo por etapa não disponíveis. Certifique-se de que a função RPC 'get_tempo_por_etapa' está configurada no banco de dados.")

# ========================================
# ABA 7: PRODUTIVIDADE DO VENDEDOR
# ========================================
with tab7:
    st.markdown("### 📞 Produtividade do Vendedor - Análise de Chamadas")
    st.caption("Métricas detalhadas de discagens, atendimentos e ligações efetivas")
    
    # Buscar dados de chamadas
    data_inicio_query = datetime.combine(data_inicio, datetime.min.time())
    data_fim_query = datetime.combine(data_fim, datetime.max.time())
    
    df_chamadas = get_chamadas_vendedores(data_inicio_query, data_fim_query)
    
    if not df_chamadas.empty:

        df_chamadas['atendido_em'] = pd.to_datetime(df_chamadas['atendido_em'])
        data_min = df_chamadas['atendido_em'].min()
        data_max = df_chamadas['atendido_em'].max()
        
        # Adicionar coluna duration_minutos se não existir
        if 'duration_minutos' not in df_chamadas.columns and 'duration' in df_chamadas.columns:
            df_chamadas['duration_minutos'] = df_chamadas['duration'] / 60
        
        # Classificar tipos de ligação
        df_chamadas['tipo_ligacao'] = df_chamadas['causa_desligamento'].apply(
            lambda x: 'Atendida' if x == 'Atendida' else 'Não Atendida'
        )
        
        # Definir ligações efetivas (atendidas com duração > 50 segundos)
        df_chamadas['efetiva'] = (
            (df_chamadas['causa_desligamento'] == 'Atendida') & 
            (df_chamadas['duration'] > 50)
        )
        
        if not df_chamadas.empty:
            # ========================================
            # SELETOR DE VENDEDOR
            # ========================================
            st.markdown("#### 👤 Seleção de Vendedor")
            
            vendedores_disponiveis = ['Todos'] + sorted(df_chamadas['name'].dropna().unique().tolist())
            vendedor_selecionado = st.selectbox(
                "Escolha um vendedor para análise detalhada:",
                vendedores_disponiveis,
                key="vendedor_prod_select"
            )
            
            # Filtrar dados pelo vendedor selecionado
            if vendedor_selecionado != 'Todos':
                df_vendedor = df_chamadas[df_chamadas['name'] == vendedor_selecionado].copy()
            else:
                df_vendedor = df_chamadas.copy()
            
            st.markdown("---")
            
            # ========================================
            # SEÇÃO 0: DISCAGENS POR VENDEDOR POR DIA
            # ========================================
            st.markdown("#### 📈 Discagens por Vendedor por Dia")
            st.caption("Acompanhe a evolução diária das ligações de cada vendedor no período")
            
            # Preparar dados para o gráfico de linhas
            df_chamadas['data'] = df_chamadas['atendido_em'].dt.date
            
            # Agrupar por data e vendedor
            df_discagens_dia = df_chamadas.groupby(['data', 'name']).size().reset_index(name='discagens')
            
            # Criar label com nome e ramal
            df_ramal = df_chamadas[['name', 'ramal']].drop_duplicates()
            df_discagens_dia = df_discagens_dia.merge(df_ramal, on='name', how='left')
            df_discagens_dia['vendedor_label'] = df_discagens_dia.apply(
                lambda row: f"{row['name']} ({int(row['ramal'])})" if pd.notna(row['ramal']) else row['name'], 
                axis=1
            )
            
            # Ordenar vendedores por total de discagens (decrescente)
            ordem_vendedores = df_discagens_dia.groupby('vendedor_label')['discagens'].sum().sort_values(ascending=False).index.tolist()
            
            # Garantir que todas as datas do período apareçam (mesmo sem discagens)
            df_discagens_dia['data'] = pd.to_datetime(df_discagens_dia['data'])
            
            if vendedor_selecionado != 'Todos':
                df_discagens_dia = df_discagens_dia[df_discagens_dia['name'] == vendedor_selecionado]
            
            # Criar gráfico de linhas (usando paleta do módulo config)
            fig_discagens_dia = px.line(
                df_discagens_dia,
                x='data',
                y='discagens',
                color='vendedor_label',
                labels={'data': '', 'discagens': '', 'vendedor_label': ''},
                markers=True,
                color_discrete_sequence=CHART_COLORS,
                category_orders={'vendedor_label': ordem_vendedores}
            )
            
            fig_discagens_dia.update_layout(
                height=500,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=14, color='#ffffff'),
                    bgcolor='rgba(0,0,0,0)',
                    itemsizing='constant'
                ),
                xaxis=dict(
                    tickformat='%d/%m',
                    tickangle=0,
                    tickfont=dict(size=12, color='#CBD5E0'),
                    gridcolor='rgba(255,255,255,0.1)',
                    showgrid=True,
                    dtick='D1',  # Um tick por dia
                    tickmode='auto',
                    nticks=30
                ),
                yaxis=dict(
                    tickfont=dict(size=12, color='#CBD5E0'),
                    gridcolor='rgba(255,255,255,0.1)',
                    showgrid=True,
                    zeroline=False
                ),
                margin=dict(l=20, r=20, t=60, b=40),
                hoverlabel=dict(
                    bgcolor='#2d3748',
                    font_size=14,
                    font_family="Arial"
                )
            )
            
            # Estilizar as linhas e marcadores
            fig_discagens_dia.update_traces(
                line=dict(width=2.5),
                marker=dict(size=8, line=dict(width=1, color='#1a1f2e')),
                hovertemplate='<b>%{y}</b> discagens<extra>%{fullData.name}</extra>'
            )
            
            st.plotly_chart(fig_discagens_dia, use_container_width=True)
            
            # Mini resumo abaixo do gráfico
            col_resumo2, col_resumo3, col_resumo4 = st.columns(3)
            
            with col_resumo2:
                media_dia = df_discagens_dia.groupby('data')['discagens'].sum().mean()
                st.metric("📊 Média Discagens por Dia", f"{media_dia:.0f}")
            
            with col_resumo3:
                melhor_dia = df_discagens_dia.groupby('data')['discagens'].sum().idxmax()
                max_discagens = df_discagens_dia.groupby('data')['discagens'].sum().max()
                st.metric("🏆 Melhor Dia", f"{melhor_dia.strftime('%d/%m')}", delta=f"{int(max_discagens)} disc.")
            
            with col_resumo4:
                vendedores_ativos = df_discagens_dia['vendedor_label'].nunique()
                st.metric("👥 Vendedores Ativos", f"{vendedores_ativos}")
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 1: MÉTRICAS PRINCIPAIS
            # ========================================
            st.markdown("#### 📊 Métricas de Performance")
            
            total_discagens = len(df_vendedor)
            total_atendidas = len(df_vendedor[df_vendedor['causa_desligamento'] == 'Atendida'])
            total_efetivas = df_vendedor['efetiva'].sum()
            
            # Calcular taxas
            taxa_atendimento = (total_atendidas / total_discagens * 100) if total_discagens > 0 else 0
            taxa_efetividade = (total_efetivas / total_atendidas * 100) if total_atendidas > 0 else 0
            taxa_conversao_geral = (total_efetivas / total_discagens * 100) if total_discagens > 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "📞 Total Discagens",
                    f"{total_discagens:,}".replace(",", "."),
                    help="Todas as tentativas de ligação"
                )
            
            with col2:
                st.metric(
                    "✅ Atendidas",
                    f"{total_atendidas:,}".replace(",", "."),
                    delta=f"{taxa_atendimento:.1f}%",
                    help="Ligações que foram atendidas"
                )
            
            with col3:
                st.metric(
                    "🎯 Efetivas",
                    f"{total_efetivas:,}".replace(",", "."),
                    delta=f"{taxa_conversao_geral:.1f}%",
                    help="Ligações atendidas com duração > 50s"
                )
            
            with col4:
                tmd_atendidas = df_vendedor[df_vendedor['causa_desligamento'] == 'Atendida']['duration_minutos'].mean()
                st.metric(
                    "⏱️ TMD Atendidas",
                    f"{tmd_atendidas:.1f} min" if pd.notna(tmd_atendidas) else "N/A",
                    help="Tempo médio de duração das ligações atendidas"
                )
            
            with col5:
                tmd_efetivas = df_vendedor[df_vendedor['efetiva']]['duration_minutos'].mean()
                st.metric(
                    "⏱️ TMD Efetivas",
                    f"{tmd_efetivas:.1f} min" if pd.notna(tmd_efetivas) else "N/A",
                    help="Tempo médio de duração das ligações efetivas"
                )
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 2: FUNIL DE CONVERSÃO
            # ========================================
            st.markdown("#### 🔄 Funil de Conversão de Chamadas")
            
            col_funil1, col_funil2 = st.columns([2, 1])
            
            with col_funil1:
                # Criar dados do funil (ordem invertida para visualização)
                funil_data = pd.DataFrame({
                    'Etapa': ['Efetivas', 'Atendidas', 'Discagens'],
                    'Quantidade': [total_efetivas, total_atendidas, total_discagens],
                    'Percentual': [taxa_conversao_geral, taxa_atendimento, 100],
                    'Label': [
                        f'({taxa_atendimento:.1f}%)',
                        f'({taxa_conversao_geral:.1f}%)',
                        f''
                    ]
                })
                
                fig_funil = px.funnel(
                    funil_data,
                    x='Quantidade',
                    y='Etapa',
                    title=f'Funil de Conversão - {vendedor_selecionado}',
                    color='Etapa',
                    text='Label',
                    color_discrete_map={'Efetivas': '#4CAF50', 'Atendidas': '#FFA500', 'Discagens': '#4A9FFF'}
                )
                fig_funil.update_traces(textposition='outside', textfont_size=18, textfont=dict(family="Arial", color="white", weight="bold"))
                fig_funil.update_yaxes(categoryorder='array', categoryarray=['Discagens', 'Atendidas', 'Efetivas'], tickfont=dict(size=18))
                fig_funil.update_layout(height=610, yaxis_title='')
                st.plotly_chart(fig_funil, use_container_width=True)
            
            with col_funil2:
                st.markdown("**Taxas de Conversão**")
                st.markdown("")
                
                st.metric("📊 Taxa de Atendimento", f"{taxa_atendimento:.1f}%")
                st.caption(f"{total_atendidas} de {total_discagens} discagens")
                
                st.markdown("")
                
                st.metric("🎯 Taxa de Efetividade", f"{taxa_efetividade:.1f}%")
                st.caption(f"{total_efetivas} de {total_atendidas} atendidas")
                
                st.markdown("")
                
                st.metric("💯 Conversão Geral", f"{taxa_conversao_geral:.1f}%")
                st.caption(f"{total_efetivas} de {total_discagens} discagens")
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 3: RANKING DE VENDEDORES (se Todos estiver selecionado)
            # ========================================
            if vendedor_selecionado == 'Todos':
                st.markdown("#### 🏆 Ranking de Vendedores")
                
                # Agregar métricas por vendedor
                df_ranking = df_chamadas.groupby('name').agg({
                    'id': 'count',
                    'causa_desligamento': lambda x: (x == 'Atendida').sum(),
                    'efetiva': 'sum',
                    'duration_minutos': lambda x: x[df_chamadas.loc[x.index, 'causa_desligamento'] == 'Atendida'].mean()
                }).reset_index()
                
                df_ranking.columns = ['Vendedor', 'Discagens', 'Atendidas', 'Efetivas', 'TMD (min)']
                
                # Calcular taxas
                df_ranking['Taxa Atend. (%)'] = (df_ranking['Atendidas'] / df_ranking['Discagens'] * 100).round(1)
                df_ranking['Taxa Efet. (%)'] = (df_ranking['Efetivas'] / df_ranking['Discagens'] * 100).round(1)
                df_ranking['TMD (min)'] = df_ranking['TMD (min)'].round(1)
                
                # Ordenar por efetivas
                df_ranking = df_ranking.sort_values('Efetivas', ascending=False)
                
                col_rank1, col_rank2 = st.columns(2)
                
                with col_rank1:
                    # Gráfico de barras - Ligações Efetivas
                    fig_ranking = px.bar(
                        df_ranking,
                        x='Vendedor',
                        y='Efetivas',
                        title='Ranking - Ligações Efetivas por Vendedor',
                        color='Efetivas',
                        color_continuous_scale='Greens',
                        text='Efetivas'
                    )
                    fig_ranking.update_traces(textposition='outside', textfont_size=14)
                    fig_ranking.update_xaxes(tickfont=dict(size=12), tickangle=-45)
                    fig_ranking.update_layout(height=400, coloraxis_colorbar=dict(tickfont=dict(size=12)))
                    st.plotly_chart(fig_ranking, use_container_width=True)
                
                with col_rank2:
                    # Gráfico de dispersão - Taxa de Efetividade vs Volume
                    fig_scatter = px.scatter(
                        df_ranking,
                        x='Discagens',
                        y='Taxa Efet. (%)',
                        size='Efetivas',
                        color='Vendedor',
                        title='Eficiência vs Volume',
                        labels={'Discagens': 'Volume de Discagens', 'Taxa Efet. (%)': 'Taxa de Efetividade (%)'},
                        hover_data=['Atendidas', 'Efetivas', 'TMD (min)']
                    )
                    fig_scatter.update_layout(height=400, showlegend=True)
                    fig_scatter.update_xaxes(tickfont=dict(size=16))
                    fig_scatter.update_yaxes(tickfont=dict(size=16))
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Tabela de ranking
                st.dataframe(
                    df_ranking,
                    column_config={
                        "Vendedor": st.column_config.TextColumn("Vendedor", width="medium"),
                        "Discagens": st.column_config.NumberColumn("Discagens", format="%d"),
                        "Atendidas": st.column_config.NumberColumn("Atendidas", format="%d"),
                        "Efetivas": st.column_config.NumberColumn("Efetivas", format="%d"),
                        "Taxa Atend. (%)": st.column_config.NumberColumn("Taxa Atend.", format="%.1f%%"),
                        "Taxa Efet. (%)": st.column_config.NumberColumn("Taxa Efet.", format="%.1f%%"),
                        "TMD (min)": st.column_config.NumberColumn("TMD", format="%.1f")
                    },
                    hide_index=True,
                    width='stretch',
                    height=min(400, len(df_ranking) * 35 + 100)
                )
                
                st.markdown("")
            
            # ========================================
            # SEÇÃO 4: DISTRIBUIÇÃO DE RESULTADOS
            # ========================================
            st.markdown("#### 📈 Análise de Resultados das Chamadas")
            
            col_dist1, col_dist2 = st.columns(2)
            
            with col_dist1:
                # Distribuição por motivo de desligamento
                df_motivos = df_vendedor['causa_desligamento'].value_counts().reset_index()
                df_motivos.columns = ['Motivo', 'Quantidade']
                
                fig_motivos = px.bar(
                    df_motivos,
                    y='Motivo',
                    x='Quantidade',
                    title='Distribuição por Resultado',
                    orientation='h',
                    color='Quantidade',
                    color_continuous_scale='Blues',
                    text='Quantidade'
                )
                fig_motivos.update_traces(textposition='outside', textfont_size=16)
                fig_motivos.update_yaxes(categoryorder='total descending', tickfont=dict(size=14))
                fig_motivos.update_xaxes(showticklabels=False)
                fig_motivos.update_layout(height=400, yaxis_title='', xaxis_title='', coloraxis_colorbar=dict(tickfont=dict(size=14)))
                st.plotly_chart(fig_motivos, use_container_width=True)
            
            with col_dist2:
                # Distribuição de duração (apenas atendidas)
                df_atendidas_duracao = df_vendedor[df_vendedor['causa_desligamento'] == 'Atendida'].copy()
                
                if not df_atendidas_duracao.empty:
                    fig_duracao = px.histogram(
                        df_atendidas_duracao,
                        x='duration_minutos',
                        nbins=20,
                        title='Distribuição de Duração (Ligações Atendidas)',
                        labels={'duration_minutos': 'Duração (minutos)', 'count': 'Ligações'},
                        color_discrete_sequence=['#4A9FFF'],
                        text_auto=True
                    )
                    fig_duracao.update_traces(textposition='outside', textfont_size=14, marker_line_width=1.5)
                    fig_duracao.update_layout(height=400, showlegend=False, bargap=0.1)
                    # Calcular o máximo valor para limitar o range
                    max_count = len(df_atendidas_duracao)
                    fig_duracao.update_yaxes(title_text='Ligações', range=[0, max_count * 0.9], showticklabels=False)
                    fig_duracao.add_vline(x=50/60, line_dash="dash", line_color="red", 
                                         annotation_text="Limite Efetiva (50s)")
                    st.plotly_chart(fig_duracao, use_container_width=True)
                else:
                    st.info("Sem ligações atendidas para análise de duração")
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 5: TABELA DE LIGAÇÕES EFETIVAS
            # ========================================
            st.markdown("#### 🎯 Ligações Efetivas (Duração > 50s)")
            
            df_efetivas = df_vendedor[df_vendedor['efetiva']].copy()
            
            if not df_efetivas.empty:
                # Preparar dados
                df_efetivas_display = df_efetivas[['name', 'atendente', 'ramal', 'atendido_em', 'duration', 'url_gravacao']].copy()
                df_efetivas_display['atendido_em'] = pd.to_datetime(df_efetivas_display['atendido_em'])
                df_efetivas_display = df_efetivas_display.sort_values('atendido_em', ascending=False)
                
                df_efetivas_display['duration_formatada'] = df_efetivas_display['duration'].apply(
                    lambda x: f"{int(x//60)}:{int(x%60):02d}" if pd.notna(x) else "N/A"
                )
                df_efetivas_display['atendido_em_formatado'] = df_efetivas_display['atendido_em'].dt.strftime('%d/%m/%Y %H:%M')
                
                df_efetivas_display = df_efetivas_display.rename(columns={
                    'name': 'Vendedor',
                    'atendente': 'Atendente',
                    'ramal': 'Ramal',
                    'url_gravacao': 'Gravação'
                })
                
                st.info(f"📊 Total de {len(df_efetivas_display)} ligações efetivas encontradas")
                
                st.dataframe(
                    df_efetivas_display[['Vendedor', 'Atendente', 'Ramal', 'atendido_em_formatado', 'duration_formatada', 'Gravação']],
                    column_config={
                        "Vendedor": st.column_config.TextColumn("Vendedor"),
                        "Atendente": st.column_config.TextColumn("Atendente"),
                        "Ramal": st.column_config.NumberColumn("Ramal", format="%d"),
                        "atendido_em_formatado": st.column_config.TextColumn("Data/Hora"),
                        "duration_formatada": st.column_config.TextColumn("Duração"),
                        "Gravação": st.column_config.LinkColumn("🔊 Gravação", display_text="Ouvir")
                    },
                    hide_index=True,
                    width='stretch',
                    height=min(400, len(df_efetivas_display) * 35 + 100)
                )
            else:
                st.warning("⚠️ Nenhuma ligação efetiva encontrada no período selecionado")
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 6: TABELA DE TODAS AS DISCAGENS
            # ========================================
            st.markdown("#### 📞 Histórico Completo de Discagens")
            
            # Preparar dados
            df_discagens = df_vendedor.copy()
            df_discagens['atendido_em'] = pd.to_datetime(df_discagens['atendido_em'])
            df_discagens = df_discagens.sort_values('atendido_em', ascending=False)
            
            df_discagens['duration_formatada'] = df_discagens['duration'].apply(
                lambda x: f"{int(x//60)}:{int(x%60):02d}" if pd.notna(x) and x > 0 else "0:00"
            )
            df_discagens['atendido_em_formatado'] = df_discagens['atendido_em'].dt.strftime('%d/%m/%Y %H:%M')
            
            df_discagens_display = df_discagens.rename(columns={
                'name': 'Vendedor',
                'atendente': 'Atendente',
                'ramal': 'Ramal',
                'causa_desligamento': 'Resultado',
                'url_gravacao': 'Gravação'
            })
            
            # Adicionar coluna de status visual
            df_discagens_display['Status'] = df_discagens_display.apply(
                lambda row: '🎯 Efetiva' if row['efetiva'] else ('✅ Atendida' if row['Resultado'] == 'Atendida' else '❌ Não Atendida'),
                axis=1
            )
            
            st.info(f"📊 Total de {len(df_discagens_display)} discagens no período")
            
            st.dataframe(
                df_discagens_display[['Vendedor', 'Atendente', 'Ramal', 'atendido_em_formatado', 'duration_formatada', 'Resultado', 'Status', 'Gravação']],
                column_config={
                    "Vendedor": st.column_config.TextColumn("Vendedor"),
                    "Atendente": st.column_config.TextColumn("Atendente"),
                    "Ramal": st.column_config.NumberColumn("Ramal", format="%d"),
                    "atendido_em_formatado": st.column_config.TextColumn("Data/Hora"),
                    "duration_formatada": st.column_config.TextColumn("Duração"),
                    "Resultado": st.column_config.TextColumn("Resultado"),
                    "Status": st.column_config.TextColumn("Status"),
                    "Gravação": st.column_config.LinkColumn("🔊 Gravação", display_text="Ouvir")
                },
                hide_index=True,
                width='stretch',
                height=min(500, len(df_discagens_display) * 35 + 100)
            )
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 7: INSIGHTS ADICIONAIS
            # ========================================
            st.markdown("### 💡 Insights e Recomendações Detalhadas")
            
            col_ins1, col_ins2, col_ins3 = st.columns(3)
            
            # Calcular métricas adicionais para insights
            if 'atendido_em' in df_vendedor.columns:
                df_vendedor['hora'] = pd.to_datetime(df_vendedor['atendido_em']).dt.hour
                # Top 3 horários com mais ligações efetivas
                top_horarios = df_vendedor[df_vendedor['efetiva']].groupby('hora').size().sort_values(ascending=False).head(3) if df_vendedor['efetiva'].sum() > 0 else None
            else:
                top_horarios = None
            
            with col_ins1:
                if top_horarios is not None and len(top_horarios) > 0:
                    # Construir HTML para os top 3 horários
                    medals = ["🥇", "🥈", "🥉"]
                    horarios_list = []
                    for i, (hora, qtd) in enumerate(top_horarios.items()):
                        medal = medals[i] if i < 3 else ""
                        hora_int = int(hora)
                        qtd_int = int(qtd)
                        horarios_list.append(
                            '<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">'
                            f'<span style="font-size: 1.1rem; color: #ffffff;">{medal} {hora_int}h - {hora_int+1}h</span>'
                            f'<span style="font-size: 1.1rem; font-weight: 700; color: #20B2AA;">{qtd_int} efetivas</span>'
                            '</div>'
                        )
                    horarios_html = "".join(horarios_list)
                    
                    html_card1 = (
                        '<div class="metric-card">'
                        '<h4 style="margin-top: 0; color: #20B2AA;">🕐 Top 3 Melhores Horários</h4>'
                        '<p style="font-size: 0.85rem; color: #CBD5E0; margin-bottom: 15px;">Horários com mais ligações efetivas</p>'
                        f'{horarios_html}'
                        '<p style="font-size: 0.85rem; color: #CBD5E0; margin-bottom: 0; margin-top: 12px;">'
                        '💡 <b>Dica:</b> Concentre as ligações nesses horários para maximizar resultados.'
                        '</p>'
                        '</div>'
                    )
                    st.markdown(html_card1, unsafe_allow_html=True)
                else:
                    st.info("📊 Dados insuficientes para análise de horário")
            
            with col_ins2:
                # Definir cores e textos
                if taxa_conversao_geral >= 15:
                    status_color = "#48bb78" # Green
                    status_text = "EXCELENTE"
                    status_icon = "✅"
                elif taxa_conversao_geral >= 10:
                    status_color = "#4299e1" # Blue
                    status_text = "BOM"
                    status_icon = "⚠️"
                else:
                    status_color = "#f56565" # Red
                    status_text = "ATENÇÃO"
                    status_icon = "📉"
                
                html_card2 = f"""
                <div class="metric-card">
                    <h4 style="margin-top: 0; color: #20B2AA;">📊 Performance</h4>
                    <div style="text-align: center; margin: 15px 0;">
                        <span style="font-size: 1.5rem; font-weight: 800; color: {status_color};">{status_icon} {status_text}</span><br>
                        <span style="font-size: 0.9rem; color: #CBD5E0;">Conversão Geral: <b style="color: #ffffff;">{taxa_conversao_geral:.1f}%</b></span>
                    </div>
                    <hr style="margin: 10px 0; border-color: rgba(32, 178, 170, 0.2);">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="text-align: center;">
                            <span style="font-size: 0.8rem; color: #CBD5E0;">Atendimento</span><br>
                            <span style="font-size: 1.1rem; font-weight: 600; color: #ffffff;">{taxa_atendimento:.1f}%</span>
                        </div>
                        <div style="text-align: center;">
                            <span style="font-size: 0.8rem; color: #CBD5E0;">Efetividade</span><br>
                            <span style="font-size: 1.1rem; font-weight: 600; color: #ffffff;">{taxa_efetividade:.1f}%</span>
                        </div>
                    </div>
                </div>
                """
                st.markdown(html_card2, unsafe_allow_html=True)
            
            with col_ins3:
                meta_efetivas = int(total_discagens * 0.15)  # Meta: 15% de conversão
                diff_meta = total_efetivas - meta_efetivas
                percentual_meta = (total_efetivas / meta_efetivas * 100) if meta_efetivas > 0 else 0
                
                if diff_meta >= 0:
                    meta_color = "#48bb78" # Green
                    meta_msg = f"✅ <b>Meta Atingida!</b> +{diff_meta} ligações"
                else:
                    meta_color = "#ed8936" # Orange
                    meta_msg = f"📊 <b>Faltam {abs(diff_meta)}</b> ligações"
                
                # Limit progress bar to 100%
                prog_width = int(min(percentual_meta, 100))
                total_efetivas_int = int(total_efetivas)
                
                html_card3 = f"""
                <div class="metric-card">
                    <h4 style="margin-top: 0; color: #20B2AA;">🎯 Meta Efetivas</h4>
                    <span style="color: #20B2AA;">(15% do total de discagens)</span>
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 15px;">
                        <div>
                            <span style="font-size: 2rem; font-weight: 800; color: #ffffff;">{total_efetivas_int}</span>
                            <span style="font-size: 0.9rem; color: #CBD5E0;"> / {meta_efetivas}</span>
                        </div>
                        <span style="font-size: 1.2rem; font-weight: 700; color: {meta_color};">{percentual_meta:.0f}%</span>
                    </div>
                    <div style="width: 100%%; background-color: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; margin: 10px 0;">
                        <div style="width: {prog_width}%%; background-color: {meta_color}; height: 8px; border-radius: 4px;"></div>
                    </div>
                    <p style="font-size: 0.9rem; color: {meta_color}; margin-bottom: 0; margin-top: 5px;">{meta_msg}</p>
                </div>
                """
                st.markdown(html_card3, unsafe_allow_html=True)
            
        else:
            st.info("Nenhuma chamada encontrada para os vendedores selecionados no período.")
    else:
        st.info("⚠️ Dados de chamadas não disponíveis. Certifique-se de que a função RPC 'get_chamadas_vendedores' está configurada no banco de dados.")

# ========================================
# ABA 8: MURAL DE VENDAS
# ========================================
with tab8:
    st.markdown("### 💰 Mural de Vendas")
    st.caption("Análise completa de vendas e desempenho comercial")
    
    # Filtrar apenas leads com venda
    df_vendas = df_leads[df_leads['data_venda'].notna()].copy()
    
    # Filtrar por data de venda dentro do período
    df_vendas = df_vendas[
        (df_vendas['data_venda'].dt.date >= data_inicio) & 
        (df_vendas['data_venda'].dt.date <= data_fim)
    ]
    
    if not df_vendas.empty:
        # ========================================
        # SEÇÃO 1: MÉTRICAS GERAIS DE VENDAS
        # ========================================
        st.markdown("#### 📊 Métricas Gerais")
        
        col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
        
        with col_v1:
            total_vendas = len(df_vendas)
            st.metric("💰 Total de Vendas", f"{total_vendas:,}".replace(",", "."))
        
        with col_v2:
            # Calcular tempo médio de venda (da criação até a venda) em dias
            df_vendas['tempo_venda'] = (df_vendas['data_venda'].dt.normalize() - df_vendas['criado_em'].dt.normalize()).dt.days
            tempo_medio_venda = df_vendas['tempo_venda'].mean()
            st.metric("⏱️ Tempo Médio de Venda", f"{tempo_medio_venda:.1f} dias")
        
        with col_v3:
            # Taxa de conversão do período
            total_leads_periodo = len(df_leads)
            if total_leads_periodo > 0:
                taxa_conversao_periodo = (total_vendas / total_leads_periodo) * 100
                st.metric("📈 Taxa de Conversão", f"{taxa_conversao_periodo:.1f}%")
            else:
                st.metric("📈 Taxa de Conversão", "0%")
        
        with col_v4:
            # Vendedor mais produtivo
            if 'vendedor' in df_vendas.columns:
                vendedor_top = df_vendas['vendedor'].value_counts().index[0] if len(df_vendas) > 0 else "N/A"
                vendas_top = df_vendas['vendedor'].value_counts().iloc[0] if len(df_vendas) > 0 else 0
                st.metric("🏆 Top Vendedor", vendedor_top if len(str(vendedor_top)) < 15 else str(vendedor_top)[:12] + "...")
                st.caption(f"{vendas_top} vendas")
        
        with col_v5:
            # Tempo mais rápido de venda
            if 'tempo_venda' in df_vendas.columns:
                tempo_min = df_vendas['tempo_venda'].min()
                st.metric("⚡ Venda Mais Rápida", f"{tempo_min:.1f} dias")
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 2: VENDAS POR VENDEDOR
        # ========================================
        st.markdown("#### 👥 Desempenho por Vendedor")
        
        if 'vendedor' in df_vendas.columns:
            # Agregar dados por vendedor
            df_vendedor_stats = df_vendas.groupby('vendedor').agg({
                'id': 'count',
                'tempo_venda': 'mean',
                'criado_em': 'count'
            }).reset_index()
            
            df_vendedor_stats.columns = ['Vendedor', 'Total Vendas', 'Tempo Médio (dias)', 'Leads']
            df_vendedor_stats['Tempo Médio (dias)'] = df_vendedor_stats['Tempo Médio (dias)'].round(1)
            df_vendedor_stats = df_vendedor_stats.sort_values('Total Vendas', ascending=False)
            
            # Calcular taxa de conversão por vendedor
            vendas_por_vendedor = df_vendas.groupby('vendedor').size()
            leads_por_vendedor = df_leads.groupby('vendedor').size()
            
            df_vendedor_stats['Taxa Conversão (%)'] = df_vendedor_stats['Vendedor'].apply(
                lambda v: (vendas_por_vendedor.get(v, 0) / leads_por_vendedor.get(v, 1)) * 100 if leads_por_vendedor.get(v, 0) > 0 else 0
            ).round(1)
            
            col_chart_v1, col_chart_v2 = st.columns(2)
            
            with col_chart_v1:
                # Gráfico de barras - Vendas por vendedor
                fig_vendas_vendedor = px.bar(
                    df_vendedor_stats.head(10),
                    x='Vendedor',
                    y='Total Vendas',
                    title='Top 10 Vendedores - Total de Vendas',
                    labels={'Vendedor': 'Vendedor', 'Total Vendas': 'Quantidade'},
                    color='Total Vendas',
                    color_continuous_scale='Blues'
                )
                fig_vendas_vendedor.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_vendas_vendedor, use_container_width=True)
            
            with col_chart_v2:
                # Gráfico de barras - Taxa de conversão por vendedor
                fig_conversao_vendedor = px.bar(
                    df_vendedor_stats.head(10),
                    x='Vendedor',
                    y='Taxa Conversão (%)',
                    title='Top 10 Vendedores - Taxa de Conversão',
                    labels={'Vendedor': 'Vendedor', 'Taxa Conversão (%)': 'Taxa (%)'},
                    color='Taxa Conversão (%)',
                    color_continuous_scale='Greens'
                )
                fig_conversao_vendedor.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_conversao_vendedor, use_container_width=True)
            
            # Tabela de desempenho
            st.dataframe(
                df_vendedor_stats,
                column_config={
                    "Vendedor": st.column_config.TextColumn("Vendedor"),
                    "Total Vendas": st.column_config.NumberColumn("Vendas", format="%d"),
                    "Tempo Médio (dias)": st.column_config.NumberColumn("Tempo Médio", format="%.1f"),
                    "Taxa Conversão (%)": st.column_config.NumberColumn("Taxa Conversão", format="%.1f%%")
                },
                hide_index=True,
                width='stretch',
                height=min(400, len(df_vendedor_stats) * 35 + 100)
            )
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 3: HISTÓRICO DE VENDAS
        # ========================================
        st.markdown("#### 📈 Histórico de Vendas")
        
        # Criar range completo de datas do período
        date_range_vendas = pd.date_range(start=data_inicio, end=data_fim, freq='D')
        df_todas_datas = pd.DataFrame({'data_venda_formatada': date_range_vendas.date})
        
        # Vendas por dia
        df_vendas['data_venda_formatada'] = df_vendas['data_venda'].dt.date
        df_vendas_dia = df_vendas.groupby('data_venda_formatada').size().reset_index(name='vendas')
        
        # Merge com todas as datas do período, preenchendo com 0 onde não há vendas
        df_vendas_dia = df_todas_datas.merge(df_vendas_dia, on='data_venda_formatada', how='left')
        df_vendas_dia['vendas'] = df_vendas_dia['vendas'].fillna(0).astype(int)
        
        df_vendas_dia['data_venda_formatada'] = pd.to_datetime(df_vendas_dia['data_venda_formatada'])
        df_vendas_dia = df_vendas_dia.sort_values('data_venda_formatada')
        df_vendas_dia['Data'] = df_vendas_dia['data_venda_formatada'].dt.strftime('%d/%m')
        
        col_hist1, col_hist2 = st.columns([2, 1])
        
        with col_hist1:
            # Gráfico de linha - Vendas ao longo do tempo
            fig_historico = px.line(
                df_vendas_dia,
                x='Data',
                y='vendas',
                title='Evolução de Vendas no Período',
                labels={'Data': 'Data', 'vendas': 'Quantidade de Vendas'},
                markers=True
            )
            fig_historico.update_traces(line_color='#4A9FFF', line_width=3)
            fig_historico.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig_historico, use_container_width=True)
        
        with col_hist2:
            st.markdown("**Estatísticas do Período**")
            
            # Calcular estatísticas
            media_vendas_dia = df_vendas_dia['vendas'].mean()
            max_vendas_dia = df_vendas_dia['vendas'].max()
            min_vendas_dia = df_vendas_dia['vendas'].min()
            
            st.metric("📊 Média por Dia", f"{media_vendas_dia:.1f}")
            st.metric("📈 Melhor Dia", f"{int(max_vendas_dia)}")
            st.metric("📉 Pior Dia", f"{int(min_vendas_dia)}")
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 4: INSIGHTS DE VENDAS
        # ========================================
        st.markdown("#### 💡 Insights e Análises")
        
        col_ins1, col_ins2 = st.columns(2)
        
        with col_ins1:
            st.markdown("**🔍 Distribuição por Dia da Semana**")
            
            # Vendas por dia da semana
            df_vendas['dia_semana'] = df_vendas['data_venda'].dt.day_name()
            dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            
            df_dia_semana = df_vendas['dia_semana'].value_counts().reindex(dias_ordem, fill_value=0).reset_index()
            df_dia_semana.columns = ['dia', 'vendas']
            df_dia_semana['dia'] = dias_pt
            
            fig_dia_semana = px.bar(
                df_dia_semana,
                x='dia',
                y='vendas',
                title='Vendas por Dia da Semana',
                labels={'dia': 'Dia', 'vendas': 'Vendas'},
                color='vendas',
                color_continuous_scale='Blues'
            )
            fig_dia_semana.update_layout(height=350)
            st.plotly_chart(fig_dia_semana, use_container_width=True)
        
        with col_ins2:
            st.markdown("**📋 Distribuição por Pipeline**")
            
            if 'pipeline' in df_vendas.columns:
                df_pipeline = df_vendas['pipeline'].value_counts().reset_index()
                df_pipeline.columns = ['Pipeline', 'Vendas']
                
                fig_pipeline = px.pie(
                    df_pipeline,
                    values='Vendas',
                    names='Pipeline',
                    title='Vendas por Pipeline'
                )
                fig_pipeline.update_layout(height=350)
                st.plotly_chart(fig_pipeline, use_container_width=True)
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 5: ANÁLISE DE CICLO DE VENDA
        # ========================================
        st.markdown("#### ⏱️ Análise do Ciclo de Venda")
        
        col_ciclo1, col_ciclo2 = st.columns(2)
        
        with col_ciclo1:
            # Distribuição do tempo de venda
            fig_tempo_dist = px.histogram(
                df_vendas,
                x='tempo_venda',
                nbins=20,
                title='Distribuição do Tempo de Venda (em dias)',
                labels={'tempo_venda': 'Dias até Venda', 'count': 'Quantidade'},
                color_discrete_sequence=['#4A9FFF']
            )
            fig_tempo_dist.update_layout(height=350)
            st.plotly_chart(fig_tempo_dist, use_container_width=True)
        
        with col_ciclo2:
            st.markdown("**📊 Estatísticas de Tempo**")
            
            quartis = df_vendas['tempo_venda'].quantile([0.25, 0.5, 0.75])
            
            st.metric("25% das vendas em até", f"{quartis[0.25]:.1f} dias")
            st.metric("50% das vendas em até", f"{quartis[0.5]:.1f} dias")
            st.metric("75% das vendas em até", f"{quartis[0.75]:.1f} dias")
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 6: TABELA DETALHADA DE VENDAS
        # ========================================
        st.markdown("#### 📋 Detalhes das Vendas")
        
        # Preparar tabela de vendas
        df_vendas_table = df_vendas[['id', 'lead_name', 'vendedor', 'pipeline', 'criado_em', 'data_venda', 'tempo_venda']].copy()
        df_vendas_table['criado_em'] = df_vendas_table['criado_em'].dt.strftime('%d/%m/%Y')
        df_vendas_table['data_venda'] = df_vendas_table['data_venda'].dt.strftime('%d/%m/%Y')
        df_vendas_table['tempo_venda'] = df_vendas_table['tempo_venda'].round(1)
        
        # Adicionar link do Kommo
        df_vendas_table['Link'] = df_vendas_table['id'].apply(generate_kommo_link)
        
        df_vendas_table = df_vendas_table.rename(columns={
            'lead_name': 'Lead',
            'vendedor': 'Vendedor',
            'pipeline': 'Pipeline',
            'criado_em': 'Data Criação',
            'data_venda': 'Data Venda',
            'tempo_venda': 'Tempo (dias)'
        })
        
        # Remover coluna ID após criar link
        df_vendas_table = df_vendas_table.drop(columns=['id'])
        
        st.dataframe(
            df_vendas_table.sort_values('Data Venda', ascending=False),
            column_config={
                "Lead": st.column_config.TextColumn("Lead"),
                "Vendedor": st.column_config.TextColumn("Vendedor"),
                "Pipeline": st.column_config.TextColumn("Pipeline"),
                "Data Criação": st.column_config.TextColumn("Criado em"),
                "Data Venda": st.column_config.TextColumn("Vendido em"),
                "Tempo (dias)": st.column_config.NumberColumn("Ciclo (dias)", format="%.1f"),
                "Link": st.column_config.LinkColumn("Link Kommo", display_text="Abrir")
            },
            hide_index=True,
            width='stretch',
            height=min(500, len(df_vendas_table) * 35 + 100)
        )
    else:
        st.info("📊 Nenhuma venda registrada no período selecionado.")
        st.caption("Ajuste os filtros na barra lateral para visualizar vendas de outros períodos.")

# ========================================
# ABA 9: DEMOS REALIZADAS
# ========================================
with tab9:
    st.markdown("### ✅ Demonstrações Realizadas")
    st.caption("Análise completa das demonstrações realizadas no período")
    
    # Filtrar demos realizadas usando constante DEMO_COMPLETED_STATUSES
    demos_realizadas_df = df_leads[
        (df_leads['data_demo'].notna()) &
        (df_leads['data_demo'] >= pd.Timestamp(datetime.combine(data_inicio, datetime.min.time()))) &
        (df_leads['data_demo'] <= pd.Timestamp(datetime.combine(data_fim, datetime.max.time()))) &
        (
            (
                (df_leads['status'] == 'Desqualificados') &
                (df_leads['data_demo'].notna()) &
                (df_leads['data_noshow'].isna())
            ) |
            (
                (df_leads['data_demo'].notna()) &
                (df_leads['status'].isin(DEMO_COMPLETED_STATUSES))
            )
        )
    ].copy()
    
    if not demos_realizadas_df.empty:
        # ========================================
        # SEÇÃO 1: MÉTRICAS GERAIS
        # ========================================
        col_dr1, col_dr2, col_dr3, col_dr4 = st.columns(4)
        
        with col_dr1:
            total_demos = len(demos_realizadas_df)
            st.metric("✅ Total Demos Realizadas", f"{total_demos:,}".replace(",", "."))
        
        with col_dr2:
            # Contar vendas ganhas no período (usando df_leads filtrado)
            demos_convertidas = len(df_leads[
                (df_leads['data_venda'].notna()) &
                (df_leads['data_venda'] >= pd.Timestamp(datetime.combine(data_inicio, datetime.min.time()))) &
                (df_leads['data_venda'] <= pd.Timestamp(datetime.combine(data_fim, datetime.max.time())))
            ])
            st.metric("💰 Demos Convertidas", f"{demos_convertidas:,}".replace(",", "."))
        
        with col_dr3:
            demos_desqualificadas = len(demos_realizadas_df[demos_realizadas_df['status'] == 'Desqualificados'])
            st.metric("❌ Demos Desqualificadas", f"{demos_desqualificadas:,}".replace(",", "."))
        
        with col_dr4:
            taxa_conversao_demo = (demos_convertidas / total_demos * 100) if total_demos > 0 else 0
            st.metric("📈 Taxa de Conversão", f"{taxa_conversao_demo:.1f}%")
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 2: ROI MARKETING - ANÁLISE DE CAMPANHAS
        # ========================================
        st.markdown("#### 📣 ROI Marketing - Análise de Campanhas")
        st.caption("Identifique quais campanhas geram mais demos e quais desqualificam mais")
        
        # Verificar se existem colunas de UTM
        utm_cols_disponiveis = []
        for col in ['utm_campaign', 'utm_source', 'utm_medium']:
            if col in demos_realizadas_df.columns:
                utm_cols_disponiveis.append(col)
        
        if utm_cols_disponiveis:
            # Seletor de dimensão UTM
            col_utm_select, col_utm_info = st.columns([1, 2])
            
            with col_utm_select:
                utm_selecionada = st.selectbox(
                    "Analisar por:",
                    options=utm_cols_disponiveis,
                    format_func=lambda x: {
                        'utm_campaign': '🎯 Campanha (utm_campaign)',
                        'utm_source': '🌐 Fonte (utm_source)',
                        'utm_medium': '📱 Mídia (utm_medium)'
                    }.get(x, x),
                    key="utm_roi_select"
                )
            
            with col_utm_info:
                st.info(f"📊 Mostrando análise por **{utm_selecionada.replace('utm_', '').title()}**")
            
            # Preparar dados de análise de demos
            df_utm_analise = demos_realizadas_df.copy()
            df_utm_analise[utm_selecionada] = df_utm_analise[utm_selecionada].fillna('(não informado)')
            df_utm_analise[utm_selecionada] = df_utm_analise[utm_selecionada].replace('', '(não informado)')
            
            # Agrupar demos por UTM (total e desqualificados)
            df_demos_por_utm = df_utm_analise.groupby(utm_selecionada).agg(
                total_demos=('id', 'count'),
                desqualificados=('status', lambda x: (x == 'Desqualificados').sum())
            ).reset_index()
            
            # Pegar vendas do período e agrupar por UTM (convertidos)
            df_vendas_periodo = df_leads[
                (df_leads['data_venda'].notna()) &
                (df_leads['data_venda'] >= pd.Timestamp(datetime.combine(data_inicio, datetime.min.time()))) &
                (df_leads['data_venda'] <= pd.Timestamp(datetime.combine(data_fim, datetime.max.time())))
            ].copy()
            df_vendas_periodo[utm_selecionada] = df_vendas_periodo[utm_selecionada].fillna('(não informado)')
            df_vendas_periodo[utm_selecionada] = df_vendas_periodo[utm_selecionada].replace('', '(não informado)')
            
            df_vendas_por_utm = df_vendas_periodo.groupby(utm_selecionada).agg(
                convertidos=('id', 'count')
            ).reset_index()
            
            # Fazer merge dos dois DataFrames
            df_utm_resumo = df_demos_por_utm.merge(df_vendas_por_utm, on=utm_selecionada, how='left')
            df_utm_resumo['convertidos'] = df_utm_resumo['convertidos'].fillna(0).astype(int)
            
            # Calcular percentuais
            df_utm_resumo['taxa_desqualificacao'] = (df_utm_resumo['desqualificados'] / df_utm_resumo['total_demos'] * 100).round(1)
            df_utm_resumo['taxa_conversao'] = (df_utm_resumo['convertidos'] / df_utm_resumo['total_demos'] * 100).round(1)
            df_utm_resumo['aproveitamento'] = df_utm_resumo['total_demos'] - df_utm_resumo['desqualificados']
            
            # Ordenar por total de demos (decrescente)
            df_utm_resumo = df_utm_resumo.sort_values('total_demos', ascending=False)
            
            # Renomear coluna UTM para exibição
            df_utm_resumo = df_utm_resumo.rename(columns={utm_selecionada: 'Campanha/Fonte'})
            
            st.markdown("")
            
            # Exibir métricas resumidas
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                total_campanhas = len(df_utm_resumo[df_utm_resumo['Campanha/Fonte'] != '(não informado)'])
                st.metric("🎯 Campanhas Ativas", total_campanhas)
            
            with col_m2:
                melhor_campanha = df_utm_resumo[df_utm_resumo['Campanha/Fonte'] != '(não informado)'].nlargest(1, 'total_demos')
                if not melhor_campanha.empty:
                    camp_nome = melhor_campanha['Campanha/Fonte'].iloc[0]
                    camp_demos = melhor_campanha['total_demos'].iloc[0]
                    st.metric("🏆 Mais Demos", f"{camp_demos}", delta=f"Campanha: {camp_nome}", delta_color="off")
                else:
                    st.metric("🏆 Mais Demos", "-")
            
            with col_m3:
                # Campanha com melhor taxa de conversão (mínimo 3 demos)
                df_com_conversao = df_utm_resumo[(df_utm_resumo['Campanha/Fonte'] != '(não informado)') & (df_utm_resumo['total_demos'] >= 3)]
                if not df_com_conversao.empty:
                    melhor_conversao = df_com_conversao.nlargest(1, 'taxa_conversao')
                    st.metric("💰 Melhor Conversão", f"{melhor_conversao['taxa_conversao'].iloc[0]:.0f}%", delta=f"Campanha: {melhor_conversao['Campanha/Fonte'].iloc[0]}", delta_color="off")
                else:
                    st.metric("💰 Melhor Conversão", "-")
            
            with col_m4:
                # Campanha com maior desqualificação (alerta)
                df_com_desq = df_utm_resumo[(df_utm_resumo['Campanha/Fonte'] != '(não informado)') & (df_utm_resumo['total_demos'] >= 3)]
                if not df_com_desq.empty:
                    pior_campanha = df_com_desq.nlargest(1, 'taxa_desqualificacao')
                    st.metric("⚠️ Maior Desqualificação", f"{pior_campanha['taxa_desqualificacao'].iloc[0]:.0f}%", delta=f"Campanha: {pior_campanha['Campanha/Fonte'].iloc[0]}", delta_color="inverse")
                else:
                    st.metric("⚠️ Maior Desqualificação", "-")
            
            st.markdown("")
            
            # Gráficos lado a lado
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                # Top 10 campanhas por volume de demos
                df_top10 = df_utm_resumo.nlargest(10, 'total_demos').copy()
                
                # Preparar dados para gráfico de barras sobrepostas
                df_top10_melted = df_top10.melt(
                    id_vars=['Campanha/Fonte'],
                    value_vars=['total_demos', 'convertidos'],
                    var_name='Métrica',
                    value_name='Quantidade'
                )
                df_top10_melted['Métrica'] = df_top10_melted['Métrica'].map({
                    'total_demos': 'Demos',
                    'convertidos': 'Convertidos'
                })
                # Ordenar para que Demos seja renderizado primeiro (embaixo) e Convertidos por cima
                df_top10_melted['ordem'] = df_top10_melted['Métrica'].map({'Demos': 2, 'Convertidos': 1})
                df_top10_melted = df_top10_melted.sort_values('ordem')
                
                fig_demos = px.bar(
                    df_top10_melted,
                    x='Quantidade',
                    range_x=[0, df_top10_melted['Quantidade'].max()+2],
                    y='Campanha/Fonte',
                    color='Métrica',
                    orientation='h',
                    title='📊 Top 10 - Demos e Conversões por Campanha',
                    labels={'Quantidade': 'Quantidade', 'Campanha/Fonte': ''},
                    color_discrete_map={'Demos': '#4A9FFF', 'Convertidos': '#48BB78'},
                    text='Quantidade',
                    barmode='group'
                )
                fig_demos.update_layout(
                    height=450,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    ),
                    yaxis={'categoryorder': 'total ascending'}
                )
                fig_demos.update_traces(textposition='outside', textfont_size=11)
                st.plotly_chart(fig_demos, use_container_width=True)
            
            with col_graf2:
                # Taxa de desqualificação por campanha (mínimo 3 demos)
                df_desq = df_utm_resumo[df_utm_resumo['total_demos'] >= 3].nlargest(10, 'taxa_desqualificacao').copy()
                
                if not df_desq.empty:
                    fig_desq = px.bar(
                        df_desq,
                        x='taxa_desqualificacao',
                        range_x=[0, df_desq['taxa_desqualificacao'].max()+10],
                        y='Campanha/Fonte',
                        orientation='h',
                        title='⚠️ Taxa de Desqualificação por Campanha',
                        labels={'taxa_desqualificacao': 'Taxa de Desqualificação (%)', 'Campanha/Fonte': ''},
                        color='taxa_desqualificacao',
                        color_continuous_scale='Reds',
                        text=df_desq['taxa_desqualificacao'].apply(lambda x: f'{x:.1f}%')
                    )
                    fig_desq.update_layout(
                        height=400,
                        showlegend=False,
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    fig_desq.update_traces(textposition='outside', textfont_size=12)
                    st.plotly_chart(fig_desq, use_container_width=True)
                else:
                    st.info("Dados insuficientes para análise de desqualificação (mínimo 3 demos por campanha)")
            
            st.markdown("")
            
            # Tabela detalhada
            st.markdown("##### 📋 Detalhamento por Campanha")
            
            # Formatar tabela para exibição
            df_tabela_utm = df_utm_resumo.copy()
            df_tabela_utm = df_tabela_utm.rename(columns={
                'total_demos': 'Demos',
                'desqualificados': 'Desqualificados',
                'convertidos': 'Vendas',
                'taxa_desqualificacao': '% Desqualificação',
                'taxa_conversao': '% Conversão',
                'aproveitamento': 'Aproveitamento'
            })
            
            st.dataframe(
                df_tabela_utm[['Campanha/Fonte', 'Demos', 'Aproveitamento', 'Desqualificados', 'Vendas', '% Desqualificação', '% Conversão']],
                column_config={
                    "Campanha/Fonte": st.column_config.TextColumn("Campanha/Fonte", width="large"),
                    "Demos": st.column_config.NumberColumn("Demos", format="%d"),
                    "Aproveitamento": st.column_config.NumberColumn("Aproveitamento", format="%d", help="Demos - Desqualificados"),
                    "Desqualificados": st.column_config.NumberColumn("Desqualificados", format="%d"),
                    "Vendas": st.column_config.NumberColumn("Vendas", format="%d"),
                    "% Desqualificação": st.column_config.NumberColumn("% Desq.", format="%.1f%%"),
                    "% Conversão": st.column_config.NumberColumn("% Conv.", format="%.1f%%")
                },
                hide_index=True,
                width='stretch',
                height=min(400, len(df_tabela_utm) * 35 + 50)
            )
            
            # Insights automáticos
            st.markdown("")
            with st.expander("💡 Insights Automáticos de Marketing"):
                insights = []
                
                # Insight 1: Campanha com mais demos
                top_camp = df_utm_resumo[df_utm_resumo['Campanha/Fonte'] != '(não informado)'].nlargest(1, 'total_demos')
                if not top_camp.empty:
                    insights.append(f"🏆 **Maior volume:** A campanha **{top_camp['Campanha/Fonte'].iloc[0]}** gerou {top_camp['total_demos'].iloc[0]} demos ({top_camp['total_demos'].iloc[0]/df_utm_resumo['total_demos'].sum()*100:.1f}% do total).")
                
                # Insight 2: Campanha com melhor conversão
                df_conv = df_utm_resumo[(df_utm_resumo['Campanha/Fonte'] != '(não informado)') & (df_utm_resumo['total_demos'] >= 3) & (df_utm_resumo['convertidos'] > 0)]
                if not df_conv.empty:
                    best_conv = df_conv.nlargest(1, 'taxa_conversao')
                    insights.append(f"💰 **Melhor conversão:** A campanha **{best_conv['Campanha/Fonte'].iloc[0]}** tem taxa de conversão de {best_conv['taxa_conversao'].iloc[0]:.1f}%.")
                
                # Insight 3: Campanha problemática
                df_prob = df_utm_resumo[(df_utm_resumo['Campanha/Fonte'] != '(não informado)') & (df_utm_resumo['total_demos'] >= 5) & (df_utm_resumo['taxa_desqualificacao'] > 50)]
                if not df_prob.empty:
                    worst = df_prob.nlargest(1, 'taxa_desqualificacao')
                    insights.append(f"⚠️ **Atenção:** A campanha **{worst['Campanha/Fonte'].iloc[0]}** tem {worst['taxa_desqualificacao'].iloc[0]:.1f}% de desqualificação. Considere revisar o público-alvo ou a qualificação.")
                
                # Insight 4: Leads sem UTM
                sem_utm = df_utm_resumo[df_utm_resumo['Campanha/Fonte'] == '(não informado)']
                if not sem_utm.empty and sem_utm['total_demos'].iloc[0] > 0:
                    pct_sem_utm = sem_utm['total_demos'].iloc[0] / df_utm_resumo['total_demos'].sum() * 100
                    insights.append(f"📊 **Rastreamento:** {pct_sem_utm:.1f}% das demos ({sem_utm['total_demos'].iloc[0]}) não possuem UTM. Melhore o tracking para análises mais precisas.")
                
                if insights:
                    for insight in insights:
                        st.markdown(insight)
                else:
                    st.info("Dados insuficientes para gerar insights automáticos.")
        
        else:
            st.warning("⚠️ Colunas de UTM (utm_campaign, utm_source, utm_medium) não encontradas nos dados.")
            st.caption("Verifique se os leads possuem informações de rastreamento de marketing.")
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 3: TABELA DE DEMOS REALIZADAS
        # ========================================
        st.markdown("#### 📋 Lista de Demonstrações Realizadas")
        
        # Preparar DataFrame para exibição
        df_demos_display = demos_realizadas_df[['id', 'lead_name', 'vendedor', 'data_demo', 'status']].copy()
        df_demos_display.columns = ['ID', 'Lead', 'Vendedor', 'Data Demo', 'Status']
        
        # Formatar data
        df_demos_display['Data Demo'] = df_demos_display['Data Demo'].dt.strftime('%d/%m/%Y')
        
        # Ordenar por data (mais recente primeiro)
        df_demos_display = df_demos_display.sort_values('Data Demo', ascending=False)
        
        # Adicionar link
        df_demos_display['Link'] = df_demos_display['ID'].apply(generate_kommo_link)
        
        st.dataframe(
            df_demos_display[['Link', 'Lead', 'Vendedor', 'Data Demo', 'Status']],
            column_config={
                "Link": st.column_config.LinkColumn("🔗 Link", display_text="Abrir"),
                "Lead": st.column_config.TextColumn("Lead"),
                "Vendedor": st.column_config.TextColumn("Vendedor"),
                "Data Demo": st.column_config.TextColumn("Data Demo"),
                "Status": st.column_config.TextColumn("Status Atual")
            },
            hide_index=True,
            width='stretch',
            height=min(400, len(df_demos_display) * 35 + 100)
        )
        
        st.markdown("")
        
        # ========================================
        # SEÇÃO 4: ANÁLISE DE DESQUALIFICAÇÕES
        # ========================================
        if demos_desqualificadas > 0:
            st.markdown("#### ❌ Análise de Desqualificações")
            
            # Filtrar apenas desqualificados
            df_desqualificados = demos_realizadas_df[demos_realizadas_df['status'] == 'Desqualificados'].copy()
            
            # Verificar se existem as colunas de motivo e descrição
            if 'motivos_desqualificacao' in df_desqualificados.columns:
                # Contar motivos de desqualificação
                df_motivos = df_desqualificados['motivos_desqualificacao'].value_counts().reset_index()
                df_motivos.columns = ['Motivo', 'Quantidade']
                
                # Gráfico de barras horizontais
                col_graf, col_tabela = st.columns([2, 1])
                
                with col_graf:
                    fig_motivos = px.bar(
                        df_motivos,
                        y='Motivo',
                        x='Quantidade',
                        title='Motivos de Desqualificação',
                        orientation='h',
                        labels={'Motivo': 'Motivo', 'Quantidade': 'Quantidade'},
                        color='Quantidade',
                        color_continuous_scale='Reds'
                    )
                    fig_motivos.update_layout(height=max(300, len(df_motivos) * 40), showlegend=False)
                    st.plotly_chart(fig_motivos, use_container_width=True)
                
                with col_tabela:
                    st.markdown("**📊 Resumo**")
                    st.dataframe(
                        df_motivos,
                        column_config={
                            "Motivo": st.column_config.TextColumn("Motivo"),
                            "Quantidade": st.column_config.NumberColumn("Qtd", format="%d")
                        },
                        hide_index=True,
                        width='stretch',
                        height=max(300, len(df_motivos) * 35 + 50)
                    )
            else:
                st.info("ℹ️ Coluna 'motivos_desqualificacao' não encontrada nos dados.")
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 5: DESCRIÇÕES DAS DESQUALIFICAÇÕES
            # ========================================
            if 'descricao_desqualificacao' in df_desqualificados.columns:
                st.markdown("#### 📝 Descrições das Desqualificações")
                st.caption("Detalhes e observações sobre cada desqualificação")
                
                # Filtrar apenas registros com descrição
                df_com_descricao = df_desqualificados[
                    df_desqualificados['descricao_desqualificacao'].notna() & 
                    (df_desqualificados['descricao_desqualificacao'] != '')
                ].copy()
                
                if not df_com_descricao.empty:
                    # Preparar DataFrame para exibição
                    df_descricoes = df_com_descricao[
                        ['id', 'lead_name', 'vendedor', 'motivos_desqualificacao', 'descricao_desqualificacao', 'data_demo']
                    ].copy()
                    
                    df_descricoes.columns = ['ID', 'Lead', 'Vendedor', 'Motivo', 'Descrição', 'Data Demo']
                    df_descricoes['Data Demo'] = df_descricoes['Data Demo'].dt.strftime('%d/%m/%Y')
                    df_descricoes = df_descricoes.sort_values('Data Demo', ascending=False)
                    
                    # Adicionar link
                    df_descricoes['Link'] = df_descricoes['ID'].apply(generate_kommo_link)
                    
                    # Exibir tabela com descrições
                    st.dataframe(
                        df_descricoes[['Link', 'Lead', 'Vendedor', 'Motivo', 'Data Demo', 'Descrição']],
                        column_config={
                            "Link": st.column_config.LinkColumn("🔗 Link", display_text="Abrir"),
                            "Lead": st.column_config.TextColumn("Lead", width="medium"),
                            "Vendedor": st.column_config.TextColumn("Vendedor", width="small"),
                            "Motivo": st.column_config.TextColumn("Motivo", width="medium"),
                            "Data Demo": st.column_config.TextColumn("Data", width="small"),
                            "Descrição": st.column_config.TextColumn("Descrição", width="large")
                        },
                        hide_index=True,
                        width='stretch',
                        height=min(500, len(df_descricoes) * 50 + 100)
                    )
                    
                    # Opção de expandir descrições individuais
                    st.markdown("")
                    with st.expander("🔍 Ver Descrições Detalhadas (Uma por Vez)"):
                        lead_selecionado = st.selectbox(
                            "Selecione um lead para ver a descrição completa",
                            options=df_descricoes['Lead'].tolist(),
                            key="lead_descricao_select"
                        )
                        
                        if lead_selecionado:
                            descricao_completa = df_descricoes[df_descricoes['Lead'] == lead_selecionado].iloc[0]
                            
                            st.markdown(f"**Lead:** {descricao_completa['Lead']}")
                            st.markdown(f"**Vendedor:** {descricao_completa['Vendedor']}")
                            st.markdown(f"**Motivo:** {descricao_completa['Motivo']}")
                            st.markdown(f"**Data:** {descricao_completa['Data Demo']}")
                            st.markdown("**Descrição Completa:**")
                            st.info(descricao_completa['Descrição'])
                else:
                    st.info("ℹ️ Nenhuma desqualificação possui descrição preenchida.")
            else:
                st.info("ℹ️ Coluna 'descricao_desqualificacao' não encontrada nos dados.")
        else:
            st.success("✨ Nenhuma demonstração foi desqualificada no período!")
    else:
        st.info("ℹ️ Nenhuma demonstração realizada no período selecionado.")

# Footer
st.markdown("---")
st.caption("💡 **Dica**: Use os filtros na barra lateral para ajustar o período e vendedores.")
st.caption("🔄 Os dados são atualizados automaticamente a cada 30 minutos.")
