"""
Módulo de Análise de Marketing - Dashboard Kommo

Fornece análises avançadas de campanhas de marketing:
- Performance por UTM (campaign, source, medium)
- Análise de desqualificação por campanha
- Comparação entre períodos
- Insights automáticos
- ROI e eficiência de campanhas
"""
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.logging import get_logger


logger = get_logger("marketing_analytics")


# ========================================
# ENUMS E CONSTANTES
# ========================================

class UTMDimension(Enum):
    """Dimensões UTM disponíveis para análise"""
    CAMPAIGN = "utm_campaign"
    SOURCE = "utm_source"
    MEDIUM = "utm_medium"
    
    @property
    def display_name(self) -> str:
        names = {
            "utm_campaign": "Campanha",
            "utm_source": "Fonte",
            "utm_medium": "Mídia"
        }
        return names.get(self.value, self.value)
    
    @property
    def icon(self) -> str:
        icons = {
            "utm_campaign": "🎯",
            "utm_source": "🌐",
            "utm_medium": "📱"
        }
        return icons.get(self.value, "📊")


class InsightType(Enum):
    """Tipos de insights gerados"""
    POSITIVE = "positive"      # Destaque positivo
    WARNING = "warning"        # Alerta/atenção
    CRITICAL = "critical"      # Problema crítico
    INFO = "info"              # Informativo
    OPPORTUNITY = "opportunity" # Oportunidade de melhoria


@dataclass
class MarketingInsight:
    """Representa um insight de marketing"""
    type: InsightType
    title: str
    description: str
    metric_value: Optional[float] = None
    metric_label: Optional[str] = None
    campaign: Optional[str] = None
    recommendation: Optional[str] = None
    priority: int = 1  # 1 = alta, 2 = média, 3 = baixa
    
    @property
    def icon(self) -> str:
        icons = {
            InsightType.POSITIVE: "✅",
            InsightType.WARNING: "⚠️",
            InsightType.CRITICAL: "🚨",
            InsightType.INFO: "ℹ️",
            InsightType.OPPORTUNITY: "💡"
        }
        return icons.get(self.type, "📊")


@dataclass
class CampaignMetrics:
    """Métricas de uma campanha"""
    name: str
    total_leads: int = 0
    demos_agendadas: int = 0
    demos_realizadas: int = 0
    desqualificados: int = 0
    vendas: int = 0
    noshows: int = 0
    
    @property
    def taxa_agendamento(self) -> float:
        return (self.demos_agendadas / self.total_leads * 100) if self.total_leads > 0 else 0
    
    @property
    def taxa_realizacao(self) -> float:
        return (self.demos_realizadas / self.demos_agendadas * 100) if self.demos_agendadas > 0 else 0
    
    @property
    def taxa_desqualificacao(self) -> float:
        return (self.desqualificados / self.demos_realizadas * 100) if self.demos_realizadas > 0 else 0
    
    @property
    def taxa_conversao(self) -> float:
        return (self.vendas / self.demos_realizadas * 100) if self.demos_realizadas > 0 else 0
    
    @property
    def taxa_noshow(self) -> float:
        return (self.noshows / self.demos_agendadas * 100) if self.demos_agendadas > 0 else 0
    
    @property
    def taxa_aproveitamento(self) -> float:
        """Taxa de leads que não foram desqualificados"""
        return ((self.demos_realizadas - self.desqualificados) / self.demos_realizadas * 100) if self.demos_realizadas > 0 else 0
    
    @property
    def eficiencia_funil(self) -> float:
        """Eficiência geral do funil (vendas / leads)"""
        return (self.vendas / self.total_leads * 100) if self.total_leads > 0 else 0


@dataclass
class PeriodComparison:
    """Comparação entre dois períodos"""
    metric_name: str
    current_value: float
    previous_value: float
    
    @property
    def absolute_change(self) -> float:
        return self.current_value - self.previous_value
    
    @property
    def percentage_change(self) -> float:
        if self.previous_value == 0:
            return 100 if self.current_value > 0 else 0
        return ((self.current_value - self.previous_value) / self.previous_value) * 100
    
    @property
    def trend(self) -> str:
        if self.percentage_change > 5:
            return "up"
        elif self.percentage_change < -5:
            return "down"
        return "stable"
    
    @property
    def trend_icon(self) -> str:
        icons = {"up": "📈", "down": "📉", "stable": "➡️"}
        return icons.get(self.trend, "")


# ========================================
# CLASSE PRINCIPAL DE ANÁLISE
# ========================================

class MarketingAnalyzer:
    """
    Analisador de marketing com insights avançados.
    
    Uso:
        analyzer = MarketingAnalyzer(df_leads, df_leads_anterior)
        metrics = analyzer.get_campaign_metrics(UTMDimension.CAMPAIGN)
        insights = analyzer.generate_insights()
        comparison = analyzer.compare_periods()
    """
    
    # Status que indicam desqualificação
    DESQUALIFICADO_STATUS = "Desqualificados"
    
    # Limites para alertas
    THRESHOLD_DESQUALIFICACAO_ALTA = 40  # %
    THRESHOLD_DESQUALIFICACAO_CRITICA = 60  # %
    THRESHOLD_NOSHOW_ALTO = 30  # %
    THRESHOLD_CONVERSAO_BAIXA = 10  # %
    MIN_LEADS_ANALISE = 5  # Mínimo de leads para análise estatística
    
    def __init__(
        self,
        df_leads: pd.DataFrame,
        df_leads_anterior: Optional[pd.DataFrame] = None,
        demo_completed_statuses: Optional[List[str]] = None
    ):
        """
        Args:
            df_leads: DataFrame com leads do período atual
            df_leads_anterior: DataFrame com leads do período anterior (para comparação)
            demo_completed_statuses: Lista de status que indicam demo realizada
        """
        self.df = df_leads.copy() if not df_leads.empty else pd.DataFrame()
        self.df_anterior = df_leads_anterior.copy() if df_leads_anterior is not None and not df_leads_anterior.empty else None
        self.demo_completed_statuses = demo_completed_statuses or []
        
        # Normalizar colunas UTM
        self._normalize_utm_columns()
        
        logger.info(
            "MarketingAnalyzer inicializado",
            leads_atual=len(self.df),
            leads_anterior=len(self.df_anterior) if self.df_anterior is not None else 0
        )
    
    def _normalize_utm_columns(self) -> None:
        """Normaliza colunas UTM (preenche vazios, trata nulos)"""
        utm_cols = ['utm_campaign', 'utm_source', 'utm_medium']
        
        for df in [self.df, self.df_anterior]:
            if df is None or df.empty:
                continue
            for col in utm_cols:
                if col in df.columns:
                    df[col] = df[col].fillna('(não rastreado)')
                    df[col] = df[col].replace('', '(não rastreado)')
                    df[col] = df[col].str.strip()
    
    def get_available_dimensions(self) -> List[UTMDimension]:
        """Retorna dimensões UTM disponíveis nos dados"""
        available = []
        for dim in UTMDimension:
            if dim.value in self.df.columns:
                # Verificar se há dados além de "(não rastreado)"
                unique_values = self.df[dim.value].unique()
                if len(unique_values) > 1 or (len(unique_values) == 1 and unique_values[0] != '(não rastreado)'):
                    available.append(dim)
        return available
    
    def get_campaign_metrics(
        self,
        dimension: UTMDimension = UTMDimension.CAMPAIGN,
        min_leads: int = 1
    ) -> List[CampaignMetrics]:
        """
        Calcula métricas por campanha/fonte/mídia.
        
        Args:
            dimension: Dimensão UTM para agrupar
            min_leads: Mínimo de leads para incluir na análise
        
        Returns:
            Lista de CampaignMetrics ordenada por total de leads
        """
        if self.df.empty or dimension.value not in self.df.columns:
            return []
        
        metrics_list = []
        
        for campaign_name in self.df[dimension.value].unique():
            df_campaign = self.df[self.df[dimension.value] == campaign_name]
            
            if len(df_campaign) < min_leads:
                continue
            
            metrics = CampaignMetrics(name=campaign_name)
            metrics.total_leads = len(df_campaign)
            
            # Demos agendadas
            if 'data_demo' in df_campaign.columns:
                metrics.demos_agendadas = df_campaign['data_demo'].notna().sum()
            
            # Demos realizadas (usando status)
            if 'status' in df_campaign.columns and self.demo_completed_statuses:
                demos_realizadas_mask = (
                    df_campaign['status'].isin(self.demo_completed_statuses) |
                    (
                        (df_campaign['status'] == self.DESQUALIFICADO_STATUS) &
                        (df_campaign['data_demo'].notna()) &
                        (df_campaign.get('data_noshow', pd.Series([None]*len(df_campaign))).isna())
                    )
                )
                metrics.demos_realizadas = demos_realizadas_mask.sum()
            
            # Desqualificados
            if 'status' in df_campaign.columns:
                metrics.desqualificados = (df_campaign['status'] == self.DESQUALIFICADO_STATUS).sum()
            
            # Vendas
            if 'data_venda' in df_campaign.columns:
                metrics.vendas = df_campaign['data_venda'].notna().sum()
            
            # No-shows
            if 'data_noshow' in df_campaign.columns:
                metrics.noshows = df_campaign['data_noshow'].notna().sum()
            
            metrics_list.append(metrics)
        
        # Ordenar por total de leads
        metrics_list.sort(key=lambda x: x.total_leads, reverse=True)
        
        return metrics_list
    
    def get_metrics_dataframe(
        self,
        dimension: UTMDimension = UTMDimension.CAMPAIGN,
        min_leads: int = 1
    ) -> pd.DataFrame:
        """
        Retorna DataFrame com todas as métricas por campanha.
        
        Args:
            dimension: Dimensão UTM
            min_leads: Mínimo de leads
        
        Returns:
            DataFrame formatado para exibição
        """
        metrics_list = self.get_campaign_metrics(dimension, min_leads)
        
        if not metrics_list:
            return pd.DataFrame()
        
        data = []
        for m in metrics_list:
            data.append({
                dimension.display_name: m.name,
                'Total Leads': m.total_leads,
                'Demos Agendadas': m.demos_agendadas,
                'Demos Realizadas': m.demos_realizadas,
                'Desqualificados': m.desqualificados,
                'Vendas': m.vendas,
                'No-shows': m.noshows,
                '% Agendamento': round(m.taxa_agendamento, 1),
                '% Realização': round(m.taxa_realizacao, 1),
                '% Desqualificação': round(m.taxa_desqualificacao, 1),
                '% Conversão': round(m.taxa_conversao, 1),
                '% No-show': round(m.taxa_noshow, 1),
                '% Aproveitamento': round(m.taxa_aproveitamento, 1),
                'Eficiência Funil': round(m.eficiencia_funil, 2)
            })
        
        return pd.DataFrame(data)
    
    def compare_periods(
        self,
        dimension: UTMDimension = UTMDimension.CAMPAIGN
    ) -> Dict[str, List[PeriodComparison]]:
        """
        Compara métricas entre período atual e anterior.
        
        Returns:
            Dicionário {nome_campanha: [lista de comparações]}
        """
        if self.df_anterior is None or self.df_anterior.empty:
            return {}
        
        current_metrics = {m.name: m for m in self.get_campaign_metrics(dimension)}
        
        # Calcular métricas do período anterior
        analyzer_anterior = MarketingAnalyzer(
            self.df_anterior,
            demo_completed_statuses=self.demo_completed_statuses
        )
        previous_metrics = {m.name: m for m in analyzer_anterior.get_campaign_metrics(dimension)}
        
        comparisons = {}
        
        # Campanhas em ambos os períodos
        all_campaigns = set(current_metrics.keys()) | set(previous_metrics.keys())
        
        for campaign in all_campaigns:
            curr = current_metrics.get(campaign)
            prev = previous_metrics.get(campaign)
            
            campaign_comparisons = []
            
            metrics_to_compare = [
                ('total_leads', 'Total Leads'),
                ('demos_realizadas', 'Demos Realizadas'),
                ('taxa_desqualificacao', '% Desqualificação'),
                ('taxa_conversao', '% Conversão'),
                ('taxa_noshow', '% No-show'),
                ('vendas', 'Vendas'),
            ]
            
            for attr, label in metrics_to_compare:
                curr_val = getattr(curr, attr, 0) if curr else 0
                prev_val = getattr(prev, attr, 0) if prev else 0
                
                campaign_comparisons.append(PeriodComparison(
                    metric_name=label,
                    current_value=curr_val,
                    previous_value=prev_val
                ))
            
            comparisons[campaign] = campaign_comparisons
        
        return comparisons
    
    def generate_insights(
        self,
        dimension: UTMDimension = UTMDimension.CAMPAIGN,
        max_insights: int = 10
    ) -> List[MarketingInsight]:
        """
        Gera insights automáticos baseados nos dados.
        
        Args:
            dimension: Dimensão UTM para análise
            max_insights: Número máximo de insights
        
        Returns:
            Lista de MarketingInsight ordenada por prioridade
        """
        insights = []
        metrics_list = self.get_campaign_metrics(dimension, min_leads=self.MIN_LEADS_ANALISE)
        
        if not metrics_list:
            insights.append(MarketingInsight(
                type=InsightType.INFO,
                title="Dados Insuficientes",
                description=f"Não há campanhas com volume mínimo de {self.MIN_LEADS_ANALISE} leads para análise estatística.",
                priority=3
            ))
            return insights
        
        # 1. Melhor campanha em volume
        best_volume = metrics_list[0]
        total_leads = sum(m.total_leads for m in metrics_list)
        share = (best_volume.total_leads / total_leads * 100) if total_leads > 0 else 0
        
        insights.append(MarketingInsight(
            type=InsightType.POSITIVE,
            title="Maior Volume de Leads",
            description=f"A campanha '{best_volume.name}' lidera com {best_volume.total_leads} leads ({share:.1f}% do total).",
            metric_value=best_volume.total_leads,
            metric_label="leads",
            campaign=best_volume.name,
            priority=2
        ))
        
        # 2. Melhor taxa de conversão
        campaigns_with_sales = [m for m in metrics_list if m.vendas > 0]
        if campaigns_with_sales:
            best_conversion = max(campaigns_with_sales, key=lambda x: x.taxa_conversao)
            insights.append(MarketingInsight(
                type=InsightType.POSITIVE,
                title="Melhor Taxa de Conversão",
                description=f"'{best_conversion.name}' converte {best_conversion.taxa_conversao:.1f}% das demos em vendas ({best_conversion.vendas} vendas de {best_conversion.demos_realizadas} demos).",
                metric_value=best_conversion.taxa_conversao,
                metric_label="%",
                campaign=best_conversion.name,
                recommendation="Investir mais nesta campanha pode aumentar vendas.",
                priority=1
            ))
        
        # 3. Campanhas com alta desqualificação
        high_desq = [m for m in metrics_list if m.taxa_desqualificacao >= self.THRESHOLD_DESQUALIFICACAO_ALTA]
        for m in high_desq[:3]:
            insight_type = InsightType.CRITICAL if m.taxa_desqualificacao >= self.THRESHOLD_DESQUALIFICACAO_CRITICA else InsightType.WARNING
            
            insights.append(MarketingInsight(
                type=insight_type,
                title="Alta Taxa de Desqualificação",
                description=f"'{m.name}' tem {m.taxa_desqualificacao:.1f}% de desqualificação ({m.desqualificados} de {m.demos_realizadas} demos).",
                metric_value=m.taxa_desqualificacao,
                metric_label="%",
                campaign=m.name,
                recommendation="Revisar público-alvo e qualificação inicial dos leads.",
                priority=1 if insight_type == InsightType.CRITICAL else 2
            ))
        
        # 4. Campanhas com alto no-show
        high_noshow = [m for m in metrics_list if m.taxa_noshow >= self.THRESHOLD_NOSHOW_ALTO and m.demos_agendadas >= 5]
        for m in high_noshow[:2]:
            insights.append(MarketingInsight(
                type=InsightType.WARNING,
                title="Alta Taxa de No-show",
                description=f"'{m.name}' tem {m.taxa_noshow:.1f}% de no-shows ({m.noshows} de {m.demos_agendadas} agendamentos).",
                metric_value=m.taxa_noshow,
                metric_label="%",
                campaign=m.name,
                recommendation="Implementar lembretes e confirmação de presença.",
                priority=2
            ))
        
        # 5. Campanhas com baixa conversão mas bom volume
        low_conversion = [
            m for m in metrics_list 
            if m.taxa_conversao < self.THRESHOLD_CONVERSAO_BAIXA 
            and m.demos_realizadas >= 10
            and m.vendas >= 1
        ]
        for m in low_conversion[:2]:
            insights.append(MarketingInsight(
                type=InsightType.OPPORTUNITY,
                title="Oportunidade de Melhoria",
                description=f"'{m.name}' tem bom volume ({m.demos_realizadas} demos) mas baixa conversão ({m.taxa_conversao:.1f}%).",
                metric_value=m.taxa_conversao,
                metric_label="%",
                campaign=m.name,
                recommendation="Otimizar o processo de fechamento para esta campanha.",
                priority=2
            ))
        
        # 6. Leads não rastreados
        not_tracked = [m for m in metrics_list if '(não rastreado)' in m.name.lower() or 'não informado' in m.name.lower()]
        if not_tracked:
            total_not_tracked = sum(m.total_leads for m in not_tracked)
            pct_not_tracked = (total_not_tracked / total_leads * 100) if total_leads > 0 else 0
            
            if pct_not_tracked > 10:
                insights.append(MarketingInsight(
                    type=InsightType.WARNING,
                    title="Rastreamento Incompleto",
                    description=f"{pct_not_tracked:.1f}% dos leads ({total_not_tracked}) não possuem UTM rastreada.",
                    metric_value=pct_not_tracked,
                    metric_label="%",
                    recommendation="Revisar configuração de UTMs nas campanhas e landing pages.",
                    priority=2
                ))
        
        # 7. Comparação com período anterior
        if self.df_anterior is not None and not self.df_anterior.empty:
            comparisons = self.compare_periods(dimension)
            
            # Identificar campanhas com queda significativa
            for campaign, comps in comparisons.items():
                for comp in comps:
                    if comp.metric_name == 'Vendas' and comp.percentage_change < -20 and comp.previous_value >= 3:
                        insights.append(MarketingInsight(
                            type=InsightType.CRITICAL,
                            title="Queda em Vendas",
                            description=f"'{campaign}' teve queda de {abs(comp.percentage_change):.1f}% em vendas vs período anterior.",
                            metric_value=comp.percentage_change,
                            metric_label="%",
                            campaign=campaign,
                            recommendation="Investigar mudanças na campanha ou mercado.",
                            priority=1
                        ))
                    
                    if comp.metric_name == '% Desqualificação' and comp.absolute_change > 15 and comp.current_value >= 30:
                        insights.append(MarketingInsight(
                            type=InsightType.WARNING,
                            title="Aumento em Desqualificação",
                            description=f"'{campaign}' aumentou {comp.absolute_change:.1f}pp em desqualificação (de {comp.previous_value:.1f}% para {comp.current_value:.1f}%).",
                            metric_value=comp.absolute_change,
                            metric_label="pp",
                            campaign=campaign,
                            recommendation="Verificar qualidade dos leads desta fonte.",
                            priority=2
                        ))
        
        # 8. Melhor eficiência de funil
        best_efficiency = max(metrics_list, key=lambda x: x.eficiencia_funil)
        if best_efficiency.eficiencia_funil > 0:
            insights.append(MarketingInsight(
                type=InsightType.POSITIVE,
                title="Melhor Eficiência de Funil",
                description=f"'{best_efficiency.name}' tem a melhor eficiência geral: {best_efficiency.eficiencia_funil:.2f}% de leads convertidos em vendas.",
                metric_value=best_efficiency.eficiencia_funil,
                metric_label="%",
                campaign=best_efficiency.name,
                priority=2
            ))
        
        # 9. Campanhas sem vendas
        no_sales = [m for m in metrics_list if m.vendas == 0 and m.demos_realizadas >= 5]
        if no_sales:
            names = ", ".join([m.name for m in no_sales[:3]])
            insights.append(MarketingInsight(
                type=InsightType.WARNING,
                title="Campanhas Sem Conversão",
                description=f"{len(no_sales)} campanha(s) com demos realizadas mas sem vendas: {names}.",
                metric_value=len(no_sales),
                metric_label="campanhas",
                recommendation="Avaliar se o público-alvo está correto ou descontinuar.",
                priority=2
            ))
        
        # Ordenar por prioridade e limitar
        insights.sort(key=lambda x: x.priority)
        
        return insights[:max_insights]
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas resumidas de todas as campanhas.
        
        Returns:
            Dicionário com métricas agregadas
        """
        if self.df.empty:
            return {}
        
        total_leads = len(self.df)
        
        # Calcular por diferentes dimensões
        summary = {
            'total_leads': total_leads,
            'campanhas_ativas': 0,
            'fontes_ativas': 0,
            'midias_ativas': 0,
            'leads_rastreados': 0,
            'pct_rastreamento': 0,
            'total_vendas': 0,
            'taxa_conversao_geral': 0,
            'melhor_campanha': None,
            'pior_campanha': None,
            'campanha_mais_vendas': None,
        }
        
        # Contagem por dimensão
        for dim in UTMDimension:
            if dim.value in self.df.columns:
                unique = self.df[dim.value].unique()
                tracked = [v for v in unique if '(não rastreado)' not in str(v).lower() and 'não informado' not in str(v).lower()]
                
                if dim == UTMDimension.CAMPAIGN:
                    summary['campanhas_ativas'] = len(tracked)
                elif dim == UTMDimension.SOURCE:
                    summary['fontes_ativas'] = len(tracked)
                elif dim == UTMDimension.MEDIUM:
                    summary['midias_ativas'] = len(tracked)
        
        # Leads rastreados
        if 'utm_campaign' in self.df.columns:
            rastreados = self.df[
                (~self.df['utm_campaign'].str.contains('não rastreado|não informado', case=False, na=False))
            ]
            summary['leads_rastreados'] = len(rastreados)
            summary['pct_rastreamento'] = (len(rastreados) / total_leads * 100) if total_leads > 0 else 0
        
        # Vendas
        if 'data_venda' in self.df.columns:
            summary['total_vendas'] = self.df['data_venda'].notna().sum()
            summary['taxa_conversao_geral'] = (summary['total_vendas'] / total_leads * 100) if total_leads > 0 else 0
        
        # Melhores/piores campanhas
        metrics = self.get_campaign_metrics(UTMDimension.CAMPAIGN, min_leads=5)
        metrics_filtrados = [m for m in metrics if '(não rastreado)' not in m.name.lower()]
        
        if metrics_filtrados:
            # Melhor por conversão
            with_sales = [m for m in metrics_filtrados if m.vendas > 0]
            if with_sales:
                best = max(with_sales, key=lambda x: x.taxa_conversao)
                summary['melhor_campanha'] = {
                    'nome': best.name,
                    'taxa_conversao': best.taxa_conversao,
                    'vendas': best.vendas
                }
            
            # Pior por desqualificação
            worst = max(metrics_filtrados, key=lambda x: x.taxa_desqualificacao)
            if worst.taxa_desqualificacao > 0:
                summary['pior_campanha'] = {
                    'nome': worst.name,
                    'taxa_desqualificacao': worst.taxa_desqualificacao,
                    'desqualificados': worst.desqualificados
                }
            
            # Mais vendas
            most_sales = max(metrics_filtrados, key=lambda x: x.vendas)
            if most_sales.vendas > 0:
                summary['campanha_mais_vendas'] = {
                    'nome': most_sales.name,
                    'vendas': most_sales.vendas,
                    'total_leads': most_sales.total_leads
                }
        
        return summary
    
    def get_desqualification_analysis(
        self,
        dimension: UTMDimension = UTMDimension.CAMPAIGN
    ) -> pd.DataFrame:
        """
        Análise detalhada de desqualificação por campanha.
        
        Returns:
            DataFrame com análise de desqualificação
        """
        if self.df.empty or 'motivos_desqualificacao' not in self.df.columns:
            return pd.DataFrame()
        
        df_desq = self.df[self.df['status'] == self.DESQUALIFICADO_STATUS].copy()
        
        if df_desq.empty:
            return pd.DataFrame()
        
        # Agrupar por campanha e motivo
        analysis = df_desq.groupby([dimension.value, 'motivos_desqualificacao']).size().reset_index(name='quantidade')
        
        # Calcular percentual
        totals = df_desq.groupby(dimension.value).size()
        analysis['total_campanha'] = analysis[dimension.value].map(totals)
        analysis['percentual'] = (analysis['quantidade'] / analysis['total_campanha'] * 100).round(1)
        
        # Ordenar
        analysis = analysis.sort_values(['total_campanha', 'quantidade'], ascending=[False, False])
        
        return analysis
    
    def get_trend_data(
        self,
        dimension: UTMDimension = UTMDimension.CAMPAIGN,
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Dados de tendência para gráfico de linha.
        
        Returns:
            DataFrame com dados diários por campanha
        """
        if self.df.empty or 'criado_em' not in self.df.columns:
            return pd.DataFrame()
        
        # Top N campanhas por volume
        top_campaigns = self.df[dimension.value].value_counts().head(top_n).index.tolist()
        
        df_filtered = self.df[self.df[dimension.value].isin(top_campaigns)].copy()
        df_filtered['data'] = pd.to_datetime(df_filtered['criado_em']).dt.date
        
        # Agrupar por data e campanha
        trend = df_filtered.groupby(['data', dimension.value]).size().reset_index(name='leads')
        
        return trend


# ========================================
# FUNÇÕES DE CONVENIÊNCIA
# ========================================

def create_marketing_analyzer(
    df_leads: pd.DataFrame,
    df_leads_anterior: Optional[pd.DataFrame] = None,
    demo_completed_statuses: Optional[List[str]] = None
) -> MarketingAnalyzer:
    """
    Factory function para criar MarketingAnalyzer.
    
    Args:
        df_leads: DataFrame com leads
        df_leads_anterior: DataFrame do período anterior
        demo_completed_statuses: Status de demo completada
    
    Returns:
        Instância configurada de MarketingAnalyzer
    """
    return MarketingAnalyzer(
        df_leads=df_leads,
        df_leads_anterior=df_leads_anterior,
        demo_completed_statuses=demo_completed_statuses
    )


def get_quick_insights(
    df_leads: pd.DataFrame,
    demo_completed_statuses: Optional[List[str]] = None
) -> List[str]:
    """
    Gera lista simples de insights como strings.
    
    Args:
        df_leads: DataFrame com leads
        demo_completed_statuses: Status de demo completada
    
    Returns:
        Lista de strings com insights
    """
    analyzer = MarketingAnalyzer(df_leads, demo_completed_statuses=demo_completed_statuses)
    insights = analyzer.generate_insights()
    
    return [f"{i.icon} **{i.title}**: {i.description}" for i in insights]
