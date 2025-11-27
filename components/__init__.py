"""
Módulo de componentes do Dashboard Kommo
"""
from components.metrics import (
    metric_with_comparison,
    info_card,
    progress_metric,
    status_badge,
)

from components.charts import (
    create_line_chart,
    create_bar_chart,
    create_funnel_chart,
    create_histogram,
    create_scatter_chart,
)

from components.tables import (
    styled_dataframe,
    paginated_dataframe,
    ranking_table,
    summary_table,
)

from components.marketing_dashboard import (
    render_marketing_dashboard,
    render_marketing_summary_cards,
    render_insights_cards,
    render_campaign_performance_chart,
    render_conversion_funnel_chart,
    render_desqualification_analysis,
    render_period_comparison,
    render_campaign_ranking,
    render_metrics_table,
    render_trend_chart,
)

__all__ = [
    # Metrics
    'metric_with_comparison',
    'info_card',
    'progress_metric',
    'status_badge',
    # Charts
    'create_line_chart',
    'create_bar_chart',
    'create_funnel_chart',
    'create_histogram',
    'create_scatter_chart',
    # Tables
    'styled_dataframe',
    'paginated_dataframe',
    'ranking_table',
    'summary_table',
    # Marketing Dashboard
    'render_marketing_dashboard',
    'render_marketing_summary_cards',
    'render_insights_cards',
    'render_campaign_performance_chart',
    'render_conversion_funnel_chart',
    'render_desqualification_analysis',
    'render_period_comparison',
    'render_campaign_ranking',
    'render_metrics_table',
    'render_trend_chart',
]
