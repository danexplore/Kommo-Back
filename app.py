import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from supabase import create_client, Client
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Painel de Acompanhamento de Leads - Kommo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# CONFIGURAÇÃO DE STATUS DO KOMMO
# ========================================
# IMPORTANTE: Esta lista precisa ser ajustada de acordo com os status
# reais utilizados no Kommo CRM da ecosys AUTO.

# Status que indicam que a demo foi concluída
DEMO_COMPLETED_STATUSES = [
    "5 - Demonstração realizada",
    "6 - Lead quente",
    "5 - VISITA REALIZADA",
    "6 - EM Negociação",
]

# Status que indicam que o lead saiu do funil (conclusão/encerramento)
FUNNEL_CLOSED_STATUSES = [
    "Venda Ganha",
    "Desqualificados",
]

# Todos os status que indicam que o lead não precisa mais de ação
COMPLETED_STATUSES = DEMO_COMPLETED_STATUSES + FUNNEL_CLOSED_STATUSES

# Manter compatibilidade com código existente
STATUS_POS_DEMO = COMPLETED_STATUSES

# Configuração do Supabase
@st.cache_resource
def init_supabase():
    """Inicializa conexão com Supabase"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    if not url or not key:
        st.error("⚠️ Credenciais do Supabase não configuradas. Configure SUPABASE_URL e SUPABASE_KEY.")
        st.stop()
    
    return create_client(url, key)

supabase: Client = init_supabase()

# CSS customizado - Dark Mode sofisticado
st.markdown("""
    <style>
    /* Background geral */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    /* Main */
    .main {
        padding: 2rem 1.5rem;
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    /* Texto base */
    body {
        color: #ffffff;
    }
    
    /* Títulos */
    h1 {
        font-weight: 800;
        color: #4A9FFF;
        text-shadow: 0 2px 10px rgba(74, 159, 255, 0.3);
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        font-weight: 700;
        color: #4A9FFF;
        font-size: 1.8rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        font-weight: 600;
        color: #4A9FFF;
        font-size: 1.3rem;
    }
    
    /* Dividers */
    hr, .stDivider {
        border-color: rgba(74, 159, 255, 0.2);
    }
    
    /* Métricas */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(26, 31, 58, 0.8) 0%, rgba(15, 20, 40, 0.8) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(74, 159, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(74, 159, 255, 0.1);
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        color: #4A9FFF;
        text-shadow: 0 2px 8px rgba(74, 159, 255, 0.3);
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: #ffffff;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 0.9rem;
        color: #4A9FFF;
    }
    
    /* Tabelas */
    .stDataFrame {
        background: linear-gradient(135deg, rgba(26, 31, 58, 0.95) 0%, rgba(15, 20, 40, 0.95) 100%) !important;
        border-radius: 12px;
        border: 2px solid rgba(74, 159, 255, 0.25) !important;
        box-shadow: 0 8px 32px 0 rgba(74, 159, 255, 0.1);
        overflow: hidden;
    }
    
    .stDataFrame th {
        background: linear-gradient(135deg, rgba(74, 159, 255, 0.25) 0%, rgba(43, 127, 232, 0.15) 100%) !important;
        color: #4A9FFF !important;
        font-weight: 700;
        border: none !important;
        border-bottom: 2px solid rgba(74, 159, 255, 0.3) !important;
        padding: 12px !important;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.5px;
    }
    
    .stDataFrame td {
        border-color: rgba(74, 159, 255, 0.15) !important;
        color: #ffffff !important;
        padding: 10px 12px !important;
        border-bottom: 1px solid rgba(74, 159, 255, 0.08) !important;
    }
    
    .stDataFrame tr {
        background-color: transparent !important;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: rgba(74, 159, 255, 0.08) !important;
        border-left: 3px solid #4A9FFF !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background-color: rgba(74, 159, 255, 0.02) !important;
    }
    
    /* Alertas */
    .stAlert {
        background: linear-gradient(135deg, rgba(26, 31, 58, 0.9) 0%, rgba(15, 20, 40, 0.9) 100%);
        border-radius: 12px;
        border: 1px solid rgba(74, 159, 255, 0.3);
        color: #ffffff;
    }
    
    .stAlert-info {
        border-left: 4px solid #4A9FFF;
    }
    
    .stAlert-warning {
        border-left: 4px solid #ff8c00;
    }
    
    .stAlert-error {
        border-left: 4px solid #ff4444;
    }
    
    .stAlert-success {
        border-left: 4px solid #00ff88;
    }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid rgba(74, 159, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        padding: 0 28px;
        background-color: rgba(26, 31, 58, 0.6);
        border-radius: 12px 12px 0 0;
        font-weight: 600;
        color: #b0b0b0;
        border: 1px solid rgba(74, 159, 255, 0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(74, 159, 255, 0.2) 0%, rgba(43, 127, 232, 0.1) 100%);
        color: #4A9FFF;
        border: 2px solid #4A9FFF;
        border-bottom: none;
        box-shadow: 0 -4px 12px rgba(74, 159, 255, 0.15);
    }
    
    .stTabs [aria-selected="false"]:hover {
        background-color: rgba(74, 159, 255, 0.1);
        color: #ffffff;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #0f1428 0%, #1a1f3a 100%);
    }
    
    section[data-testid="stSidebar"] * {
        color: #ffffff;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #4A9FFF;
    }
    
    section[data-testid="stSidebar"] label {
        color: #ffffff;
        font-weight: 500;
    }
    
    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stMultiSelect > div > div {
        background-color: rgba(74, 159, 255, 0.08);
        border-color: rgba(74, 159, 255, 0.2);
        border-radius: 8px;
    }
    
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] select {
        background-color: rgba(74, 159, 255, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(74, 159, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    
    section[data-testid="stSidebar"] button {
        background: linear-gradient(135deg, #4A9FFF 0%, #2B7FE8 100%);
        color: #ffffff;
        border: none;
        font-weight: 600;
        border-radius: 8px;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background: linear-gradient(135deg, #5AAFFF 0%, #4A9FFF 100%);
        box-shadow: 0 4px 12px rgba(74, 159, 255, 0.3);
    }
    
    section[data-testid="stSidebar"] .stInfo, 
    section[data-testid="stSidebar"] .stWarning,
    section[data-testid="stSidebar"] .stError {
        background-color: rgba(74, 159, 255, 0.1);
        border-color: rgba(74, 159, 255, 0.3);
    }
    
    /* Links */
    a {
        color: #4A9FFF;
        text-decoration: none;
        font-weight: 600;
    }
    
    a:hover {
        color: #5AAFFF;
        text-decoration: underline;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        background-color: rgba(74, 159, 255, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(74, 159, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stNumberInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
    }
    
    /* Checkbox */
    .stCheckbox > label {
        color: #ffffff;
    }
    
    /* Caption */
    .caption {
        color: #a0a0a0;
    }
    
    /* Gradiente de destaque para cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(74, 159, 255, 0.1) 0%, rgba(43, 127, 232, 0.05) 100%);
        border-left: 4px solid #4A9FFF;
        border-radius: 12px;
        padding: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Funções de consulta ao banco
@st.cache_data(ttl=1800)  # Cache de 30 minutos
def get_leads_data(data_inicio: datetime, data_fim: datetime, vendedores: list = None):
    """Busca dados de leads da view kommo_leads_statistics"""
    try:
        query = supabase.table('kommo_leads_statistics').select('*')
        
        # Filtro de data (criado_em dentro do período)
        query = query.gte('criado_em', data_inicio.isoformat())
        query = query.lte('criado_em', data_fim.isoformat())
        
        # Filtro de vendedor (se especificado)
        if vendedores and len(vendedores) > 0:
            query = query.in_('vendedor', vendedores)
        
        response = query.execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Converter colunas de data
            date_columns = ['criado_em', 'data_agendamento', 'data_demo', 'data_noshow', 'data_venda']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados: {str(e)}")
        return pd.DataFrame()

def generate_kommo_link(lead_id):
    """Gera link clicável para o Kommo"""
    if pd.isna(lead_id):
        return ""
    return f"https://atendimentoecosysauto.kommo.com/leads/detail/{int(lead_id)}"

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

# Header
st.title("📊 Painel de Acompanhamento de Leads - Kommo")
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
hoje = datetime.now().date()

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
            max_value=datetime.now(),
            format="DD/MM/YYYY",
            key="data_inicio_custom"
        )
    
    with col2:
        data_fim = st.date_input(
            "Até",
            value=hoje,
            max_value=datetime.now(),
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
st.sidebar.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

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
hoje = pd.Timestamp(datetime.now().date())

# ========================================
# MÉTRICAS PRINCIPAIS (KPIs)
# ========================================
st.markdown("### 📊 Visão Geral do Período")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_leads = len(df_leads)
    st.metric("📥 Total de Leads", f"{total_leads:,}".replace(",", "."))

with col2:
    leads_com_demo = len(df_leads[df_leads['data_demo'].notna()])
    if total_leads > 0:
        pct_com_demo = (leads_com_demo / total_leads) * 100
        st.metric("📅 Com Demo", f"{leads_com_demo:,}".replace(",", "."), delta=f"{pct_com_demo:.1f}%")
    else:
        st.metric("📅 Com Demo", f"{leads_com_demo:,}".replace(",", "."), delta="0%")

with col3:
    leads_atencao_count = len(df_leads[
        (df_leads['data_demo'] < hoje) &
        (df_leads['data_noshow'].isna()) &
        (df_leads['data_venda'].isna()) &
        (~df_leads['status'].isin(STATUS_POS_DEMO))
    ])
    st.metric("⚠️ Exigem Atenção", f"{leads_atencao_count:,}".replace(",", "."), 
              delta=None if leads_atencao_count == 0 else "Ação necessária", delta_color="inverse")

with col4:
    leads_convertidos = len(df_leads[df_leads['data_venda'].notna()])
    st.metric("✅ Convertidos", f"{leads_convertidos:,}".replace(",", "."))

with col5:
    if total_leads > 0:
        taxa_conversao = (leads_convertidos / total_leads) * 100
        st.metric("📈 Taxa Conversão", f"{taxa_conversao:.1f}%")
    else:
        st.metric("📈 Taxa Conversão", "0%")

st.markdown("---")

# ========================================
# ABAS PRINCIPAIS
# ========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚨 Leads com Atenção", 
    "📆 Demos de Hoje",
    "📅 Resumo Diário",
    "🔍 Detalhes dos Leads",
    "⏱️ Tempo por Etapa",
    "📞 Produtividade do Vendedor"
])

# ========================================
# ABA 1: LEADS QUE EXIGEM ATENÇÃO
# ========================================
with tab1:
    st.markdown("### 🚨 Leads que Exigem Atenção")
    st.caption("Leads com demo vencida que não foram atualizados corretamente")
    
    leads_atencao = df_leads[
        (df_leads['data_demo'] < hoje) &  # Demo já passou
        (df_leads['data_noshow'].isna()) &  # Não marcado como no-show
        (df_leads['data_venda'].isna()) &  # Não marcado como venda
        (~df_leads['status'].isin(STATUS_POS_DEMO))  # Status não indica demo realizada
    ].copy()

    if not leads_atencao.empty:
        # Ordenar por data_demo (mais antiga primeiro)
        leads_atencao = leads_atencao.sort_values('data_demo')
        
        # Preparar DataFrame para exibição
        df_atencao_display = leads_atencao[[
            'id', 'lead_name', 'vendedor', 'status', 'data_demo'
        ]].copy()
        
        df_atencao_display.columns = ['ID', 'Lead', 'Vendedor', 'Status Atual', 'Data da Demo']
        
        # Formatar data
        df_atencao_display['Data da Demo'] = df_atencao_display['Data da Demo'].dt.strftime('%d/%m/%Y')
        
        # Adicionar link
        df_atencao_display['Link'] = df_atencao_display['ID'].apply(generate_kommo_link)
        
        # Exibir contagem
        st.error(f"⚠️ **{len(leads_atencao)} leads** precisam de atenção imediata!")
        
        st.markdown("")
        
        # Exibir tabela com links clicáveis
        st.dataframe(
            df_atencao_display[['Lead', 'Vendedor', 'Status Atual', 'Data da Demo', 'Link']],
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link Kommo",
                    display_text="Abrir"
                )
            },
            hide_index=True,
            width='stretch',
            height=min(450, len(df_atencao_display) * 35 + 100)
        )
    else:
        st.success("✅ Não há leads que exigem atenção no momento!")

# ========================================
# PREPARAR DADOS PARA RESUMO DIÁRIO
# ========================================

# Buscar todos os leads independente de data de criação para o resumo diário
@st.cache_data(ttl=1800)
def get_all_leads_for_summary(data_inicio: datetime, data_fim: datetime, vendedores: list = None):
    """Busca todos os leads para o resumo diário (sem filtro de criado_em)"""
    try:
        query = supabase.table('kommo_leads_statistics').select('*')
        
        if vendedores and len(vendedores) > 0:
            query = query.in_('vendedor', vendedores)
        
        response = query.execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Converter colunas de data
            date_columns = ['criado_em', 'data_agendamento', 'data_demo', 'data_noshow', 'data_venda']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        return pd.DataFrame()

# Função para buscar tempo médio por etapa
@st.cache_data(ttl=1800)
def get_tempo_por_etapa():
    """Busca o tempo médio que leads ficam em cada etapa"""
    try:
        # Executar query SQL para obter tempo médio por status
        response = supabase.rpc('get_tempo_por_etapa').execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        # Se a função RPC não existir, retornar DataFrame vazio
        return pd.DataFrame()

# Função para buscar dados de chamadas dos vendedores
@st.cache_data(ttl=1800)
def get_chamadas_vendedores(data_inicio, data_fim):
    """Busca dados de chamadas dos vendedores no período"""
    try:
        # Query para buscar chamadas com informações do vendedor
        response = supabase.rpc('get_chamadas_vendedores', {
            'data_inicio': data_inicio.isoformat(),
            'data_fim': data_fim.isoformat()
        }).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Converter duration de segundos para minutos
            if 'duration' in df.columns:
                df['duration_minutos'] = df['duration'] / 60
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        # Se a função RPC não existir, retornar DataFrame vazio
        return pd.DataFrame()

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
    
    # Reuniões Realizadas - lógica do BI
    # Filtra leads com data_demo no dia E:
    # 1) Status = "Desqualificados" AND data_demo preenchida AND data_noshow vazia
    # OU
    # 2) data_demo preenchida AND status IN ("5 - Demonstração realizada", "6 - Lead quente", "Venda ganha")
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
                    (df_all_leads['status'].isin(['5 - Demonstração realizada', '6 - Lead quente', 'Venda ganha']))
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
        'Dia': data.strftime('%A').lower(),
        'Novos Leads': novos_leads,
        'Agendamentos': agendamentos,
        'Demos no Dia': demos_dia,
        'Noshow': noshow,
        'Demos Realizadas': demos_realizadas,
        'Porcentagem Demos': porcentagem_demos,
        '% Noshow': porcentagem_noshow,
    })

df_resumo = pd.DataFrame(resumo_daily)

# Traduzir dias da semana
dias_pt = {
    'monday': 'segunda-feira',
    'tuesday': 'terça-feira',
    'wednesday': 'quarta-feira',
    'thursday': 'quinta-feira',
    'friday': 'sexta-feira',
    'saturday': 'sábado',
    'sunday': 'domingo'
}
df_resumo['Dia'] = df_resumo['Dia'].map(dias_pt)

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
# ABA 2: DEMONSTRAÇÕES DE HOJE
# ========================================
with tab2:
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
            'id', 'lead_name', 'vendedor', 'status', 'data_demo'
        ]].copy()
        
        df_demos_hoje.columns = ['ID', 'Lead', 'Vendedor', 'Status', 'Horário da Demo']
        
        # Formatar horário (se tiver hora, senão mostrar só a data)
        df_demos_hoje['Horário da Demo'] = df_demos_hoje['Horário da Demo'].dt.strftime('%d/%m/%Y %H:%M')
        
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
# ABA 3: RESUMO DIÁRIO
# ========================================
with tab3:
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
                    
                    # Reuniões Realizadas
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
                                    (df_vendedor['status'].isin(['5 - Demonstração realizada', '6 - Lead quente', 'Venda ganha']))
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
                            'Dia': dias_pt.get(data.strftime('%A').lower(), data.strftime('%A')),
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
# ABA 4: DETALHES DOS LEADS
# ========================================
with tab4:
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
# ABA 5: TEMPO POR ETAPA
# ========================================
with tab5:
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
# ABA 6: PRODUTIVIDADE DO VENDEDOR
# ========================================
with tab6:
    st.markdown("### 📞 Produtividade do Vendedor")
    st.caption("Análise de chamadas e desempenho dos vendedores")
    
    # Buscar dados de chamadas
    df_chamadas = get_chamadas_vendedores(
        datetime.combine(data_inicio, datetime.min.time()),
        datetime.combine(data_fim, datetime.max.time())
    )
    
    if not df_chamadas.empty:
        # Filtrar por vendedores selecionados se houver
        if vendedores_selecionados:
            df_chamadas = df_chamadas[df_chamadas['name'].isin(vendedores_selecionados)]
        
        if not df_chamadas.empty:
            # ========================================
            # SEÇÃO 1: MÉTRICAS GERAIS
            # ========================================
            st.markdown("#### 📊 Métricas Gerais")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                total_chamadas = len(df_chamadas)
                st.metric("☎️ Total de Chamadas", f"{total_chamadas:,}".replace(",", "."))
            
            with col_m2:
                if 'duration_minutos' in df_chamadas.columns:
                    tmd = df_chamadas['duration_minutos'].mean()
                    st.metric("⏱️ TMD (Tempo Médio)", f"{tmd:.1f} min")
                else:
                    st.metric("⏱️ TMD (Tempo Médio)", "N/A")
            
            with col_m3:
                duracao_total = df_chamadas['duration'].sum() / 60  # em minutos
                horas_totais = duracao_total / 60  # em horas
                if horas_totais < 1:
                    st.metric("⏳ Duração Total", f"{duracao_total:.0f} min")
                else:
                    st.metric("⏳ Duração Total", f"{horas_totais:.1f}h")
            
            with col_m4:
                vendedores_unicos = df_chamadas['name'].nunique() if 'name' in df_chamadas.columns else 0
                st.metric("👥 Vendedores", f"{vendedores_unicos}")
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 2: CHAMADAS POR VENDEDOR
            # ========================================
            st.markdown("#### 👥 Chamadas por Vendedor")
            
            if 'name' in df_chamadas.columns:
                df_vendedores = df_chamadas.groupby('name').agg({
                    'id': 'count',
                    'duration_minutos': ['mean', 'sum']
                }).reset_index()
                
                df_vendedores.columns = ['Vendedor', 'Total de Chamadas', 'TMD (minutos)', 'Duração Total (minutos)']
                df_vendedores['TMD (minutos)'] = df_vendedores['TMD (minutos)'].round(2)
                df_vendedores['Duração Total (minutos)'] = df_vendedores['Duração Total (minutos)'].round(0)
                df_vendedores = df_vendedores.sort_values('Total de Chamadas', ascending=False)
                
                # Gráfico de barras - Total de Chamadas
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    fig_vendedores = px.bar(
                        df_vendedores,
                        x='Vendedor',
                        y='Total de Chamadas',
                        title='Total de Chamadas por Vendedor',
                        labels={'Vendedor': 'Vendedor', 'Total de Chamadas': 'Quantidade'},
                        color='Total de Chamadas',
                        color_continuous_scale='Viridis'
                    )
                    fig_vendedores.update_layout(height=400, xaxis_tickangle=-45)
                    st.plotly_chart(fig_vendedores, use_container_width=True)
                
                with col_chart2:
                    # Gráfico de ligações por dia
                    if 'atendido_em' in df_chamadas.columns:
                        df_chamadas_copy = df_chamadas.copy()
                        df_chamadas_copy['atendido_em'] = pd.to_datetime(df_chamadas_copy['atendido_em'])
                        df_chamadas_copy['data'] = df_chamadas_copy['atendido_em'].dt.date
                        
                        df_por_dia = df_chamadas_copy.groupby(['name', 'data']).size().reset_index(name='chamadas')
                        df_por_dia.columns = ['Vendedor', 'Data', 'Chamadas']
                        df_por_dia['Data'] = pd.to_datetime(df_por_dia['Data']).dt.strftime('%d/%m')
                        
                        fig_por_dia = px.line(
                            df_por_dia,
                            x='Data',
                            y='Chamadas',
                            color='Vendedor',
                            title='Ligações por Dia (Comparação)',
                            labels={'Data': 'Data', 'Chamadas': 'Quantidade'},
                            markers=True
                        )
                        fig_por_dia.update_layout(height=400, hovermode='x unified')
                        st.plotly_chart(fig_por_dia, use_container_width=True)
                
                # Tabela de vendedores
                st.dataframe(
                    df_vendedores,
                    column_config={
                        "Vendedor": st.column_config.TextColumn("Vendedor"),
                        "Total de Chamadas": st.column_config.NumberColumn("Chamadas", format="%d"),
                        "TMD (minutos)": st.column_config.NumberColumn("TMD (min)", format="%.2f"),
                        "Duração Total (minutos)": st.column_config.NumberColumn("Total (min)", format="%.0f")
                    },
                    hide_index=True,
                    width='stretch',
                    height=min(300, len(df_vendedores) * 35 + 100)
                )
            
            st.markdown("")
            
            # ========================================
            # SEÇÃO 3: RELATÓRIO DETALHADO DE CHAMADAS
            # ========================================
            st.markdown("#### 📋 Relatório Detalhado de Chamadas")
            
            # Preparar dados para tabela
            df_relatorio = df_chamadas.copy()
            
            # Renomear e formatar colunas
            if 'name' in df_relatorio.columns:
                df_relatorio = df_relatorio.rename(columns={
                    'name': 'Vendedor',
                    'atendente': 'Atendente',
                    'atendido_em': 'Atendido em',
                    'finalizado_em': 'Finalizado em',
                    'duration_minutos': 'Duração (min)',
                    'causa_desligamento': 'Motivo',
                    'ramal': 'Ramal',
                    'url_gravacao': 'Gravação'
                })
            
            # Converter timestamps
            if 'Atendido em' in df_relatorio.columns:
                df_relatorio['Atendido em'] = pd.to_datetime(df_relatorio['Atendido em'])
                df_relatorio['Atendido em'] = df_relatorio['Atendido em'].dt.strftime('%d/%m/%Y %H:%M')
            
            if 'Finalizado em' in df_relatorio.columns:
                df_relatorio['Finalizado em'] = pd.to_datetime(df_relatorio['Finalizado em'])
                df_relatorio['Finalizado em'] = df_relatorio['Finalizado em'].dt.strftime('%d/%m/%Y %H:%M')
            
            # Selecionar colunas para exibição
            colunas_exibicao = [col for col in ['Vendedor', 'Atendente', 'Ramal', 'Atendido em', 'Duração (min)', 'Motivo', 'Gravação'] 
                               if col in df_relatorio.columns]
            df_relatorio_exibicao = df_relatorio[colunas_exibicao].copy()
            
            # Formatar coluna de duração
            if 'Duração (min)' in df_relatorio_exibicao.columns:
                df_relatorio_exibicao['Duração (min)'] = df_relatorio_exibicao['Duração (min)'].round(1)
            
            # Criar coluna com link da gravação
            column_config_dict = {}
            for col in df_relatorio_exibicao.columns:
                if col == 'Gravação':
                    column_config_dict[col] = st.column_config.LinkColumn("🔊 Gravação")
                elif col == 'Duração (min)':
                    column_config_dict[col] = st.column_config.NumberColumn("Duração (min)", format="%.1f")
                elif col in ['Atendido em', 'Finalizado em']:
                    column_config_dict[col] = st.column_config.TextColumn(col)
                else:
                    column_config_dict[col] = st.column_config.TextColumn(col)
            
            st.dataframe(
                df_relatorio_exibicao.sort_values('Atendido em', ascending=False),
                column_config=column_config_dict,
                hide_index=True,
                width='stretch',
                height=min(600, len(df_relatorio_exibicao) * 35 + 100)
            )
            
            st.markdown("")
        else:
            st.info("Nenhuma chamada encontrada para os vendedores selecionados no período.")
    else:
        st.info("⚠️ Dados de chamadas não disponíveis. Certifique-se de que a função RPC 'get_chamadas_vendedores' está configurada no banco de dados.")

# Footer
st.markdown("---")
st.caption("💡 **Dica**: Use os filtros na barra lateral para ajustar o período e vendedores.")
st.caption("🔄 Os dados são atualizados automaticamente a cada 30 minutos.")
