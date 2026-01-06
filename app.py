import os
import time
from datetime import datetime, timedelta, timezone
import feedparser
from google import genai # Nova SDK moderna
from ddgs import DDGS    # Biblioteca corrigida
import requests
from newspaper import Article

# ================= CONFIGURAÇÕES =================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
MAX_ITEMS = 5 

# ================= FUNÇÕES DE APOIO =================

def get_br_time():
    """Retorna a data/hora atual no fuso horário de Brasília (UTC-3)."""
    utc_now = datetime.now(timezone.utc)
    br_time = utc_now - timedelta(hours=3)
    return br_time.strftime('%d/%m %H:%M')

def resolve_url(title, google_link):
    """
    Tenta obter a URL limpa. 
    Estratégia 1: Busca no DuckDuckGo (ddgs).
    Estratégia 2: Tenta seguir o redirect do Google (fallback).
    """
    # 1. Tentar DuckDuckGo (DDGS)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(title, region='br-pt', max_results=1))
            if results:
                return results[0]['href']
    except Exception as e:
        print(f"  [!] Erro no DuckDuckGo: {e}")

    # 2. Fallback: Tentar resolver o redirect do Google diretamente
    try:
        print("  [i] Tentando resolver redirect do Google...")
        # User-agent é essencial para o Google não bloquear o request
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.head(google_link, allow_redirects=True, headers=headers, timeout=5)
        return response.url
    except Exception as e:
        print(f"  [!] Falha total na resolução de URL: {e}")
        return google_link # Retorna o link sujo mesmo, melhor que nada

def extract_content(url):
    """Extrai o corpo do texto da notícia."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception:
        return None

def summarize_with_gemini(title, text):
    """Gera o resumo usando a NOVA SDK do Google GenAI."""
    if not GEMINI_KEY:
        return "⚠️ Erro: Chave Gemini não configurada."
    if not text or len(text) < 300:
        return None

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        prompt = f"""
        Atue como editor chefe. Resuma a notícia abaixo em 3 bullet points curtos em português do Brasil.
        Título: {title}
        Texto: {text[:4000]}
        """
        
        # Chamada atualizada para a nova SDK
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}"

def send_telegram_message(text):
    """Envia a mensagem para o Telegram com tratamento de erros."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Dividir mensagens longas (limite 4096 do Telegram)
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    else:
        parts = [text]

    for part in parts:
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Erro envio Telegram: {e}")

# ================= FLUXO PRINCIPAL =================

def main():
    print("--- 🚀 Iniciando Digere-News (Versão 2.0) ---")
    
    if not GEMINI_KEY:
        print("❌ ERRO: GEMINI_API_KEY não encontrada.")
        return

    feed = feedparser.parse(RSS_URL)
    
    # Cabeçalho com hora corrigida
    full_report = f"🗞️ *Briefing de Notícias* - {get_br_time()}\n\n"
    
    items_processed = 0

    for entry in feed.entries:
        if items_processed >= MAX_ITEMS:
            break
            
        print(f"Processando: {entry.title}")
        
        # Resolve URL (com fallback robusto)
        url = resolve_url(entry.title, entry.link)
        
        content = extract_content(url)
        summary = summarize_with_gemini(entry.title, content)
        
        # Se falhou a extração, gera link smry.ai
        if not summary or "Erro" in summary:
            # Garante que não passamos o link do google para o smry se possível
            clean_link_for_smry = url if "news.google.com" not in url else entry.link
            summary = f"⚠️ Resumo indisponível. [Leia via Smry.ai](https://smry.ai/{clean_link_for_smry})"

        full_report += f"🔹 *{entry.title}*\n{summary}\n[Link Original]({url})\n\n---\n\n"
        items_processed += 1
        time.sleep(1) 

    # Salvar e Enviar
    with open("briefing_diario.md", "w", encoding="utf-8") as f:
        f.write(full_report)
    
    send_telegram_message(full_report)
    print("✅ Concluído!")

if __name__ == "__main__":
    main()