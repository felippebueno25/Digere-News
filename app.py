import os
import re
import time
import json
import hashlib
from datetime import datetime, timedelta, timezone
import feedparser
from google import genai
from ddgs import DDGS
import requests # Para envio ao Telegram
from curl_cffi import requests as crequests # Bypass de bloqueios (UOL/Globo)
import trafilatura

# ================= CONFIGURAÇÕES =================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
MAX_ITEMS = 20 # Limite de notícias por execução
HISTORY_FILE = ".news_history.json" # Histórico de notícias já enviadas
HISTORY_DAYS = 7 # Manter histórico por 7 dias 

# ================= FUNÇÕES DE APOIO =================

def get_br_time():
    """Hora atual de Brasília (UTC-3)."""
    return (datetime.now(timezone.utc) - timedelta(hours=3)).strftime('%d/%m %H:%M')

def load_history():
    """Carrega o histórico de notícias já processadas."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_history(history):
    """Salva o histórico de notícias processadas."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")

def get_news_hash(title, url):
    """
    Gera um hash único para uma notícia baseado em título + URL.
    Isso evita duplicatas mesmo se o título mudar ligeiramente.
    """
    key = f"{title.lower().strip()}|{url.lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()

def is_news_duplicate(title, url, history):
    """
    Verifica se a notícia já foi processada.
    Retorna True se é duplicata, False se é nova.
    """
    news_hash = get_news_hash(title, url)
    return news_hash in history

def clean_old_history(history):
    """
    Remove notícias do histórico que têm mais de HISTORY_DAYS dias.
    Mantém o arquivo controlado.
    """
    cutoff_date = (datetime.now(timezone.utc) - timedelta(hours=3, days=HISTORY_DAYS)).isoformat()
    
    cleaned = {}
    for hash_id, entry in history.items():
        if entry.get('timestamp', '') > cutoff_date:
            cleaned[hash_id] = entry
    
    return cleaned

def resolve_url_ddg(title):
    """
    Busca a URL original no DuckDuckGo.
    """
    clean_title = title.split(" - ")[0] if " - " in title else title
    print(f"  [Busca] '{clean_title}'...")

    for attempt in range(1, 3):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(clean_title, region='br-pt', max_results=1))
                if results:
                    return results[0]['href']
        except Exception:
            time.sleep(1) 
    return None

def extract_content_robust(url):
    """
    Usa 'curl_cffi' (Chrome 120) para baixar o HTML e 'trafilatura' para extrair o texto.
    """
    if not url or "news.google.com" in url: return None
    
    print("  [Extração] Baixando conteúdo...")
    try:
        # Impersonate Chrome resolve o erro 403 do UOL
        response = crequests.get(url, impersonate="chrome120", timeout=15)
        
        if response.status_code == 200:
            text = trafilatura.extract(response.content, include_comments=False, include_tables=False)
            if text and len(text) > 200:
                print("  -> Sucesso!")
                return text
            else:
                print("  -> Texto curto/vazio.")
        else:
            print(f"  -> Bloqueado (Status {response.status_code})")
            
    except Exception as e:
        print(f"  -> Erro no download: {e}")
    return None

def generate_final_report(news_data):
    """
    Envia TODAS as notícias para o Gemini de uma vez só, 
    otimizado para economia de tokens.
    """
    if not GEMINI_KEY: return "⚠️ Erro: API Key não configurada."
    if not news_data: return "⚠️ Nenhuma notícia foi coletada."

    print(f"\n[IA] Gerando relatório consolidado ({len(news_data)} notícias)...")

    # INSTRUÇÃO DO SISTEMA (Compactada)
    # Define o formato de saída desejado e a persona.
    system_instruction = """Persona: Você é um Analista de Inteligência Sênior com foco em Análise de Discurso e Contexto Histórico. Sua missão não é apenas informar, mas "desarmar" a notícia. Você escreve para um cidadão exigente que despreza o sensacionalismo e busca entender as engrenagens por trás dos fatos. Sua Missão: Processar notícias brutas e entregar uma análise profunda, ética e crítica. Seu foco é identificar vieses, interesses ocultos e consequências sociais, eliminando o lixo informacional. O que a notícia não está dizendo? Quais vozes foram omitidas? Isso é um evento isolado ou parte de um padrão histórico/político? Quem ganha com a propagação desta narrativa específica? etc.Linguagem Humana e Direta: Sem "corporativês". Use um tom de conversa inteligente e honesta. Transparência: Se houver ambiguidade na fonte, aponte-a. Concisão Crítica: Vá direto ao ponto, mas não sacrifique a complexidade pelo simplismo. O FATO NU E CRU: (A notícia limpa de adjetivos e manipulações). O QUE ESTÁ EM JOGO: (Os interesses políticos, econômicos ou sociais por trás do evento). ALERTA DE RUÍDO: (Identifique se há sensacionalismo, viés ideológico óbvio ou distração de outros temas importantes). PARA PENSAR: (Uma pergunta provocativa ou uma conexão com a realidade do leitor que amplia a visão sobre o tema)."""

    # MONTAGEM DO PROMPT (Otimizada)
    prompt_content = f"Data: {get_br_time()}\n\n"
    
    for item in news_data:
        # 1. Limpeza de "sujeira" (espaços duplos e quebras de linha excessivas)
        raw_text = item['content'] or ""
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        
        # 2. Truncamento inteligente (2500 chars é suficiente para o contexto principal)
        # O lead jornalístico está sempre no início.
        content_preview = clean_text[:2500] 
        
        # 3. Formato de entrada minimalista para economizar tokens
        # O LLM entende XML-like tags ou separadores simples melhor que texto descritivo.
        prompt_content += f"""
        <n>
        <original_title>{item['title']}</original_title>
        <url>{item['url']}</url>
        <body>{clean_text[:2500]}</body>
        </n>
        """

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', # Modelo econômico
            config=genai.types.GenerateContentConfig(
                temperature=0.4 # Menos criativo, mais focado nos fatos
            ),
            contents=[system_instruction, prompt_content]
        )
        return response.text
    except Exception as e:
        return f"Erro fatal na IA: {e}"

def send_telegram(text):
    """Envia o relatório final para o Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    
    for part in parts:
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Erro Telegram: {e}")

# ================= MAIN =================

def main():
    print("--- 🚀 Iniciando v8.0 (Com Deduplicação de Estado) ---")
    
    # Carregar histórico de notícias já processadas
    history = load_history()
    history = clean_old_history(history)  # Remover entradas antigas
    print(f"📋 Histórico carregado: {len(history)} notícias já processadas")
    
    feed = feedparser.parse(RSS_URL)
    news_buffer = [] 
    duplicates_found = 0
    
    count = 0
    for entry in feed.entries:
        if count >= MAX_ITEMS: break
        
        # Resolver URL antes de verificar duplicata
        clean_url = resolve_url_ddg(entry.title)
        if not clean_url:
            print(f"📰 {entry.title}")
            print("   -> Pulei (Sem link)")
            continue
        
        # Verificar duplicata
        if is_news_duplicate(entry.title, clean_url, history):
            print(f"📰 {entry.title}")
            print("   -> Duplicata detectada (pulado)")
            duplicates_found += 1
            continue
        
        print(f"📰 {entry.title}")
        
        # Extrair Conteúdo (Camuflado)
        content = extract_content_robust(clean_url)
        
        # Guardar no Buffer
        news_buffer.append({
            'title': entry.title,
            'url': clean_url,
            'content': content
        })
        
        count += 1
        time.sleep(2)
    
    print(f"\n📊 Resumo: {len(news_buffer)} notícias novas, {duplicates_found} duplicatas")

    # Gerar Relatório Final
    if news_buffer:
        final_report = generate_final_report(news_buffer)
        
        # Atualizar histórico com as notícias processadas
        now = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        for item in news_buffer:
            news_hash = get_news_hash(item['title'], item['url'])
            history[news_hash] = {
                'title': item['title'],
                'url': item['url'],
                'timestamp': now
            }
        
        save_history(history)
        
        # Salvar e Enviar
        with open("briefing_diario.md", "w", encoding="utf-8") as f:
            f.write(final_report)
        
        send_telegram(final_report)
        print("\n✅ Relatório enviado com sucesso!")
    else:
        print("\n⚠️ Nenhuma notícia nova para processar.")

if __name__ == "__main__":
    main()