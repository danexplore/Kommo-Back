"""
EXEMPLO DE USO DOS NOVOS MÓDULOS
================================

Este arquivo demonstra como usar os módulos refatorados.
A estrutura foi organizada da seguinte forma:

kommo-back/
├── app.py                    # Entry point principal (atual)
├── config/
│   ├── __init__.py          # Exporta todas as configs
│   ├── settings.py          # Constantes, status, cores, TTLs
│   └── styles.py            # CSS e funções de estilo
├── services/
│   ├── __init__.py          # Exporta todos os serviços
│   ├── supabase_service.py  # Conexão e queries Supabase
│   └── gemini_service.py    # IA e chat
├── core/
│   ├── __init__.py          # Exporta lógica de negócio
│   ├── metrics.py           # Cálculos de métricas
│   └── helpers.py           # Funções auxiliares
├── components/
│   ├── __init__.py          # Exporta componentes
│   ├── metrics.py           # Cards e métricas visuais
│   ├── charts.py            # Gráficos Plotly
│   └── tables.py            # Tabelas formatadas
└── utils/
    ├── __init__.py          # Exporta utilitários
    ├── formatters.py        # Formatação de dados
    └── validators.py        # Validações

COMO USAR:
"""

# ============================================
# EXEMPLO 1: Importando configurações
# ============================================
from config import (
    DEMO_COMPLETED_STATUSES,
    FUNNEL_CLOSED_STATUSES,
    COLORS,
    CHART_COLORS,
    DIAS_PT,
    META_CONVERSAO_EFETIVAS,
    get_main_css,
)

# Usar constantes
print(f"Status de demo completa: {DEMO_COMPLETED_STATUSES}")
print(f"Cor primária: {COLORS['primary']}")


# ============================================
# EXEMPLO 2: Usando serviços de dados
# ============================================
from datetime import datetime
from services import (
    get_leads_data,
    get_chamadas_vendedores,
    gerar_insights_ia,
)

# Buscar dados
data_inicio = datetime(2025, 11, 1)
data_fim = datetime(2025, 11, 26)

# df_leads = get_leads_data(data_inicio, data_fim)
# df_chamadas = get_chamadas_vendedores(data_inicio, data_fim)


# ============================================
# EXEMPLO 3: Calculando métricas
# ============================================
from core import (
    calcular_demos_realizadas,
    calcular_metricas_periodo,
    calcular_metricas_chamadas,
    generate_kommo_link,
)

# Calcular métricas do período
# metricas = calcular_metricas_periodo(df_leads, data_inicio, data_fim)
# print(f"Total de leads: {metricas['total_leads']}")
# print(f"Taxa de conversão: {metricas['taxa_conversao']:.1f}%")

# Gerar link do Kommo
link = generate_kommo_link(12345)
print(f"Link do lead: {link}")


# ============================================
# EXEMPLO 4: Usando utilitários
# ============================================
from utils import (
    format_currency,
    format_percentage,
    format_duration,
    safe_divide,
    validate_date_range,
)

# Formatar valores
print(format_currency(1500.50))         # R$ 1.500,50
print(format_percentage(85.5))          # 85.5%
print(format_duration(125))             # 2:05
print(safe_divide(10, 0, default=0))    # 0 (sem erro!)


# ============================================
# EXEMPLO 5: Criando componentes visuais
# ============================================
import streamlit as st
from components import (
    metric_with_comparison,
    progress_metric,
    create_line_chart,
    styled_dataframe,
)

# Em uma app Streamlit:
# metric_with_comparison("Total Leads", 150, 120, help_text="Leads no período")
# progress_metric("Meta Efetivas", current=45, target=50)


# ============================================
# BENEFÍCIOS DA NOVA ESTRUTURA
# ============================================
"""
1. MANUTENIBILIDADE
   - Código organizado por responsabilidade
   - Fácil encontrar e modificar funcionalidades

2. REUTILIZAÇÃO
   - Funções podem ser usadas em diferentes partes
   - Componentes padronizados

3. TESTABILIDADE
   - Funções isoladas são fáceis de testar
   - Mocking simplificado

4. TIPAGEM
   - Type hints em todas as funções
   - Melhor autocomplete e detecção de erros

5. CONSISTÊNCIA
   - Cores, estilos e status centralizados
   - Mudanças em um lugar afetam todo o app
"""

if __name__ == "__main__":
    print("✅ Módulos carregados com sucesso!")
    print("\nEstrutura criada:")
    print("  - config/: Configurações e estilos")
    print("  - services/: Conexões com APIs")
    print("  - core/: Lógica de negócio")
    print("  - components/: Componentes visuais")
    print("  - utils/: Utilitários gerais")
