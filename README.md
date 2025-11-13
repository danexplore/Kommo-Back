# Painel de Acompanhamento de Leads - Kommo

Painel desenvolvido em Streamlit para acompanhamento e gestão de leads do CRM Kommo, conectado diretamente ao banco de dados Supabase/PostgreSQL.

## 📋 Descrição

Este painel resolve a lacuna no acompanhamento de leads, fornecendo visualizações claras e acionáveis sobre o status dos leads, especialmente aqueles que passam por etapas críticas sem atualização adequada.

## 🎯 Funcionalidades

### 🚨 Módulo 1: Leads que Exigem Atenção
- Identifica leads com demo vencida não atualizados
- Mostra leads que não foram marcados como no-show ou venda
- Exibe leads que não estão em status pós-demo apropriado
- Links diretos para o Kommo

### 📅 Módulo 2: Resumo Diário da Equipe
- Visão agregada das atividades por dia
- Métricas: Novos Leads, Agendamentos, Demos, No-shows, Demos Realizadas
- Linha de totais para análise geral
- Ordenação por data (mais recente primeiro)

### 🔍 Módulo 3: Acompanhamento Detalhado
- Tabela completa e pesquisável de todos os leads
- Filtro de busca por nome do lead
- Visualização de todas as datas importantes
- Links clicáveis para o Kommo

### ⚙️ Filtros Globais
- **Período**: Seleção de data inicial e final (padrão: últimos 30 dias)
- **Vendedores**: Seleção múltipla de vendedores (padrão: todos)
- Atualização manual dos dados

## 🏗️ Arquitetura

- **Frontend**: Streamlit
- **Análise de Dados**: Pandas
- **Banco de Dados**: PostgreSQL (Supabase)
- **Cache**: Atualização automática a cada 30 minutos

## 📊 Modelo de Dados

### View Principal: `kommo_leads_statistics`
- `id`: ID único do lead
- `lead_name`: Nome do lead
- `vendedor`: Vendedor responsável
- `status_id` / `status`: Status atual
- `pipeline`: Funil do lead
- `criado_em`: Data de criação
- `data_agendamento`: Data do agendamento
- `data_demo`: Data da demonstração
- `data_noshow`: Data do no-show
- `data_venda`: Data da venda

### Tabela de Apoio: `kommo_users`
- `user_name`: Nome do vendedor
- `kommo_user_id`: ID do usuário no Kommo

## 🚀 Configuração e Deploy

### 1. Variáveis de Ambiente

Crie um arquivo `.env` baseado no `.env.example`:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-aqui
```

### 2. Instalação Local

```powershell
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py
```

Acesse: `http://localhost:8501`

### 3. Deploy na Vercel

```powershell
# Configurar variáveis de ambiente
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# Deploy
vercel --prod
```

## ⚙️ Configurações Importantes

### Status Pós-Demo

Lista de status que indicam demo realizada (definida no código):
- Demonstração Realizada
- Lead Quente
- Venda Ganha
- Em Negociação

**⚠️ CRÍTICO**: Validar esta lista com o gestor de vendas.

### Performance

- **Cache de dados**: 30 minutos
- **Cache de vendedores**: 12 horas
- Queries otimizadas com filtros no banco
- Botão manual de atualização disponível

## 📦 Estrutura do Projeto

```
├── app.py                    # Aplicação principal
├── api/
│   └── main.py              # Entry point para Vercel
├── .streamlit/
│   └── config.toml          # Configurações Streamlit
├── vercel.json              # Configuração Vercel
├── requirements.txt         # Dependências
├── .env.example             # Exemplo de variáveis
├── .gitignore               # Arquivos ignorados
└── README.md
```

## 👥 Personas

### Vendedor
- Acompanhamento diário da carteira
- Identificação rápida de leads que precisam de ação
- Follow-up pós-demo

### Gestor de Vendas
- Performance agregada da equipe
- Filtro por vendedor individual
- Auditoria do uso do CRM
- Identificação de gargalos no funil

## 🔐 Segurança

- Painel sem autenticação individual (acesso único)
- Proteger com firewall/VPN em produção
- Não commitar arquivo `.env` com credenciais reais

## 📝 Regras de Negócio

### Leads que Exigem Atenção

Um lead aparece nesta seção quando **TODAS** as condições são verdadeiras:
1. `data_demo` < HOJE (demo já passou)
2. `data_noshow` ESTÁ NULO (não marcado como no-show)
3. `data_venda` ESTÁ NULO (não marcado como venda)
4. `status` NÃO está na lista de status pós-demo

## 🛠️ Tecnologias

- Python 3.9+
- Streamlit 1.29.0
- Pandas 2.1.3
- Supabase 2.3.0
- PostgreSQL

## 📅 Data do PRD

13 de novembro de 2025
