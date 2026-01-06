import os
import time
import feedparser
import google.generativeai as genai
import requests
from ddgs import DDGS
from newspaper import Article

# ================= CONFIGURAÇÕES =================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configura o SDK do Gemini
genai.configure(api_key=GEMINI_KEY)
# Usando gemini-1.5-flash para velocidade e custo/benefício
model = genai.GenerativeModel('gemini-2.5-flash')

RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
MAX_ITEMS = 5 

# ================= FUNÇÕES DE APOIO =================

def get_clean_url_via_search(title):
    """Bypass do redirecionador do Google via DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(title, region='br-pt', max_results=1))
            if results:
                return results[0]['href']
    except Exception as e:
        print(f"  [!] Erro no DuckDuckGo: {e}")
    return None

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
    """Resumo via IA."""
    if not text or len(text) < 300:
        return None

    prompt = f"Resuma a notícia '{title}' em 3 bullet points curtos em português. Conteúdo: {text[:4000]}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}"

def send_telegram_message(text):
    """Envia a mensagem final para o Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado. Pulando envio.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # O Telegram tem limite de 4096 caracteres. Se exceder, dividimos.
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    else:
        parts = [text]

    for part in parts:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

# ================= FLUXO PRINCIPAL =================

def main():
    print("--- 🚀 Iniciando Digere-News ---")
    
    feed = feedparser.parse(RSS_URL)
    full_report = f"🗞️ *Briefing de Notícias* - {time.strftime('%d/%m %H:%M')}\n\n"

    for i, entry in enumerate(feed.entries[:MAX_ITEMS]):
        print(f"[{i+1}/{MAX_ITEMS}] Processando: {entry.title}")
        
        url = get_clean_url_via_search(entry.title)
        if not url: continue
        
        content = extract_content(url)
        summary = summarize_with_gemini(entry.title, content)
        
        if not summary:
            summary = f"⚠️ Conteúdo com paywall. [Leia via Smry.ai](https://smry.ai/{url})"

        full_report += f"🔹 *{entry.title}*\n{summary}\n[Link Original]({url})\n\n---\n\n"
        time.sleep(1) # Delay para evitar blocks

    # Salva localmente por segurança
    with open("briefing_diario.md", "w", encoding="utf-8") as f:
        f.write(full_report)
    
    # Envia para o celular
    send_telegram_message(full_report)
    print("✅ Processo concluído e enviado!")

if __name__ == "__main__":
    main()