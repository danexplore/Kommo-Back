"""
Estilos CSS centralizados do Dashboard Kommo
"""

def get_main_css() -> str:
    """Retorna o CSS principal do dashboard"""
    return """
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
        color: #48D1CC;
        font-size: 1.8rem;
    }
    
    h3 {
        font-weight: 600;
        color: #5F9EA0;
        font-size: 1.4rem;
    }
    
    h4 {
        font-weight: 500;
        color: #7FFFD4;
        font-size: 1.1rem;
    }
    
    /* Cards métricas - estilo moderno */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #CBD5E0;
        font-weight: 500;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
    }
    
    /* Sidebar - ecosys AUTO */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #2d3748 50%, #1a1f2e 100%);
        border-right: 1px solid rgba(32, 178, 170, 0.2);
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #20B2AA;
        text-shadow: none;
    }
    
    /* Tabs - estilo ecosys */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(26, 31, 46, 0.6);
        border-radius: 12px;
        padding: 4px;
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #CBD5E0;
        font-weight: 500;
        border-radius: 8px;
        padding: 10px 16px;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(32, 178, 170, 0.15);
        color: #ffffff;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #20B2AA 0%, #008B8B 100%);
        color: #ffffff !important;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(32, 178, 170, 0.3);
    }
    
    /* DataFrames/Tabelas */
    [data-testid="stDataFrame"] {
        background-color: rgba(26, 31, 46, 0.6);
        border-radius: 12px;
        border: 1px solid rgba(32, 178, 170, 0.15);
    }
    
    /* Botões - destaque teal */
    .stButton > button {
        background: linear-gradient(135deg, #20B2AA 0%, #008B8B 100%);
        color: #ffffff;
        border: none;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(32, 178, 170, 0.25);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #48D1CC 0%, #20B2AA 100%);
        box-shadow: 0 6px 20px rgba(32, 178, 170, 0.4);
        transform: translateY(-2px);
    }
    
    /* Selectbox e Multiselect */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background-color: rgba(32, 178, 170, 0.08);
        border-color: rgba(32, 178, 170, 0.25);
        border-radius: 8px;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: rgba(32, 178, 170, 0.1);
        border-radius: 10px;
        color: #CBD5E0;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: rgba(32, 178, 170, 0.2);
        color: #ffffff;
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
    }
    
    div[data-baseweb="notification"] {
        background-color: rgba(32, 178, 170, 0.15);
        border-left: 4px solid #20B2AA;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #20B2AA 0%, #48D1CC 100%);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #20B2AA !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(32, 178, 170, 0.2);
    }
    
    /* Links */
    a {
        color: #48D1CC;
        text-decoration: none;
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
    """


def get_metric_card_html(title: str, value: str, subtitle: str = "", color: str = "#20B2AA") -> str:
    """Gera HTML para um card de métrica customizado"""
    return f"""
    <div class="metric-card">
        <h4 style="margin-top: 0; color: {color};">{title}</h4>
        <div style="font-size: 2rem; font-weight: 800; color: #ffffff; margin: 10px 0;">{value}</div>
        {f'<p style="color: #CBD5E0; margin-bottom: 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """


def get_insight_card_html(title: str, content: str, icon: str = "💡", color: str = "#20B2AA") -> str:
    """Gera HTML para um card de insight"""
    return f"""
    <div class="metric-card">
        <h4 style="margin-top: 0; color: {color};">{icon} {title}</h4>
        {content}
    </div>
    """
