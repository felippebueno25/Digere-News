# Digere-News - AI Copilot Instructions

## Visão Geral do Projeto
Este é um **bot automatizado de agregação de notícias** que:
1. Lê RSS do Google News (Brasil)
2. Resolve URLs por busca no DuckDuckGo (bypassa redirecionador)
3. Extrai conteúdo com `newspaper3k`
4. Resume via Gemini AI (google-generativeai)
5. Envia briefing ao Telegram
6. Roda automaticamente via GitHub Actions (3x/dia: 8h, 12h, 21h BRT)

**Arquitetura**: Script Python single-file (`app.py`) sem dependências de banco/servidor.

## Configuração do Ambiente

### Variáveis de Ambiente Obrigatórias
```bash
GEMINI_API_KEY=<chave-da-api-gemini>
TELEGRAM_TOKEN=<token-do-bot>
TELEGRAM_CHAT_ID=<id-do-chat>
```

No GitHub Actions, configure via **Settings → Secrets and variables → Actions**.

### Execução Local
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

## Fluxo de Dados Crítico

```
RSS Feed → DuckDuckGo (resolve URL limpa) → newspaper3k (extrai texto) 
→ Gemini (resume) → Telegram API (envia) + briefing_diario.md (salva)
```

### Tratamento de Erros Especial
- **Paywall detectado**: Conteúdo insuficiente (<300 chars) → link alternativo via smry.ai
- **Falha DuckDuckGo**: Pula notícia silenciosamente
- **Erro Gemini**: Retorna mensagem de erro mas continua processamento
- **Telegram limite**: Divide mensagens em blocos de 4000 caracteres

## Padrões e Convenções

### Modelo de IA
Sempre use `gemini-2.5-flash` (definido no código) - não trocar para modelos caros sem justificativa.

### Rate Limiting
- `time.sleep(1)` entre requisições de notícias (evita blocks do DuckDuckGo)
- Limite de `MAX_ITEMS = 5` notícias por execução (reduz custo API Gemini)

### Formato de Saída
- Briefing em Markdown com emojis (🔹, 🗞️)
- Timestamp em formato BR: `%d/%m %H:%M`
- Parse mode do Telegram: `Markdown` (não HTML)

## Debugging e Testes

### Testar Localmente
```bash
# Com vars de ambiente
export GEMINI_API_KEY=xxx
export TELEGRAM_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
python app.py
```

### Testar Sem Telegram
Comente/remova as vars de ambiente do Telegram - o script apenas salva `briefing_diario.md` localmente.

### Log de Execução
- Console mostra: `[1/5] Processando: <título>`
- Arquivo `briefing_diario.md` preserva resultado da última execução

## GitHub Actions

- **Workflow**: [.github/workflows/daily_news.yml](.github/workflows/daily_news.yml)
- **Horários**: 11:00, 15:00, 00:00 UTC (expressão cron)
- **Teste manual**: Botão "Run workflow" no GitHub
- **Artefatos**: Cada execução salva `briefing-<run_id>` por 90 dias

## Integrações Externas

### APIs Usadas
- **Google News RSS**: Sem autenticação, topic=Brasil (query params no URL)
- **DuckDuckGo Search**: Biblioteca `ddgs` (sem API key)
- **Gemini AI**: SDK oficial `google.generativeai` (requer `GEMINI_API_KEY`)
- **Telegram Bot**: REST API direta via `requests` (não usa biblioteca)

### Dependências Críticas
- `newspaper3k` + `lxml_html_clean`: Parsing de HTML (requer ambos)
- `feedparser`: Parse de XML/RSS
- `duckduckgo-search`: Alias `ddgs` (não confundir com pacote `duckduckgo`)

## Convenções de Código
- Funções auxiliares antes de `main()` (ordem: busca → extração → IA → envio)
- Seções delimitadas por comentários `# ===== NOME =====`
- Erros capturados com `try/except` mas não interrompem loop principal
- Encoding UTF-8 explícito em I/O de arquivos
