import os
import time
from datetime import datetime, timedelta, timezone
import feedparser
from google import genai
from ddgs import DDGS
import requests
from newspaper import Article

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
    """
    Remove o nome da fonte no final do título para melhorar a busca no DDG.
    Ex: 'Dólar sobe a R$ 5 - UOL Economia' vira 'Dólar sobe a R$ 5'
    """
    if " - " in title:
        return title.rsplit(" - ", 1)[0]
    return title

def resolve_url_ddg(title):
    """
    Busca Exclusiva no DuckDuckGo com retentativa.
    """
    clean_title = clean_title_for_search(title)
    print(f"  [Busca] Procurando: '{clean_title}'...")

    # Tenta até 2 vezes
    for attempt in range(1, 3):
        try:
            with DDGS() as ddgs:
                # region='br-pt' foca em resultados do Brasil
                results = list(ddgs.text(clean_title, region='br-pt', max_results=1))
                if results:
                    found_url = results[0]['href']
                    print(f"  [Sucesso] Link encontrado: {found_url[:50]}...")
                    return found_url
        except Exception as e:
            print(f"  [!] Erro DDG (Tentativa {attempt}): {e}")
            time.sleep(2) # Espera um pouco antes de tentar de novo
            
    print("  [Falha] Não foi possível encontrar o link no DuckDuckGo.")
    return None

def extract_content(url):
    """Baixa o artigo usando newspaper3k."""
    try:
        # Se por acaso a URL ainda for do google, aborta para não travar
        if "news.google.com" in url:
            return None
            
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception:
        return None

def summarize_with_gemini(title, text):
    """Resume com Gemini 1.5 Flash (SDK Novo)."""
    if not GEMINI_KEY:
        return "⚠️ Erro: Chave API não configurada."
    if not text or len(text) < 300:
        return None 

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        prompt = f"""
        Atue como jornalista sênior. Resuma a notícia abaixo em 3 bullet points informativos (Português BR).
        Título: {title}
        Texto: {text[:4000]}
        """
        response = client.models.generate_content(
            model='gemini-1.5-flash',
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
    print("--- 🚀 Iniciando v4.0 (Full DuckDuckGo) ---")
    
    feed = feedparser.parse(RSS_URL)
    full_report = f"🗞️ *Briefing* - {get_br_time()}\n\n"
    
    count = 0
    for entry in feed.entries:
        if count >= MAX_ITEMS: break
        
        print(f"\n📰 Notícia: {entry.title}")
        
        # 1. Resolve URL (Só DDG)
        clean_url = resolve_url_ddg(entry.title)
        
        # Se não achou link, pula ou avisa
        if not clean_url:
            print("   -> Pulei (Link não encontrado)")
            continue
            
        # 2. Extrai Texto
        content = extract_content(clean_url)
        
        # 3. Resume
        summary = None
        if content:
            summary = summarize_with_gemini(entry.title, content)
        
        # 4. Monta Relatório
        if not summary or "Erro" in summary:
            # Se falhar, manda link do Smry
            smry_link = f"https://smry.ai/{clean_url}"
            full_report += f"🔹 *{entry.title}*\n⚠️ Resumo indisponível. [Leia no Smry.ai]({smry_link})\n[Link Original]({clean_url})\n\n---\n\n"
        else:
            full_report += f"🔹 *{entry.title}*\n{summary}\n[Link Original]({clean_url})\n\n---\n\n"
            
        count += 1
        # Pausa importante para não bloquear o DDG
        time.sleep(3)

    # Finaliza
    with open("briefing_diario.md", "w", encoding="utf-8") as f:
        f.write(full_report)
    
    send_telegram(full_report)
    print("\n✅ Concluído!")

if __name__ == "__main__":
    main()