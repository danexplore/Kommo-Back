"""
Serviço de conexão com Supabase

Implementa conexão, queries e cache com:
- Logging estruturado
- Tratamento de erros consistente
- RPCs otimizadas para performance
- Cache em múltiplas camadas
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, List
import hashlib

from supabase import create_client, Client

from config import CACHE_TTL_LEADS, CACHE_TTL_CHAMADAS, CACHE_TTL_TEMPO
from core.logging import get_logger, log_execution
from core.exceptions import (
    handle_error, 
    ConnectionError, 
    DataError, 
    ErrorCode,
    ErrorContext
)


# Logger do módulo
logger = get_logger("supabase_service")

# Colunas de data para conversão
DATE_COLUMNS = ['criado_em', 'data_demo', 'data_noshow', 'data_agendamento', 'data_venda']


# ========================================
# CONEXÃO
# ========================================

@st.cache_resource
def init_supabase() -> Client:
    """
    Inicializa conexão com Supabase.
    
    Returns:
        Cliente Supabase configurado
    
    Raises:
        ConnectionError: Se credenciais não configuradas
    """
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    
    if not url or not key:
        logger.critical("Credenciais do Supabase não configuradas")
        st.error("⚠️ Credenciais do Supabase não configuradas. Configure SUPABASE_URL e SUPABASE_KEY.")
        st.stop()
    
    try:
        client = create_client(url, key)
        logger.info("Conexão com Supabase estabelecida")
        return client
    except Exception as e:
        logger.critical("Falha ao conectar com Supabase", exception=e)
        raise ConnectionError(
            message="Não foi possível conectar ao Supabase",
            service="supabase",
            original_exception=e
        )


# Cliente global
_supabase: Optional[Client] = None


def get_supabase() -> Client:
    """Retorna instância do cliente Supabase"""
    global _supabase
    if _supabase is None:
        _supabase = init_supabase()
    return _supabase


# ========================================
# CACHE HELPERS
# ========================================

def _generate_cache_key(*args) -> str:
    """Gera uma chave de cache baseada nos argumentos"""
    key_str = "_".join(str(arg) for arg in args)
    return hashlib.md5(key_str.encode()).hexdigest()[:16]


# ========================================
# PROCESSAMENTO DE DADOS
# ========================================

def _convert_and_precompute_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas de data para datetime e pré-computa versões .date().
    
    Args:
        df: DataFrame com dados brutos
    
    Returns:
        DataFrame com colunas datetime e date pré-computadas
    """
    if df.empty:
        return df
    
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            # Pré-computar .date() para evitar chamadas repetidas
            df[f'{col}_date'] = df[col].dt.date
    
    return df


# ========================================
# RPC: BUSCA DE LEADS OTIMIZADA
# ========================================

def _fetch_leads_via_rpc(
    supabase: Client,
    data_inicio_iso: str,
    data_fim_iso: str,
    rpc_name: str = 'get_leads_by_period'
) -> pd.DataFrame:
    """
    Busca leads usando RPC otimizada.
    
    Args:
        supabase: Cliente Supabase
        data_inicio_iso: Data início em ISO format
        data_fim_iso: Data fim em ISO format
        rpc_name: Nome da RPC a usar
    
    Returns:
        DataFrame com leads
    """
    try:
        response = supabase.rpc(rpc_name, {
            'p_data_inicio': data_inicio_iso,
            'p_data_fim': data_fim_iso
        }).execute()
        
        if response.data:
            logger.info(f"RPC {rpc_name} executada com sucesso", records=len(response.data))
            return pd.DataFrame(response.data)
        
        return pd.DataFrame()
        
    except Exception as e:
        logger.warning(f"RPC {rpc_name} falhou, usando fallback", exception=str(e))
        return pd.DataFrame()


def _fetch_leads_fallback(
    supabase: Client,
    data_inicio_iso: str,
    data_fim_iso: str
) -> pd.DataFrame:
    """
    Fallback: busca leads usando queries múltiplas quando RPC não está disponível.
    
    Args:
        supabase: Cliente Supabase
        data_inicio_iso: Data início em ISO format
        data_fim_iso: Data fim em ISO format
    
    Returns:
        DataFrame com leads únicos
    """
    all_data = []
    
    for col in DATE_COLUMNS:
        try:
            response = supabase.table('kommo_leads_statistics').select('*').gte(col, data_inicio_iso).lte(col, data_fim_iso).execute()
            if response.data:
                all_data.extend(response.data)
                logger.debug(f"Query {col} retornou dados", records=len(response.data))
        except Exception as e:
            logger.warning(f"Falha na query por {col}", exception=e)
            continue
    
    if not all_data:
        return pd.DataFrame()
    
    # Deduplicação via pandas
    df = pd.DataFrame(all_data)
    df = df.drop_duplicates(subset=['id'], keep='first')
    logger.debug("Duplicatas removidas via pandas", unique=len(df))
    
    return df


def _fetch_leads_optimized(
    supabase: Client,
    data_inicio_iso: str,
    data_fim_iso: str,
    use_criado_em_only: bool = False
) -> pd.DataFrame:
    """
    Busca leads usando a melhor estratégia disponível.
    
    Args:
        supabase: Cliente Supabase
        data_inicio_iso: Data início em ISO format
        data_fim_iso: Data fim em ISO format
        use_criado_em_only: Se True, usa RPC que filtra apenas por criado_em
    
    Returns:
        DataFrame com leads
    """
    # Determinar qual RPC usar
    rpc_name = 'get_leads_by_criado_em' if use_criado_em_only else 'get_leads_by_period'
    
    # Tentar RPC primeiro
    df = _fetch_leads_via_rpc(supabase, data_inicio_iso, data_fim_iso, rpc_name)
    
    if not df.empty:
        return df
    
    # Se use_criado_em_only e RPC falhou, fazer query direta simples
    if use_criado_em_only:
        try:
            response = supabase.table('kommo_leads_statistics').select('*').gte('criado_em', data_inicio_iso).lte('criado_em', data_fim_iso).execute()
            if response.data:
                logger.info("Query direta por criado_em executada", records=len(response.data))
                return pd.DataFrame(response.data)
        except Exception as e:
            logger.warning("Query direta por criado_em falhou", exception=e)
    
    # Fallback para queries múltiplas
    return _fetch_leads_fallback(supabase, data_inicio_iso, data_fim_iso)


# ========================================
# FUNÇÕES PÚBLICAS DE LEADS
# ========================================

@st.cache_data(ttl=CACHE_TTL_LEADS, show_spinner=False)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=True)
def get_leads_data(
    data_inicio: datetime, 
    data_fim: datetime, 
    vendedores: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Busca dados de leads da view kommo_leads_statistics.
    Usa RPC otimizada get_leads_by_period.
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
        vendedores: Lista de vendedores para filtrar (opcional)
    
    Returns:
        DataFrame com os leads do período
    """
    supabase = get_supabase()
    
    data_inicio_iso = data_inicio.isoformat()
    data_fim_iso = data_fim.isoformat()
    
    # Buscar dados com RPC otimizada
    df = _fetch_leads_optimized(supabase, data_inicio_iso, data_fim_iso)
    
    if df.empty:
        logger.info("Nenhum lead encontrado no período")
        return pd.DataFrame()
    
    # Aplicar filtro de vendedor
    if vendedores and len(vendedores) > 0:
        df = df[df['vendedor'].isin(vendedores)]
        logger.debug("Filtro de vendedor aplicado", vendedores=len(vendedores), records=len(df))
    
    # Converter e pré-computar datas
    df = _convert_and_precompute_dates(df)
    
    logger.info("Leads carregados com sucesso", records=len(df))
    return df


@st.cache_data(ttl=CACHE_TTL_LEADS, show_spinner=False)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=True)
def get_leads_by_criado_em(
    data_inicio: datetime, 
    data_fim: datetime, 
    vendedores: Optional[List[str]] = None,
    pipelines: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Busca leads filtrados APENAS por criado_em (data de criação).
    Ideal para gráficos de tendência e análises de volume.
    Usa RPC otimizada get_leads_by_criado_em.
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
        vendedores: Lista de vendedores para filtrar (opcional)
        pipelines: Lista de pipelines para filtrar (opcional)
    
    Returns:
        DataFrame com os leads criados no período
    """
    supabase = get_supabase()
    
    data_inicio_iso = data_inicio.isoformat()
    data_fim_iso = data_fim.isoformat()
    
    logger.info(
        "Buscando leads por criado_em",
        data_inicio=data_inicio_iso,
        data_fim=data_fim_iso
    )
    
    # Buscar dados com RPC específica para criado_em
    df = _fetch_leads_optimized(supabase, data_inicio_iso, data_fim_iso, use_criado_em_only=True)
    
    if df.empty:
        logger.info(
            "Nenhum lead criado no período",
            data_inicio=data_inicio_iso,
            data_fim=data_fim_iso
        )
        return pd.DataFrame()
    
    # Aplicar filtros
    if vendedores and len(vendedores) > 0:
        df = df[df['vendedor'].isin(vendedores)]
    
    if pipelines and len(pipelines) > 0:
        df = df[df['pipeline'].isin(pipelines)]
    
    # Converter e pré-computar datas
    df = _convert_and_precompute_dates(df)
    
    logger.info("Leads por criado_em carregados", records=len(df))
    return df


@st.cache_data(ttl=CACHE_TTL_LEADS, show_spinner=False)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=True)
def get_all_leads_for_summary(
    data_inicio: datetime, 
    data_fim: datetime, 
    vendedores: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Busca todos os leads para o resumo diário.
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
        vendedores: Lista de vendedores para filtrar (opcional)
    
    Returns:
        DataFrame com os leads para resumo
    """
    return get_leads_data(data_inicio, data_fim, vendedores)


# ========================================
# QUERIES DE TEMPO E CHAMADAS
# ========================================

@st.cache_data(ttl=CACHE_TTL_TEMPO)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=False)
def get_tempo_por_etapa() -> pd.DataFrame:
    """
    Busca o tempo médio que leads ficam em cada etapa.
    
    Returns:
        DataFrame com tempo médio por etapa
    """
    supabase = get_supabase()
    
    response = supabase.rpc('get_tempo_por_etapa').execute()
    
    if response.data:
        logger.info("Tempo por etapa carregado", records=len(response.data))
        return pd.DataFrame(response.data)
    
    logger.info("Nenhum dado de tempo por etapa")
    return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL_CHAMADAS)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=False)
def get_chamadas_vendedores(data_inicio: datetime, data_fim: datetime) -> pd.DataFrame:
    """
    Busca dados de chamadas dos vendedores no período com paginação.
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
    
    Returns:
        DataFrame com as chamadas
    """
    supabase = get_supabase()
    
    all_data = []
    page_size = 1000
    offset = 0
    
    while True:
        response = supabase.rpc('get_chamadas_vendedores', {
            'data_inicio': data_inicio.isoformat(),
            'data_fim': data_fim.isoformat()
        }).range(offset, offset + page_size - 1).execute()
        
        if response.data:
            all_data.extend(response.data)
            logger.debug("Página de chamadas carregada", offset=offset, records=len(response.data))
            if len(response.data) < page_size:
                break
            offset += page_size
        else:
            break
    
    if all_data:
        df = pd.DataFrame(all_data)
        if 'duration' in df.columns:
            df['duration_minutos'] = df['duration'].apply(lambda x: round(x / 60, 2) if x > 0 else 0)
        logger.info("Chamadas carregadas", records=len(df))
        return df
    
    logger.info("Nenhuma chamada encontrada no período")
    return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL_LEADS)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=False)
def get_hour_noshow_analitycs(data_inicio: datetime, data_fim: datetime) -> pd.DataFrame:
    """
    Busca análises de no-shows por hora do dia.
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
    Returns:
        DataFrame com análises de no-shows por hora
    """
    supabase = get_supabase()
    
    response = supabase.rpc('calcular_taxa_noshow_por_hora', {
        'data_inicio': data_inicio.isoformat(),
        'data_fim': data_fim.isoformat()
    }).execute()
    
    if response.data:
        logger.info("Análises de no-shows por hora carregadas", records=len(response.data))
        return pd.DataFrame(response.data)
    
    logger.info("Nenhum dado de no-shows por hora encontrado")
    return pd.DataFrame()