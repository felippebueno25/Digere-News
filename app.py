import os
import time
import random
import feedparser
import google.generativeai as genai
from ddgs import DDGS
from newspaper import Article

# ================= CONFIGURAÇÕES =================
# No Codespace, use: export GEMINI_API_KEY="sua_chave"
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyC9vh0luVyUQvS16wEdfa_hf3QmJOYyAn8"

# Configura o SDK do Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
MAX_ITEMS = 5 

# ================= FUNÇÕES =================

def get_clean_url_via_search(title):
    """Busca a URL original no DuckDuckGo para evitar bloqueios do Google."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(title, region='br-pt', max_results=1))
            if results:
                return results[0]['href']
    except Exception as e:
        print(f"  [!] Erro no DuckDuckGo: {e}")
    return None

def extract_content(url):
    """Extrai o texto da notícia."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception:
        return None

def summarize_with_gemini(title, text):
    """Gera o resumo usando a API do Gemini."""
    if not text:
        return None

    prompt = f"""
    Você é um assistente de curadoria de notícias. 
    Abaixo está o título e o conteúdo bruto de uma notícia de tecnologia.
    
    Título: {title}
    Conteúdo: {text[:4000]}
    
    Tarefa:
    Crie um resumo executivo em Markdown com 3 a 4 bullet points curtos e diretos.
    Se o conteúdo parecer ser apenas um aviso de paywall ou erro, informe que o conteúdo está bloqueado.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao processar com Gemini: {e}"

# ================= EXECUÇÃO =================

def main():
    print("--- 🚀 Iniciando Digere-News com Gemini ---")
    
    feed = feedparser.parse(RSS_URL)
    report_content = f"# 🗞️ Briefing de Notícias (Gemini)\nData: {time.strftime('%d/%m/%Y %H:%M')}\n\n"

    for i, entry in enumerate(feed.entries[:MAX_ITEMS]):
        print(f"[{i+1}/{MAX_ITEMS}] Analisando: {entry.title}")
        
        clean_url = get_clean_url_via_search(entry.title)
        if not clean_url: continue
        
        raw_text = extract_content(clean_url)
        
        if raw_text and len(raw_text) > 300:
            summary = summarize_with_gemini(entry.title, raw_text)
        else:
            smry_link = f"https://smry.ai/{clean_url}"
            summary = f"⚠️ **Conteúdo Protegido.** [Leia via Smry.ai]({smry_link})"

        report_content += f"## {entry.title}\n"
        report_content += f"**Link:** {clean_url}\n\n"
        report_content += f"{summary}\n\n"
        report_content += "---\n\n"
        
        time.sleep(2) # Delay ético

    with open("briefing_diario.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("\n✅ Relatório gerado com sucesso!")

if __name__ == "__main__":
    main()