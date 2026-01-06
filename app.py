import os
import time
import feedparser
import google.generativeai as genai
import requests
from duckduckgo_search import DDGS  # Importação corrigida
from newspaper import Article

# ================= CONFIGURAÇÕES =================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Validação crítica antes de iniciar
if not GEMINI_KEY:
    print("❌ ERRO CRÍTICO: A variável GEMINI_API_KEY não foi encontrada.")
    # Não paramos o script totalmente para permitir testes locais sem API, 
    # mas o resumo falhará.
else:
    # Configura o SDK do Gemini
    genai.configure(api_key=GEMINI_KEY)

# Usando gemini-1.5-flash (versão estável e rápida atual)
# Se o 2.0 estiver disponível na sua conta, pode alterar para 'gemini-2.0-flash-exp'
MODEL_VERSION = 'gemini-1.5-flash'

RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
MAX_ITEMS = 5 

# ================= FUNÇÕES DE APOIO =================

def get_clean_url_via_search(title):
    """Bypass do redirecionador do Google via DuckDuckGo."""
    try:
        # max_results=1 garante que pegamos o primeiro link
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
    """Gera o resumo usando a API do Gemini."""
    if not GEMINI_KEY:
        return "⚠️ Erro: Chave Gemini não configurada."
        
    if not text or len(text) < 300:
        return None

    try:
        model = genai.GenerativeModel(MODEL_VERSION)
        
        prompt = f"""
        Você é um assistente de curadoria de notícias. 
        Crie um resumo executivo em Markdown com 3 a 4 bullet points curtos e diretos em português.
        
        Título: {title}
        Conteúdo: {text[:4000]}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao processar com Gemini: {e}"

def send_telegram_message(text):
    """Envia a mensagem final para o Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado. Pulando envio.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # O Telegram tem limite de 4096 caracteres. Se exceder, dividimos.
    # Margem de segurança de 4000
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    else:
        parts = [text]

    for part in parts:
        try:
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"}
            r = requests.post(url, json=payload)
            if r.status_code != 200:
                print(f"Erro Telegram: {r.text}")
        except Exception as e:
            print(f"Exceção no envio Telegram: {e}")

# ================= FLUXO PRINCIPAL =================

def main():
    print("--- 🚀 Iniciando Digere-News ---")
    
    feed = feedparser.parse(RSS_URL)
    
    # Cabeçalho com data
    current_time = time.strftime('%d/%m %H:%M')
    full_report = f"🗞️ *Briefing de Notícias* - {current_time}\n\n"

    # Itera sobre as notícias
    for i, entry in enumerate(feed.entries[:MAX_ITEMS]):
        print(f"[{i+1}/{MAX_ITEMS}] Processando: {entry.title}")
        
        # 1. Obter URL Limpa
        url = get_clean_url_via_search(entry.title)
        if not url: 
            print("   -> URL não encontrada via busca. Pulando.")
            continue
        
        # 2. Extrair Conteúdo
        content = extract_content(url)
        
        # 3. Resumir com IA
        summary = summarize_with_gemini(entry.title, content)
        
        # Fallback para Smry.ai se falhar a extração ou resumo
        if not summary or "Erro" in summary:
            # Se houve erro ou conteúdo vazio, gera link alternativo
            # Nota: smry.ai aceita a URL completa após a barra
            summary = f"⚠️ Conteúdo protegido ou erro na IA. [Leia via Smry.ai](https://smry.ai/{url})"

        full_report += f"🔹 *{entry.title}*\n{summary}\n[Link Original]({url})\n\n---\n\n"
        
        # Delay ético para não bloquear o DuckDuckGo
        time.sleep(2) 

    # Salva localmente para debug (artefato do GitHub Actions)
    with open("briefing_diario.md", "w", encoding="utf-8") as f:
        f.write(full_report)
    
    # Envia para o telemóvel
    send_telegram_message(full_report)
    print("✅ Processo concluído e enviado!")

if __name__ == "__main__":
    main()