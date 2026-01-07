# Exemplos Práticos: Sistema de Deduplicação

## Cenário 1: Primeira Execução (08h BRT)

### Estado Inicial
```
.news_history.json: NÃO EXISTE
```

### Execução
```bash
python app.py
```

### Console
```
--- 🚀 Iniciando v8.0 (Com Deduplicação de Estado) ---
📋 Histórico carregado: 0 notícias já processadas

📰 Lula assina decreto sobre reforma tributária
  [Busca] 'Lula assina decreto'...
  [Extração] Baixando conteúdo...
  -> Sucesso!

📰 BC aumenta taxa Selic para 11,5% a.a.
  [Busca] 'BC aumenta taxa'...
  [Extração] Baixando conteúdo...
  -> Sucesso!

📰 Mercado fecha em alta
  [Busca] 'Mercado fecha'...
  [Extração] Baixando conteúdo...
  -> Sucesso!

📊 Resumo: 3 notícias novas, 0 duplicatas
✅ Relatório enviado com sucesso!
```

### Arquivo Criado (`.news_history.json`)
```json
{
  "a1b2c3d4e5f6g7h8i9j0k1l2": {
    "title": "Lula assina decreto sobre reforma tributária",
    "url": "https://g1.globo.com/politica/noticia/...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "b2c3d4e5f6g7h8i9j0k1l2m3": {
    "title": "BC aumenta taxa Selic para 11,5% a.a.",
    "url": "https://www.bcb.gov.br/...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "c3d4e5f6g7h8i9j0k1l2m3n4": {
    "title": "Mercado fecha em alta",
    "url": "https://www1.folha.uol.com.br/...",
    "timestamp": "2026-01-07T08:15:00"
  }
}
```

---

## Cenário 2: Segunda Execução (12h BRT - RSS não atualizou 100%)

### Estado Inicial
```
.news_history.json: 3 entradas (da execução 08h)
```

### Feed RSS Contém
- Notícia A (já enviada 08h)
- Notícia B (já enviada 08h)
- Notícia C (já enviada 08h)
- **Notícia D (NOVA!)**

### Execução
```bash
python app.py
```

### Console
```
--- 🚀 Iniciando v8.0 (Com Deduplicação de Estado) ---
📋 Histórico carregado: 3 notícias já processadas

📰 Lula assina decreto sobre reforma tributária
   -> Duplicata detectada (pulado)

📰 BC aumenta taxa Selic para 11,5% a.a.
   -> Duplicata detectada (pulado)

📰 Mercado fecha em alta
   -> Duplicata detectada (pulado)

📰 Reforma tributária aprovada com apoio do Congresso
  [Busca] 'Reforma tributária aprovada'...
  [Extração] Baixando conteúdo...
  -> Sucesso!

📊 Resumo: 1 notícía nova, 3 duplicatas
✅ Relatório enviado com sucesso!
```

### Arquivo Atualizado (`.news_history.json`)
```json
{
  "a1b2c3d4e5f6g7h8i9j0k1l2": {
    "title": "Lula assina decreto sobre reforma tributária",
    "url": "https://g1.globo.com/politica/noticia/...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "b2c3d4e5f6g7h8i9j0k1l2m3": {
    "title": "BC aumenta taxa Selic para 11,5% a.a.",
    "url": "https://www.bcb.gov.br/...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "c3d4e5f6g7h8i9j0k1l2m3n4": {
    "title": "Mercado fecha em alta",
    "url": "https://www1.folha.uol.com.br/...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "d4e5f6g7h8i9j0k1l2m3n4o5": {
    "title": "Reforma tributária aprovada com apoio do Congresso",
    "url": "https://www2.camara.leg.br/...",
    "timestamp": "2026-01-07T12:45:00"  ← NOVA ENTRADA
  }
}
```

### Telegram Recebido
- ❌ **Executar 08h**: 3 notícias
- ✅ **Executar 12h**: 1 notícia (não repetiu A, B, C)
- **Total dia**: 4 notícias únicas (CORRETO!)

---

## Cenário 3: Terceira Execução (21h BRT)

### Estado Inicial
```
.news_history.json: 4 entradas (de 08h + 12h)
```

### Feed RSS Contém
- Notícia A (08h)
- Notícia B (08h)
- Notícia C (08h)
- Notícia D (12h)
- **Notícia E (NOVA!)**
- **Notícia F (NOVA!)**

### Execução
```bash
python app.py
```

### Console
```
--- 🚀 Iniciando v8.0 (Com Deduplicação de Estado) ---
📋 Histórico carregado: 4 notícias já processadas

📰 Lula assina decreto sobre reforma tributária
   -> Duplicata detectada (pulado)

📰 BC aumenta taxa Selic para 11,5% a.a.
   -> Duplicata detectada (pulado)

📰 Mercado fecha em alta
   -> Duplicata detectada (pulado)

📰 Reforma tributária aprovada com apoio do Congresso
   -> Duplicata detectada (pulado)

📰 Imposto sobre renda deve ser reduzido em 2026
  [Busca] 'Imposto sobre renda'...
  [Extração] Baixando conteúdo...
  -> Sucesso!

📰 Dólar fecha o dia em queda de 2%
  [Busca] 'Dólar fecha'...
  [Extração] Baixando conteúdo...
  -> Sucesso!

📊 Resumo: 2 notícias novas, 4 duplicatas
✅ Relatório enviado com sucesso!
```

### Arquivo Atualizado (`.news_history.json`)
```json
{
  "a1b2c3d4e5f6g7h8i9j0k1l2": {
    "title": "Lula assina decreto sobre reforma tributária",
    "url": "...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "b2c3d4e5f6g7h8i9j0k1l2m3": {
    "title": "BC aumenta taxa Selic para 11,5% a.a.",
    "url": "...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "c3d4e5f6g7h8i9j0k1l2m3n4": {
    "title": "Mercado fecha em alta",
    "url": "...",
    "timestamp": "2026-01-07T08:15:00"
  },
  "d4e5f6g7h8i9j0k1l2m3n4o5": {
    "title": "Reforma tributária aprovada com apoio do Congresso",
    "url": "...",
    "timestamp": "2026-01-07T12:45:00"
  },
  "e5f6g7h8i9j0k1l2m3n4o5p6": {
    "title": "Imposto sobre renda deve ser reduzido em 2026",
    "url": "...",
    "timestamp": "2026-01-07T21:30:00"  ← NOVA
  },
  "f6g7h8i9j0k1l2m3n4o5p6q7": {
    "title": "Dólar fecha o dia em queda de 2%",
    "url": "...",
    "timestamp": "2026-01-07T21:30:00"  ← NOVA
  }
}
```

### Resumo do Dia
```
Execução 08h:  3 notícias únicas → Telegram
Execução 12h:  1 notícia nova   → Telegram
Execução 21h:  2 notícias novas → Telegram
─────────────────────────────────────────
TOTAL:         6 notícias únicas → Telegram
               0 duplicatas     → Telegram
```

---

## Cenário 4: Limpeza de Histórico Antigo (Dia 8)

### Estado em 08/01 @ 08h
```json
{
  "hash_01": { "timestamp": "2026-01-01T08:00:00" },  ← 7 dias
  "hash_02": { "timestamp": "2026-01-02T08:00:00" },  ← 6 dias
  "hash_03": { "timestamp": "2026-01-07T12:00:00" },  ← 0 dias (hoje)
  "hash_04": { "timestamp": "2026-01-07T21:00:00" }   ← 0 dias (hoje)
}
```

### Execução
```bash
python app.py
```

### Processamento Interno
```python
cutoff_date = 2026-01-01T05:00:00  # 7 dias atrás
cleaned = clean_old_history(history)
```

### Resultado
```json
{
  "hash_02": { "timestamp": "2026-01-02T08:00:00" },  ← Mantém
  "hash_03": { "timestamp": "2026-01-07T12:00:00" },  ← Mantém
  "hash_04": { "timestamp": "2026-01-07T21:00:00" }   ← Mantém
}
```

**Ação**: `hash_01` foi removido (8+ dias) durante `clean_old_history()`

---

## Cenário 5: Título Levemente Modificado

### Entrada RSS
- Título: `"Lula assina novo decreto sobre reforma tributária"`
- URL: `https://g1.globo.com/politica/noticia/123`

### Histórico Existente
```json
{
  "hash1": {
    "title": "Lula assina decreto sobre reforma tributária",
    "url": "https://g1.globo.com/politica/noticia/123",
    "timestamp": "2026-01-07T08:00:00"
  }
}
```

### Verificação
```python
title_novo = "Lula assina novo decreto sobre reforma tributária"
url = "https://g1.globo.com/politica/noticia/123"

hash_novo = get_news_hash(title_novo, url)
# hash_novo = MD5("lula assina novo decreto sobre reforma tributária|https://...")

hash_old = "hash1"  # MD5("lula assina decreto sobre reforma tributária|https://...")

hash_novo == hash_old?  # NÃO (título diferentes)
```

### Resultado
```
📰 Lula assina novo decreto sobre reforma tributária
  [Busca] 'Lula assina novo decreto'...
  [Extração] Baixando conteúdo...
  -> Sucesso!

📊 Resumo: 1 notícia nova, 0 duplicatas
```

**Observação**: Isso é CORRETO! Título modificado = notícia potencialmente atualizada.

---

## Cenário 6: Reset do Histórico

### Problema
Histórico corrompido ou você quer começar do zero.

### Solução
```bash
# Opção 1: Deletar arquivo
rm .news_history.json

# Opção 2: Limpar conteúdo
echo '{}' > .news_history.json

# Próxima execução
python app.py
# Criará novo histórico vazio
```

### Risco
⚠️ **Após reset**: Próxima execução pode reenviar notícias antigas se o RSS ainda as contiver.

**Mitigação**: Execute em horário com poucos usuários, ou documente o evento.

---

## Monitoramento (Sugerido)

### Log Recomendado (Adicionar ao app.py)
```python
# Após save_history()
print(f"📊 Histórico agora contém: {len(history)} notícias")
print(f"   Período: {oldest_timestamp} → {newest_timestamp}")
```

### Métricas para Acompanhar
1. **Taxa de duplicatas**: Deve estar próximo a 0% após estabilização
2. **Tamanho do arquivo**: Deve crescer ~1 KB por dia
3. **Notícias únicas/dia**: Deve estar consistente

---

## Troubleshooting

### P: Vi muitas duplicatas hoje (10+)?
**R**: RSS quebrou ou notícias antigas reapareceram.
- Verifique feed com `feedparser.parse(RSS_URL)`
- Considere aumentar `HISTORY_DAYS`

### P: Histórico cresce muito rápido?
**R**: Possível corrupção ou duplicação acidental.
```python
# Verificar
python -c "import json; h = json.load(open('.news_history.json')); print(f'{len(h)} entradas')"
```

### P: Arquivo `.news_history.json` sumiu!
**R**: Provavelmente foi deletado ou GitHub Actions resetou.
- Sistema regenera automaticamente na próxima execução
- Primeira execução após reset pode reenviar 3-5 notícias antigas

