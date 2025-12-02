"""
Serviço de IA com Google Gemini

Implementa:
- Rate limiting para controle de custos
- Sanitização de inputs contra prompt injection
- Logging estruturado
- Tratamento de erros consistente
"""
import streamlit as st
from typing import Optional, Dict, Any, List
import google.generativeai as genai

from config import CACHE_TTL_IA
from core.logging import get_logger, log_execution
from core.security import sanitize_ai_prompt, rate_limit, check_rate_limit
from core.exceptions import handle_error, APIError


# Logger do módulo
logger = get_logger("gemini_service")


@st.cache_resource
def init_gemini():
    """
    Inicializa cliente Google Gemini.
    
    Returns:
        Modelo Gemini configurado ou None se não disponível
    """
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    
    if not api_key:
        logger.warning("GEMINI_API_KEY não configurada - funcionalidades de IA desabilitadas")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Cliente Gemini inicializado com sucesso")
        return model
    except Exception as e:
        logger.error("Falha ao inicializar Gemini", exception=e)
        return None


# Cliente global
_gemini_client = None


def get_gemini():
    """Retorna instância do cliente Gemini"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = init_gemini()
    return _gemini_client


@st.cache_data(ttl=CACHE_TTL_IA)
@log_execution("gemini_service")
@handle_error(default_return=None, show_user_error=True)
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
        logger.warning("Tentativa de gerar insights sem modelo Gemini disponível")
        return None
    
    # Rate limiting
    if not check_rate_limit("gemini_insights"):
        st.warning("⏳ Muitas requisições de IA. Aguarde um momento.")
        return None
    
    # Sanitizar descrição do período (input do usuário)
    periodo_descricao = sanitize_ai_prompt(periodo_descricao)
    
    prompt = f"""
    Você é um analista sênior de SaaS B2B especializado em análise de funil de vendas e otimização de processos comerciais para software empresarial.

    **CONTEXTO DO NEGÓCIO:**
    SaaS B2B que oferece sistema de gestão para lojas de revenda de veículos novos e seminovos. Processo de vendas: geração de leads → agendamento de demonstração do sistema → realização da demo → fechamento da venda (assinatura do software).

    **PERÍODO DE ANÁLISE:** {periodo_descricao}

    **DADOS DO PERÍODO ATUAL:**
    - Total de Leads: {metricas_atual.get('total_leads', 0):,}
    - Demos Agendadas: {metricas_atual.get('demos_agendadas', 0):,}
    - Demos Realizadas: {metricas_atual.get('demos_realizadas', 0):,}
    - No-shows: {metricas_atual.get('noshows', 0):,}
    - Vendas Fechadas: {metricas_atual.get('vendas', 0):,}

    **DADOS DO PERÍODO ANTERIOR (baseline):**
    - Total de Leads: {metricas_anterior.get('total_leads', 0):,}
    - Demos Agendadas: {metricas_anterior.get('demos_agendadas', 0):,}
    - Demos Realizadas: {metricas_anterior.get('demos_realizadas', 0):,}
    - No-shows: {metricas_anterior.get('noshows', 0):,}
    - Vendas Fechadas: {metricas_anterior.get('vendas', 0):,}

    **INSTRUÇÕES DE ANÁLISE:**

    Calcule automaticamente as seguintes taxas de conversão para ambos os períodos e compare:
    - Taxa de Qualificação: (demos agendadas / total leads) × 100
    - Taxa de Comparecimento: (demos realizadas / demos agendadas) × 100
    - Taxa de No-show: (no-shows / demos agendadas) × 100
    - Taxa de Fechamento: (vendas / demos realizadas) × 100
    - Taxa de Conversão End-to-End: (vendas / total leads) × 100

    **FORMATO DA RESPOSTA:**

    ## 📊 Resumo Executivo
    [2-3 frases destacando a performance geral do funil e a principal tendência observada. Inclua pelo menos uma métrica percentual comparativa.]

    ## ✅ Destaques Positivos
    [Liste até 3 pontos fortes com dados específicos. Priorize melhorias percentuais significativas e etapas do funil que estão performando bem.]

    ## ⚠️ Pontos Críticos de Atenção
    [Liste até 3 gargalos no funil ou quedas de performance com impacto quantificado. Identifique onde o funil está "vazando".]

    ## 🎯 Recomendações Estratégicas Priorizadas
    [Liste 3 ações específicas e implementáveis, ordenadas por impacto esperado. Cada recomendação deve indicar qual etapa do funil ela visa otimizar e o resultado esperado.]

    **DIRETRIZES DE ESTILO:**
    ✓ Use linguagem clara voltada para gestores de vendas SaaS
    ✓ Inclua números e percentuais específicos em cada ponto
    ✓ Priorize insights acionáveis sobre descrições genéricas
    ✓ Use emojis estrategicamente para facilitar escaneabilidade
    ✓ Seja direto ao ponto - gestores de SaaS valorizam eficiência
    ✓ Destaque variações percentuais maiores que ±10% como significativas
    ✓ Considere benchmarks típicos de SaaS B2B quando relevante
    """
    
    response = model.generate_content(prompt)
    logger.info("Insights gerados com sucesso")
    return response.text


@log_execution("gemini_service")
@handle_error(default_return=None, show_user_error=True)
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
        logger.warning("Tentativa de chat sem modelo Gemini disponível")
        return "❌ Funcionalidade de IA não disponível. Configure a chave GEMINI_API_KEY."
    
    # Rate limiting - mais restritivo para chat
    if not check_rate_limit("gemini_chat"):
        return "⏳ Muitas requisições. Aguarde alguns segundos antes de enviar outra mensagem."
    
    # IMPORTANTE: Sanitizar input do usuário contra prompt injection
    mensagem_usuario = sanitize_ai_prompt(mensagem_usuario)
    periodo_descricao = sanitize_ai_prompt(periodo_descricao)
    
    if not mensagem_usuario.strip():
        return "❌ Por favor, digite uma pergunta válida."
    
    logger.info("Processando chat", message_length=len(mensagem_usuario))
    
    # Montar contexto do histórico (também sanitizado)
    historico_texto = ""
    for msg in historico_chat[-5:]:  # Últimas 5 mensagens
        role = "Usuário" if msg.get('role') == 'user' else "Assistente"
        content = sanitize_ai_prompt(msg.get('content', ''))[:500]  # Limitar tamanho
        historico_texto += f"{role}: {content}\n"
    
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
    Limite sua resposta a informações relevantes sobre vendas e métricas do dashboard.
    """
    
    response = model.generate_content(prompt)
    logger.info("Resposta de chat gerada com sucesso")
    return response.text

