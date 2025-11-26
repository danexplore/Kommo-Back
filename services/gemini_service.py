"""
Serviço de IA com Google Gemini
"""
import streamlit as st
from typing import Optional, Dict, Any, List
import google.generativeai as genai

from config import CACHE_TTL_IA


@st.cache_resource
def init_gemini():
    """Inicializa cliente Google Gemini"""
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    
    if not api_key:
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')


# Cliente global
_gemini_client = None


def get_gemini():
    """Retorna instância do cliente Gemini"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = init_gemini()
    return _gemini_client


@st.cache_data(ttl=CACHE_TTL_IA)
def gerar_insights_ia(
    metricas_atual: Dict[str, Any],
    metricas_anterior: Dict[str, Any],
    periodo_descricao: str
) -> Optional[str]:
    """
    Gera insights usando IA baseado nas métricas do período.
    
    Args:
        metricas_atual: Dicionário com métricas do período atual
        metricas_anterior: Dicionário com métricas do período anterior
        periodo_descricao: Descrição textual do período
    
    Returns:
        String com insights gerados ou None se falhar
    """
    model = get_gemini()
    
    if model is None:
        return None
    
    try:
        prompt = f"""
        Você é um analista de vendas especializado em concessionárias de veículos.
        Analise os seguintes dados de performance e forneça insights estratégicos em português brasileiro.
        
        **Período:** {periodo_descricao}
        
        **Métricas Atuais:**
        - Total de Leads: {metricas_atual.get('total_leads', 0)}
        - Demos Agendadas: {metricas_atual.get('demos_agendadas', 0)}
        - Demos Realizadas: {metricas_atual.get('demos_realizadas', 0)}
        - No-shows: {metricas_atual.get('noshows', 0)}
        - Vendas: {metricas_atual.get('vendas', 0)}
        
        **Métricas do Período Anterior (para comparação):**
        - Total de Leads: {metricas_anterior.get('total_leads', 0)}
        - Demos Agendadas: {metricas_anterior.get('demos_agendadas', 0)}
        - Demos Realizadas: {metricas_anterior.get('demos_realizadas', 0)}
        - No-shows: {metricas_anterior.get('noshows', 0)}
        - Vendas: {metricas_anterior.get('vendas', 0)}
        
        Por favor, forneça:
        1. **Resumo Geral** (2-3 frases sobre a performance)
        2. **Pontos Positivos** (máximo 3 itens)
        3. **Pontos de Atenção** (máximo 3 itens)
        4. **Recomendações Estratégicas** (máximo 3 ações concretas)
        
        Use emojis para tornar a leitura mais agradável. Seja objetivo e direto.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        st.error(f"❌ Erro ao gerar insights: {str(e)}")
        return None


def chat_com_dados(
    mensagem_usuario: str,
    metricas_atual: Dict[str, Any],
    metricas_anterior: Dict[str, Any],
    periodo_descricao: str,
    historico_chat: List[Dict[str, str]]
) -> Optional[str]:
    """
    Responde perguntas do usuário baseado nos dados do dashboard.
    
    Args:
        mensagem_usuario: Pergunta do usuário
        metricas_atual: Métricas do período atual
        metricas_anterior: Métricas do período anterior
        periodo_descricao: Descrição do período
        historico_chat: Histórico de mensagens anteriores
    
    Returns:
        Resposta da IA ou None se falhar
    """
    model = get_gemini()
    
    if model is None:
        return None
    
    try:
        # Montar contexto do histórico
        historico_texto = ""
        for msg in historico_chat[-5:]:  # Últimas 5 mensagens
            role = "Usuário" if msg.get('role') == 'user' else "Assistente"
            historico_texto += f"{role}: {msg.get('content', '')}\n"
        
        prompt = f"""
        Você é um assistente de análise de dados de vendas da ecosys AUTO.
        Responda a pergunta do usuário baseado nos dados disponíveis.
        
        **Contexto do Período:** {periodo_descricao}
        
        **Dados Disponíveis:**
        - Total de Leads: {metricas_atual.get('total_leads', 0)}
        - Demos Agendadas: {metricas_atual.get('demos_agendadas', 0)}
        - Demos Realizadas: {metricas_atual.get('demos_realizadas', 0)}
        - No-shows: {metricas_atual.get('noshows', 0)}
        - Vendas: {metricas_atual.get('vendas', 0)}
        
        **Período Anterior (comparação):**
        - Total de Leads: {metricas_anterior.get('total_leads', 0)}
        - Demos Agendadas: {metricas_anterior.get('demos_agendadas', 0)}
        - Demos Realizadas: {metricas_anterior.get('demos_realizadas', 0)}
        - No-shows: {metricas_anterior.get('noshows', 0)}
        - Vendas: {metricas_anterior.get('vendas', 0)}
        
        **Histórico da Conversa:**
        {historico_texto}
        
        **Pergunta do Usuário:** {mensagem_usuario}
        
        Responda de forma objetiva em português brasileiro. Use dados concretos quando possível.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ Erro ao processar pergunta: {str(e)}"
