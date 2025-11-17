import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from supabase import create_client, Client
import plotly.express as px
from openai import OpenAI

# Configuração da página
st.set_page_config(
    page_title="Painel de Acompanhamento de Leads - ecosys AUTO",
    page_icon="🚗",
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

# Configuração do OpenAI
@st.cache_resource
def init_openai():
    """Inicializa cliente OpenAI"""
    api_key = st.secrets["OPENAI_API_KEY"]
    
    if not api_key:
        return None
    
    return OpenAI(api_key=api_key)

openai_client = init_openai()

# CSS customizado - ecosys AUTO Branding
st.markdown("""
    <style>
    /* Background geral - tons escuros com cinza */
    .stApp {
        background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
    }
    
    /* Main */
    .main {
        padding: 2rem 1.5rem;
        background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
    }
    
    /* Texto base */
    body {
        color: #ffffff;
    }
    
    /* Títulos - Teal ecosys AUTO */
    h1 {
        font-weight: 800;
        color: #20B2AA;
        text-shadow: 0 2px 10px rgba(32, 178, 170, 0.3);
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        font-weight: 700;
        color: #20B2AA;
        font-size: 1.8rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        font-weight: 600;
        color: #20B2AA;
        font-size: 1.3rem;
    }
    
    /* Dividers */
    hr, .stDivider {
        border-color: rgba(32, 178, 170, 0.2);
    }
    
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
    
    /* Alertas */
    .stAlert {
        background: linear-gradient(135deg, rgba(45, 55, 72, 0.9) 0%, rgba(26, 31, 46, 0.9) 100%);
        border-radius: 12px;
        border: 1px solid rgba(32, 178, 170, 0.3);
        color: #ffffff;
    }
    
    .stAlert-info {
        border-left: 4px solid #20B2AA;
    }
    
    .stAlert-warning {
        border-left: 4px solid #ff8c00;
    }
    
    .stAlert-error {
        border-left: 4px solid #ff4444;
    }
    
    .stAlert-success {
        border-left: 4px solid #48bb78;
    }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid rgba(32, 178, 170, 0.15);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        padding: 0 28px;
        background-color: rgba(45, 55, 72, 0.6);
        border-radius: 12px 12px 0 0;
        font-weight: 600;
        color: #CBD5E0;
        border: 1px solid rgba(32, 178, 170, 0.15);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(32, 178, 170, 0.2) 0%, rgba(0, 139, 139, 0.1) 100%);
        color: #20B2AA;
        border: 2px solid #20B2AA;
        border-bottom: none;
        box-shadow: 0 -4px 12px rgba(32, 178, 170, 0.2);
    }
    
    .stTabs [aria-selected="false"]:hover {
        background-color: rgba(32, 178, 170, 0.12);
        color: #ffffff;
    }
    
    /* Sidebar - ecosys AUTO */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
    }
    
    section[data-testid="stSidebar"] * {
        color: #ffffff;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #20B2AA;
    }
    
    section[data-testid="stSidebar"] label {
        color: #CBD5E0;
        font-weight: 500;
    }
    
    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stMultiSelect > div > div {
        background-color: rgba(32, 178, 170, 0.08);
        border-color: rgba(32, 178, 170, 0.25);
        border-radius: 8px;
    }
    
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] select {
        background-color: rgba(32, 178, 170, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(32, 178, 170, 0.25) !important;
        border-radius: 8px !important;
    }
    
    section[data-testid="stSidebar"] button {
        background: linear-gradient(135deg, #20B2AA 0%, #008B8B 100%);
        color: #ffffff;
        border: none;
        font-weight: 600;
        border-radius: 8px;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background: linear-gradient(135deg, #48D1CC 0%, #20B2AA 100%);
        box-shadow: 0 4px 12px rgba(32, 178, 170, 0.3);
    }
    
    section[data-testid="stSidebar"] .stInfo, 
    section[data-testid="stSidebar"] .stWarning,
    section[data-testid="stSidebar"] .stError {
        background-color: rgba(32, 178, 170, 0.1);
        border-color: rgba(32, 178, 170, 0.3);
    }
    
    /* Links */
    a {
        color: #20B2AA;
        text-decoration: none;
        font-weight: 600;
    }
    
    a:hover {
        color: #48D1CC;
        text-decoration: underline;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        background-color: rgba(32, 178, 170, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(32, 178, 170, 0.25) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stNumberInput > div > div > input::placeholder {
        color: rgba(203, 213, 224, 0.6) !important;
    }
    
    /* Checkbox */
    .stCheckbox > label {
        color: #CBD5E0;
    }
    
    /* Caption */
    .caption {
        color: #CBD5E0;
    }
    
    /* Gradiente de destaque para cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(32, 178, 170, 0.15) 0%, rgba(0, 139, 139, 0.08) 100%);
        border-left: 4px solid #20B2AA;
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
        
        # Filtro de data - buscar leads que tenham qualquer evento (criação, demo, noshow, agendamento, venda) no período
        # Usar múltiplas queries e combinar resultados
        data_inicio_iso = data_inicio.isoformat()
        data_fim_iso = data_fim.isoformat()
        
        # Buscar leads por cada coluna de data
        all_data = []
        
        try:
            # Query 1: criado_em
            q1 = supabase.table('kommo_leads_statistics').select('*').gte('criado_em', data_inicio_iso).lte('criado_em', data_fim_iso).execute()
            if q1.data:
                all_data.extend(q1.data)
        except:
            pass
        
        try:
            # Query 2: data_demo
            q2 = supabase.table('kommo_leads_statistics').select('*').gte('data_demo', data_inicio_iso).lte('data_demo', data_fim_iso).execute()
            if q2.data:
                all_data.extend(q2.data)
        except:
            pass
        
        try:
            # Query 3: data_noshow
            q3 = supabase.table('kommo_leads_statistics').select('*').gte('data_noshow', data_inicio_iso).lte('data_noshow', data_fim_iso).execute()
            if q3.data:
                all_data.extend(q3.data)
        except:
            pass
        
        try:
            # Query 4: data_agendamento
            q4 = supabase.table('kommo_leads_statistics').select('*').gte('data_agendamento', data_inicio_iso).lte('data_agendamento', data_fim_iso).execute()
            if q4.data:
                all_data.extend(q4.data)
        except:
            pass
        
        try:
            # Query 5: data_venda
            q5 = supabase.table('kommo_leads_statistics').select('*').gte('data_venda', data_inicio_iso).lte('data_venda', data_fim_iso).execute()
            if q5.data:
                all_data.extend(q5.data)
        except:
            pass
        
        # Remover duplicatas usando ID
        if all_data:
            seen_ids = set()
            unique_data = []
            for item in all_data:
                if item.get('id') not in seen_ids:
                    seen_ids.add(item.get('id'))
                    unique_data.append(item)
            all_data = unique_data
        
        # Se há filtro de vendedor, aplicar aqui
        if vendedores and len(vendedores) > 0:
            all_data = [item for item in all_data if item.get('vendedor') in vendedores]
        
        if all_data:
            df = pd.DataFrame(all_data)
            
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

@st.cache_data(ttl=3600)  # Cache de 1 hora
def gerar_insights_ia(metricas_atual, metricas_anterior, periodo_descricao):
    """Gera insights usando IA da OpenAI"""
    
    if not openai_client:
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

        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Você é um analista de vendas experiente. Forneça insights diretos e acionáveis."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ **Erro ao gerar insights:** {str(e)}"

def chat_com_dados(mensagem_usuario, metricas_atual, metricas_anterior, periodo_descricao, historico_chat):
    """Realiza conversa com IA sobre os dados"""
    
    if not openai_client:
        return "Erro: OpenAI não configurada"
    
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
        
        # Construir mensagens do histórico
        mensagens = [
            {"role": "system", "content": f"""Você é um assistente especializado em análise de vendas e CRM. 
Você tem acesso aos dados atuais de performance de leads e pode responder perguntas sobre tendências, 
recomendações e análises dos dados.

{contexto_dados}

Responda em português do Brasil, de forma conversacional e profissional."""}
        ]
        
        # Adicionar histórico de chat
        for msg_hist in historico_chat:
            mensagens.append({"role": msg_hist["role"], "content": msg_hist["content"]})
        
        # Adicionar mensagem atual do usuário
        mensagens.append({"role": "user", "content": mensagem_usuario})
        
        # Chamar API
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=mensagens
        )
        
        return response.choices[0].message.content
        
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
    # Período atual - Reuniões Realizadas com lógica correta
    demos_realizadas = len(df_leads[
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
                (df_leads['status'].isin(['5 - Demonstração realizada', '6 - Lead quente', 'Venda ganha']))
            )
        )
    ])
    
    # Período anterior - Demos Realizadas
    demos_realizadas_anterior = len(df_leads_anterior[
        (df_leads_anterior['data_demo'].notna()) &
        (df_leads_anterior['data_demo'] >= pd.Timestamp(datetime.combine(data_inicio_anterior, datetime.min.time()))) &
        (df_leads_anterior['data_demo'] <= pd.Timestamp(datetime.combine(data_fim_anterior, datetime.max.time()))) &
        (
            (
                (df_leads_anterior['status'] == 'Desqualificados') &
                (df_leads_anterior['data_demo'].notna()) &
                (df_leads_anterior['data_noshow'].isna())
            ) |
            (
                (df_leads_anterior['data_demo'].notna()) &
                (df_leads_anterior['status'].isin(['5 - Demonstração realizada', '6 - Lead quente', 'Venda ganha']))
            )
        )
    ]) if not df_leads_anterior.empty else 0
    
    # Calcular diferença demos realizadas
    if demos_realizadas_anterior > 0:
        diferenca_demos_real = demos_realizadas - demos_realizadas_anterior
        pct_diferenca_demos = ((demos_realizadas - demos_realizadas_anterior) / demos_realizadas_anterior) * 100
        delta_text_demos = f"{diferenca_demos_real:+d} ({pct_diferenca_demos:+.1f}%)"
        st.metric("🎯 Demos Realizadas", f"{demos_realizadas:,}".replace(",", "."), delta=delta_text_demos)
    else:
        st.metric("🎯 Demos Realizadas", f"{demos_realizadas:,}".replace(",", "."), delta="Sem comparação")
    
    # Calcular taxa de noshow período atual
    noshow_count = len(df_leads[
        (df_leads['data_noshow'].notna()) &
        (df_leads['data_noshow'] >= pd.Timestamp(datetime.combine(data_inicio, datetime.min.time()))) &
        (df_leads['data_noshow'] <= pd.Timestamp(datetime.combine(data_fim, datetime.max.time())))
    ])
    
    # Calcular taxa de noshow período anterior
    noshow_count_anterior = len(df_leads_anterior[
        (df_leads_anterior['data_noshow'].notna()) &
        (df_leads_anterior['data_noshow'] >= pd.Timestamp(datetime.combine(data_inicio_anterior, datetime.min.time()))) &
        (df_leads_anterior['data_noshow'] <= pd.Timestamp(datetime.combine(data_fim_anterior, datetime.max.time())))
    ]) if not df_leads_anterior.empty else 0
    
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🚨 Leads com Atenção",
    "🤖 Insights IA",
    "📆 Demos de Hoje",
    "📅 Resumo Diário",
    "🔍 Detalhes dos Leads",
    "⏱️ Tempo por Etapa",
    "📞 Produtividade do Vendedor",
    "💰 Mural de Vendas"
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
    
    if openai_client:
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
            st.caption(f"🕐 Análise gerada em: {datetime.now().strftime('%d/%m/%Y às %H:%M')} | 🤖 Powered by OpenAI GPT-4o-mini")
            
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
        
        1. 🔑 Obtenha uma chave API da OpenAI em: https://platform.openai.com/api-keys
        2. 📝 Adicione a chave no arquivo `.streamlit/secrets.toml`:
           ```toml
           OPENAI_API_KEY = "sk-proj-xxxxx"
           ```
        3. 🔄 Reinicie a aplicação
        
        **Custo estimado:** ~$0.001 por análise (usando GPT-5-mini)
        """)

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
            df_vendas['tempo_venda'] = (df_vendas['data_venda'] - df_vendas['criado_em']).dt.total_seconds() / 86400
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

# Footer
st.markdown("---")
st.caption("💡 **Dica**: Use os filtros na barra lateral para ajustar o período e vendedores.")
st.caption("🔄 Os dados são atualizados automaticamente a cada 30 minutos.")
