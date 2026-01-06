import os
import time
from datetime import datetime, timedelta, timezone
import feedparser
from google import genai
from ddgs import DDGS
import requests
import trafilatura
from newspaper import Article, Config

# ================= CONFIGURAÇÕES =================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
MAX_ITEMS = 5 

# ================= FUNÇÕES =================

def get_br_time():
    """Hora atual de Brasília (UTC-3)."""
    return (datetime.now(timezone.utc) - timedelta(hours=3)).strftime('%d/%m %H:%M')

def clean_title_for_search(title):
    """Remove a fonte do título para melhorar a busca no DDG."""
    if " - " in title:
        return title.rsplit(" - ", 1)[0]
    return title

def resolve_url_ddg(title):
    """Busca Exclusiva no DuckDuckGo com headers reais."""
    clean_title = clean_title_for_search(title)
    print(f"  [Busca] Procurando: '{clean_title}'...")

    for attempt in range(1, 3):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(clean_title, region='br-pt', max_results=1))
                if results:
                    found_url = results[0]['href']
                    print(f"  [Sucesso] Link encontrado: {found_url[:50]}...")
                    return found_url
        except Exception as e:
            print(f"  [!] Erro DDG (Tentativa {attempt}): {e}")
            time.sleep(2)
            
    print("  [Falha] Link não encontrado no DuckDuckGo.")
    return None

def extract_content(url):
    """
    Tenta extrair o texto completo usando Trafilatura (Melhor) e Newspaper3k (Fallback).
    Simula um navegador real para evitar bloqueios.
    """
    if "news.google.com" in url:
        return None

    print("  [Extração] Baixando conteúdo...")
    
    # 1. Tentativa Principal: Trafilatura (Mais robusto para texto)
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if text and len(text) > 300:
                print("  -> Sucesso com Trafilatura!")
                return text
    except Exception as e:
        print(f"  [!] Trafilatura falhou: {e}")

    # 2. Fallback: Newspaper3k com User-Agent de Navegador
    print("  -> Tentando fallback com Newspaper3k...")
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        config = Config()
        config.browser_user_agent = user_agent
        config.request_timeout = 10

        article = Article(url, config=config)
        article.download()
        article.parse()
        
        if article.text and len(article.text) > 300:
            print("  -> Sucesso com Newspaper3k!")
            return article.text
    except Exception as e:
        print(f"  [!] Newspaper3k falhou: {e}")

    return None

def summarize_with_gemini(title, text):
    """Resume com Gemini 1.5 Flash."""
    if not GEMINI_KEY:
        return "⚠️ Erro: Chave API não configurada."
    
    # Proteção: Se o texto for muito curto, provavelmente é erro de captura ou paywall rígido
    if not text or len(text) < 300:
        return None 

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        prompt = f"""
        Você é um editor sênior de tecnologia e política.
        Abaixo está o texto completo de uma notícia.
        
        Seu objetivo:
        1. Analise o texto na íntegra.
        2. Crie um resumo informativo em 3 a 4 bullet points (Português BR).
        3. Foque nos fatos, números e consequências. Evite lero-lero.
        
        Título: {title}
        
        Texto da Notícia:
        {text[:8000]} 
        """
        # Aumentei o limite de caracteres para 8000 para caber mais contexto
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Erro na IA: {str(e)}"

def send_telegram(text):
    """Envia para o Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for part in parts:
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Erro Telegram: {e}")

# ================= MAIN =================

def main():
    print("--- 🚀 Iniciando v5.0 (Trafilatura + Extração Robusta) ---")
    
    feed = feedparser.parse(RSS_URL)
    full_report = f"🗞️ *Briefing* - {get_br_time()}\n\n"
    
    count = 0
    for entry in feed.entries:
        if count >= MAX_ITEMS: break
        
        print(f"\n📰 Notícia: {entry.title}")
        
        # 1. Resolve URL
        clean_url = resolve_url_ddg(entry.title)
        
        if not clean_url:
            print("   -> Pulei (Link não encontrado)")
            continue
            
        # 2. Extrai Texto (Agora muito mais forte)
        content = extract_content(clean_url)
        
        # 3. Resume
        summary = None
        if content:
            summary = summarize_with_gemini(entry.title, content)
        else:
            print("   -> Falha na extração do texto (Site blindado/Paywall?)")
        
        # 4. Monta Relatório
        if not summary or "Erro" in summary:
            smry_link = f"https://smry.ai/{clean_url}"
            full_report += f"🔹 *{entry.title}*\n⚠️ Texto não extraído (Site protegido). [Tente ler no Smry.ai]({smry_link})\n[Link Original]({clean_url})\n\n---\n\n"
        else:
            full_report += f"🔹 *{entry.title}*\n{summary}\n[Link Original]({clean_url})\n\n---\n\n"
            
        count += 1
        time.sleep(3)

    # Finaliza
    with open("briefing_diario.md", "w", encoding="utf-8") as f:
        f.write(full_report)
    
    send_telegram(full_report)
    print("\n✅ Concluído!")

if __name__ == "__main__":
    main()