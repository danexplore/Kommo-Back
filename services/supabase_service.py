"""
Serviço de conexão com Supabase
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, List
from supabase import create_client, Client

from config import CACHE_TTL_LEADS, CACHE_TTL_CHAMADAS, CACHE_TTL_TEMPO


@st.cache_resource
def init_supabase() -> Client:
    """Inicializa conexão com Supabase"""
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    
    if not url or not key:
        st.error("⚠️ Credenciais do Supabase não configuradas. Configure SUPABASE_URL e SUPABASE_KEY.")
        st.stop()
    
    return create_client(url, key)


# Cliente global
_supabase: Optional[Client] = None


def get_supabase() -> Client:
    """Retorna instância do cliente Supabase"""
    global _supabase
    if _supabase is None:
        _supabase = init_supabase()
    return _supabase


@st.cache_data(ttl=CACHE_TTL_LEADS)
def get_leads_data(data_inicio: datetime, data_fim: datetime, vendedores: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Busca dados de leads da view kommo_leads_statistics.
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
        vendedores: Lista de vendedores para filtrar (opcional)
    
    Returns:
        DataFrame com os leads do período
    """
    supabase = get_supabase()
    
    try:
        data_inicio_iso = data_inicio.isoformat()
        data_fim_iso = data_fim.isoformat()
        
        all_data = []
        date_columns_to_query = ['criado_em', 'data_demo', 'data_noshow', 'data_agendamento', 'data_venda']
        
        # Buscar leads por cada coluna de data
        for col in date_columns_to_query:
            try:
                response = supabase.table('kommo_leads_statistics').select('*').gte(col, data_inicio_iso).lte(col, data_fim_iso).execute()
                if response.data:
                    all_data.extend(response.data)
            except Exception:
                continue
        
        # Remover duplicatas usando ID
        if all_data:
            seen_ids = set()
            unique_data = []
            for item in all_data:
                item_id = item.get('id')
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_data.append(item)
            all_data = unique_data
        
        # Aplicar filtro de vendedor
        if vendedores and len(vendedores) > 0:
            all_data = [item for item in all_data if item.get('vendedor') in vendedores]
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Converter colunas de data
            for col in date_columns_to_query:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
        
        return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados de leads: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL_LEADS)
def get_all_leads_for_summary(data_inicio: datetime, data_fim: datetime, vendedores: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Busca todos os leads para o resumo diário (sem filtro de criado_em).
    
    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
        vendedores: Lista de vendedores para filtrar (opcional)
    
    Returns:
        DataFrame com os leads para resumo
    """
    supabase = get_supabase()
    
    try:
        data_inicio_iso = data_inicio.isoformat()
        data_fim_iso = data_fim.isoformat()
        
        all_data = []
        date_columns_to_query = ['criado_em', 'data_demo', 'data_noshow', 'data_agendamento', 'data_venda']
        
        for col in date_columns_to_query:
            try:
                response = supabase.table('kommo_leads_statistics').select('*').gte(col, data_inicio_iso).lte(col, data_fim_iso).execute()
                if response.data:
                    all_data.extend(response.data)
            except Exception:
                continue
        
        # Remover duplicatas
        if all_data:
            seen_ids = set()
            unique_data = []
            for item in all_data:
                item_id = item.get('id')
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_data.append(item)
            all_data = unique_data
        
        # Aplicar filtro de vendedor
        if vendedores and len(vendedores) > 0:
            all_data = [item for item in all_data if item.get('vendedor') in vendedores]
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            for col in date_columns_to_query:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
        
        return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados para resumo: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL_TEMPO)
def get_tempo_por_etapa() -> pd.DataFrame:
    """
    Busca o tempo médio que leads ficam em cada etapa.
    
    Returns:
        DataFrame com tempo médio por etapa
    """
    supabase = get_supabase()
    
    try:
        response = supabase.rpc('get_tempo_por_etapa').execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
            
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL_CHAMADAS)
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
    
    try:
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
                if len(response.data) < page_size:
                    break
                offset += page_size
            else:
                break
        
        if all_data:
            df = pd.DataFrame(all_data)
            if 'duration' in df.columns:
                df['duration_minutos'] = df['duration'].apply(lambda x: round(x / 60, 2) if x > 0 else 0)
            return df
        
        return pd.DataFrame()
            
    except Exception as e:
        return pd.DataFrame()
