# 📊 Guia de Estilo para Gráficos - ecosys AUTO Dashboard

Este documento define o padrão visual para todos os gráficos Plotly no dashboard.
**Siga estas diretrizes ao criar novos gráficos.**

---

## 🎨 Paleta de Cores

```python
from config import CHART_COLORS  # Sempre usar a paleta do módulo config

# Cores principais do tema
TEAL_PRIMARY = '#20B2AA'      # Cor principal (Light Sea Green)
DARK_BG = '#1a1f2e'           # Fundo escuro
CARD_BG = '#2d3748'           # Fundo de cards/hover
TEXT_LIGHT = '#ffffff'        # Texto principal
TEXT_MUTED = '#CBD5E0'        # Texto secundário
GRID_COLOR = 'rgba(255,255,255,0.1)'  # Linhas de grade
```

---

## 📈 Template Padrão - Gráfico de Linhas

```python
import plotly.express as px
from config import CHART_COLORS

# Criar gráfico
fig = px.line(
    df,
    x='data',
    y='valor',
    color='categoria',
    title='📈 Título do Gráfico',
    labels={'data': '', 'valor': '', 'categoria': ''},  # Labels vazios (usar título)
    markers=True,
    color_discrete_sequence=CHART_COLORS,
    category_orders={'categoria': ordem_categorias}  # Ordenar legenda por relevância
)

# Aplicar layout padrão
fig.update_layout(
    height=500,
    hovermode='x unified',
    plot_bgcolor='rgba(0,0,0,0)',      # Fundo transparente
    paper_bgcolor='rgba(0,0,0,0)',     # Fundo transparente
    legend=dict(
        orientation="h",               # Legenda horizontal
        yanchor="bottom",
        y=1.02,                        # Acima do gráfico
        xanchor="center",
        x=0.5,
        font=dict(size=14, color='#ffffff'),
        bgcolor='rgba(0,0,0,0)',
        itemsizing='constant'
    ),
    xaxis=dict(
        tickformat='%d/%m',            # Formato de data brasileiro
        tickangle=0,                   # Sem rotação
        tickfont=dict(size=12, color='#CBD5E0'),
        gridcolor='rgba(255,255,255,0.1)',
        showgrid=True,
        dtick='D1',                    # Um tick por dia (se aplicável)
        tickmode='auto',
        nticks=30                      # Máximo de ticks
    ),
    yaxis=dict(
        tickfont=dict(size=12, color='#CBD5E0'),
        gridcolor='rgba(255,255,255,0.1)',
        showgrid=True,
        zeroline=False
    ),
    margin=dict(l=20, r=20, t=60, b=40),
    hoverlabel=dict(
        bgcolor='#2d3748',
        font_size=14,
        font_family="Arial"
    )
)

# Estilizar linhas e marcadores
fig.update_traces(
    line=dict(width=2.5),
    marker=dict(size=8, line=dict(width=1, color='#1a1f2e')),
    hovertemplate='<b>%{y}</b> unidades<extra>%{fullData.name}</extra>'
)

# Renderizar
st.plotly_chart(fig, width='stretch')
```

---

## 📊 Template Padrão - Gráfico de Barras

```python
import plotly.express as px

fig = px.bar(
    df,
    x='categoria',
    y='valor',
    title='📊 Título do Gráfico',
    labels={'categoria': '', 'valor': ''},
    color='valor',
    color_continuous_scale='Blues',  # Ou 'Greens', 'Reds' conforme contexto
    text='valor'
)

fig.update_layout(
    height=400,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(
        tickfont=dict(size=12, color='#CBD5E0'),
        tickangle=-45,  # Rotação para labels longas
        gridcolor='rgba(255,255,255,0.1)'
    ),
    yaxis=dict(
        tickfont=dict(size=12, color='#CBD5E0'),
        gridcolor='rgba(255,255,255,0.1)',
        showgrid=True
    ),
    margin=dict(l=20, r=20, t=60, b=80),
    coloraxis_colorbar=dict(tickfont=dict(size=12)),
    showlegend=False
)

fig.update_traces(
    textposition='outside',
    textfont_size=14,
    marker_line_width=0
)

st.plotly_chart(fig, width='stretch')
```

---

## 📊 Template Padrão - Gráfico de Barras Horizontal

```python
fig = px.bar(
    df,
    y='categoria',
    x='valor',
    title='📊 Título do Gráfico',
    orientation='h',
    color='valor',
    color_continuous_scale='Blues',
    text='valor'
)

fig.update_layout(
    height=400,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    yaxis=dict(
        categoryorder='total descending',  # Ordenar por valor
        tickfont=dict(size=14, color='#CBD5E0')
    ),
    xaxis=dict(
        showticklabels=False,  # Esconder labels do eixo X
        gridcolor='rgba(255,255,255,0.1)'
    ),
    yaxis_title='',
    xaxis_title='',
    coloraxis_colorbar=dict(tickfont=dict(size=14))
)

fig.update_traces(
    textposition='outside',
    textfont_size=16
)

st.plotly_chart(fig, width='stretch')
```

---

## 🔄 Template Padrão - Gráfico de Funil

```python
fig = px.funnel(
    df,
    x='quantidade',
    y='etapa',
    title='🔄 Funil de Conversão',
    color='etapa',
    text='label',
    color_discrete_map={
        'Etapa1': '#4CAF50',  # Verde
        'Etapa2': '#FFA500',  # Laranja
        'Etapa3': '#4A9FFF'   # Azul
    }
)

fig.update_traces(
    textposition='outside',
    textfont_size=18,
    textfont=dict(family="Arial", color="white", weight="bold")
)

fig.update_yaxes(
    categoryorder='array',
    categoryarray=['Etapa3', 'Etapa2', 'Etapa1'],  # Ordem do funil
    tickfont=dict(size=18)
)

fig.update_layout(
    height=610,
    yaxis_title='',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, width='stretch')
```

---

## 📈 Template Padrão - Histograma

```python
fig = px.histogram(
    df,
    x='valor',
    nbins=20,
    title='📈 Distribuição de Valores',
    labels={'valor': 'Valor', 'count': 'Quantidade'},
    color_discrete_sequence=['#4A9FFF'],
    text_auto=True
)

fig.update_layout(
    height=400,
    showlegend=False,
    bargap=0.1,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(
        tickfont=dict(size=12, color='#CBD5E0'),
        gridcolor='rgba(255,255,255,0.1)'
    ),
    yaxis=dict(
        title_text='Quantidade',
        tickfont=dict(size=12, color='#CBD5E0'),
        showticklabels=False,
        gridcolor='rgba(255,255,255,0.1)'
    )
)

fig.update_traces(
    textposition='outside',
    textfont_size=14,
    marker_line_width=1.5
)

# Adicionar linha de referência (opcional)
fig.add_vline(
    x=valor_referencia,
    line_dash="dash",
    line_color="red",
    annotation_text="Limite"
)

st.plotly_chart(fig, width='stretch')
```

---

## 🔵 Template Padrão - Gráfico de Dispersão

```python
fig = px.scatter(
    df,
    x='eixo_x',
    y='eixo_y',
    size='tamanho',
    color='categoria',
    title='🔵 Análise de Dispersão',
    labels={'eixo_x': 'Label X', 'eixo_y': 'Label Y'},
    hover_data=['info1', 'info2', 'info3']
)

fig.update_layout(
    height=400,
    showlegend=True,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(
        tickfont=dict(size=16, color='#CBD5E0'),
        gridcolor='rgba(255,255,255,0.1)'
    ),
    yaxis=dict(
        tickfont=dict(size=16, color='#CBD5E0'),
        gridcolor='rgba(255,255,255,0.1)'
    )
)

st.plotly_chart(fig, width='stretch')
```

---

## ✅ Checklist para Novos Gráficos

- [ ] Usar `from config import CHART_COLORS` para paleta de cores
- [ ] Fundo transparente: `plot_bgcolor='rgba(0,0,0,0)'`
- [ ] Fundo transparente: `paper_bgcolor='rgba(0,0,0,0)'`
- [ ] Grid sutil: `gridcolor='rgba(255,255,255,0.1)'`
- [ ] Fonte dos ticks: `tickfont=dict(size=12, color='#CBD5E0')`
- [ ] Hover label: `hoverlabel=dict(bgcolor='#2d3748', font_size=14)`
- [ ] **Hovertemplate**: Tooltip informativo com emojis
- [ ] Legenda horizontal acima do gráfico (quando aplicável)
- [ ] Usar `width='stretch'` ao invés de `use_container_width=True`
- [ ] Títulos com emoji relevante
- [ ] Labels do eixo vazios quando redundantes com título

---

## 🔍 Tooltips (Hovertemplates)

Os hovertemplates permitem criar tooltips personalizadas e informativas para cada gráfico.

### Estrutura Básica

```python
# Formato geral
hovertemplate='<b>%{x}</b><br>📊 Valor: %{y:,.0f}<extra></extra>'
```

**Elementos importantes:**
- `<b>%{x}</b>` - Valor do eixo X em negrito
- `<br>` - Quebra de linha
- `%{y:,.0f}` - Valor do eixo Y formatado (com separador de milhar)
- `<extra></extra>` - Remove a caixa secundária com nome da série

### Formatação de Valores

| Formato | Resultado | Uso |
|---------|-----------|-----|
| `%{y:,.0f}` | 1,234 | Inteiros com separador |
| `%{y:.1f}` | 12.3 | Uma casa decimal |
| `%{y:.1f}%` | 12.3% | Percentual |
| `%{y:,.2f}` | 1,234.56 | Duas casas decimais |

### Usando Customdata

Para exibir informações adicionais além de x e y:

```python
# Adicionar customdata ao gráfico
fig = px.bar(
    df,
    x='categoria',
    y='valor',
    custom_data=['info_extra', 'quantidade', 'taxa']  # Via px
)

# Ou com fig.update_traces:
fig.update_traces(
    customdata=df[['info_extra', 'quantidade', 'taxa']].values,
    hovertemplate='<b>%{x}</b><br>' +
                  '📊 Valor: %{y:,.0f}<br>' +
                  '📈 Quantidade: %{customdata[1]:,.0f}<br>' +
                  '🎯 Taxa: %{customdata[2]:.1f}%<extra></extra>'
)
```

### Exemplos por Tipo de Gráfico

#### 📊 Barras Verticais
```python
hovertemplate='<b>%{x}</b><br>💰 Vendas: %{y:,.0f}<extra></extra>'
```

#### 📊 Barras Horizontais
```python
hovertemplate='<b>%{y}</b><br>📊 Quantidade: %{x:,.0f}<extra></extra>'
```

#### 📈 Linhas
```python
# Com hovermode='x unified'
hovertemplate='<b>%{y}</b> discagens<extra>%{fullData.name}</extra>'
```

#### 🥧 Pizza
```python
hovertemplate='<b>%{label}</b><br>💰 Valor: %{value:,.0f}<br>📊 Percentual: %{percent}<extra></extra>'
```

#### 📊 Histograma
```python
hovertemplate='<b>%{x:.1f} min</b><br>📞 Quantidade: %{y:,.0f}<extra></extra>'
```

#### 🔵 Scatter (Dispersão)
```python
hovertemplate='<b>%{meta}</b><br>' +
              '📞 X: %{x:,.0f}<br>' +
              '🎯 Y: %{y:.1f}%<br>' +
              '📊 Info: %{customdata[0]}<extra></extra>'
```

#### 🔄 Funil
```python
hovertemplate='<b>%{y}</b><br>📊 Quantidade: %{x:,.0f}<extra></extra>'
```

### Emojis Recomendados

| Emoji | Contexto |
|-------|----------|
| 📊 | Quantidade, valor genérico |
| 📈 | Tendência positiva, crescimento |
| 📉 | Tendência negativa, taxa de no-show |
| 💰 | Vendas, valores monetários |
| 🎯 | Taxa, meta, conversão |
| 📞 | Ligações, chamadas |
| 👤 | Vendedor, usuário |
| ⏱️ | Tempo, duração |
| ✅ | Efetivas, sucesso |
| ❌ | Desqualificação, erro |
| ⚠️ | Alerta, atenção |
| 📅 | Data, dia da semana |

### Exemplos Reais do Projeto

```python
# Demos por Vendedor
hovertemplate='<b>%{x}</b><br>📊 Demos: %{y}<extra></extra>'

# Taxa de No-show (com customdata)
customdata=df[['total_demos_agendadas', 'total_noshows']].values,
hovertemplate='<b>%{x}</b><br>📉 Taxa: %{y:.1f}%<br>📊 Total Demos: %{customdata[0]}<br>❌ No-shows: %{customdata[1]}<extra></extra>'

# Ranking de Vendedores
hovertemplate='<b>%{x}</b><br>✅ Ligações Efetivas: %{y:,.0f}<extra></extra>'

# Vendas por Dia da Semana
hovertemplate='<b>%{x}</b><br>📅 Vendas: %{y:,.0f}<extra></extra>'

# Taxa de Desqualificação
hovertemplate='<b>%{y}</b><br>⚠️ Taxa de Desqualificação: %{x:.1f}%<extra></extra>'
```

---

## 🚫 O que NÃO fazer

```python
# ❌ ERRADO - Não usar use_container_width
st.plotly_chart(fig, use_container_width=True)

# ✅ CORRETO
st.plotly_chart(fig, width='stretch')

# ❌ ERRADO - Não usar fundo branco/colorido
fig.update_layout(plot_bgcolor='white')

# ✅ CORRETO
fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')

# ❌ ERRADO - Não usar cores hardcoded
color_discrete_sequence=['#ff0000', '#00ff00', '#0000ff']

# ✅ CORRETO
from config import CHART_COLORS
color_discrete_sequence=CHART_COLORS
```

---

## 📝 Notas Adicionais

1. **Datas**: Sempre usar formato brasileiro `%d/%m` ou `%d/%m/%Y`
2. **Números**: Usar separador de milhar com ponto (brasileiro)
3. **Altura**: Padrão 400-500px, ajustar conforme necessidade
4. **Responsividade**: Sempre usar `width='stretch'`
5. **Acessibilidade**: Usar cores contrastantes e tamanhos de fonte legíveis

---

## 🎯 Boas Práticas de UX em Gráficos

### Hierarquia Visual
- Títulos com emoji para identificação rápida
- Valores importantes em **negrito** nas tooltips
- Cores consistentes para métricas similares em todo o dashboard

### Interatividade
- Sempre configurar `hoverlabel` com fundo escuro (`#2d3748`)
- Usar `hovermode='x unified'` em gráficos de linha temporais
- Tooltips devem mostrar contexto, não apenas o valor

### Performance
- Limitar gráficos a 20-30 pontos de dados quando possível
- Usar `nbins=20` como padrão para histogramas
- Evitar animações em dashboards com muitos gráficos

### Consistência
- Mesma métrica = mesma cor em todos os gráficos
- Mesma escala de cores por contexto:
  - `Blues` → Volumes, quantidades neutras
  - `Greens` → Taxas positivas, conversões, sucesso
  - `Reds` → Alertas, desqualificações, problemas
  - `Oranges` → Intermediários, avisos

---

*Última atualização: Dezembro 2025*
