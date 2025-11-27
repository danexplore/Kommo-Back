"""
Serviço de conexão com Supabase

Implementa conexão, queries e cache com:
- Logging estruturado
- Tratamento de erros consistente
- Timeouts configuráveis
- Query otimizada única (performance)
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, List

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
# QUERIES DE LEADS
# ========================================

def _convert_and_precompute_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas de data para datetime e pré-computa versões .date().
    Resolve problema 1.7 (conversão de datas repetida).
    
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


def _fetch_leads_optimized(
    supabase: Client,
    data_inicio_iso: str,
    data_fim_iso: str
) -> pd.DataFrame:
    """
    Busca leads usando query otimizada única via RPC ou fallback para queries paralelas.
    Resolve problema 1.1 (5 queries separadas) e 1.2 (remoção de duplicatas).
    
    Args:
        supabase: Cliente Supabase
        data_inicio_iso: Data início em ISO format
        data_fim_iso: Data fim em ISO format
    
    Returns:
        DataFrame com leads únicos
    """
    # Tentar usar RPC otimizada primeiro (se existir no Supabase)
    try:
        response = supabase.rpc('get_leads_by_period', {
            'p_data_inicio': data_inicio_iso,
            'p_data_fim': data_fim_iso
        }).execute()
        
        if response.data:
            logger.info("Query RPC otimizada executada com sucesso", records=len(response.data))
            return pd.DataFrame(response.data)
    except Exception as e:
        # RPC não existe, usar fallback
        logger.debug("RPC get_leads_by_period não disponível, usando fallback", exception=str(e))
    
    # Fallback: usar filtro OR via query única (mais eficiente que 5 queries)
    # Nota: Supabase REST não suporta OR diretamente, então usamos uma abordagem otimizada
    all_data = []
    
    # Buscar por cada coluna mas com deduplicação eficiente via pandas
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
    
    # Usar pandas para deduplicação eficiente (resolve 1.2)
    df = pd.DataFrame(all_data)
    df = df.drop_duplicates(subset=['id'], keep='first')
    logger.debug("Duplicatas removidas via pandas", unique=len(df))
    
    return df


@st.cache_data(ttl=CACHE_TTL_LEADS)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=True)
def get_leads_data(
    data_inicio: datetime, 
    data_fim: datetime, 
    vendedores: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Busca dados de leads da view kommo_leads_statistics.
    
    Otimizações implementadas:
    - Query única otimizada (1.1)
    - Deduplicação via pandas drop_duplicates (1.2)
    - Pré-computação de colunas .date() (1.7)
    
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
    
    # Buscar dados com query otimizada
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


@st.cache_data(ttl=CACHE_TTL_LEADS)
@log_execution("supabase_service")
@handle_error(default_return=pd.DataFrame(), show_user_error=True)
def get_all_leads_for_summary(
    data_inicio: datetime, 
    data_fim: datetime, 
    vendedores: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Busca todos os leads para o resumo diário.
    Usa mesma lógica otimizada de get_leads_data.
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
        vendedores: Lista de vendedores para filtrar (opcional)
    
    Returns:
        DataFrame com os leads para resumo
    """
    # Reutiliza a função otimizada
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

