import os
import time
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

RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
MAX_ITEMS = 20 # Limite de notícias por execução 

# ================= FUNÇÕES DE APOIO =================

def get_br_time():
    """Hora atual de Brasília (UTC-3)."""
    return (datetime.now(timezone.utc) - timedelta(hours=3)).strftime('%d/%m %H:%M')

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
    Envia TODAS as notícias para o Gemini 2.5 de uma vez só.
    """
    if not GEMINI_KEY: return "⚠️ Erro: API Key não configurada (Use 'export GEMINI_API_KEY=...')."
    if not news_data: return "⚠️ Nenhuma notícia foi coletada."

    print(f"\n[IA] Gerando relatório consolidado via Gemini 2.5 ({len(news_data)} notícias)...")

    # 1. Monta o Prompt com os dados brutos
    prompt_content = f"Data do Briefing: {get_br_time()}\n\n"
    
    for idx, item in enumerate(news_data, 1):
        content_preview = item['content'][:10000] if item['content'] else "Conteúdo não disponível (Erro na extração)."
        
        prompt_content += f"""
        --- NOTÍCIA {idx} ---
        Título: {item['title']}
        Link Original: {item['url']}
        Conteúdo Bruto: 
        {content_preview}
        
        """

    # 2. Instruções para o Gemini 2.5
    system_instruction = """
    Você é o editor chefe do bot "Digere-News". 
    Sua tarefa é receber um lote de notícias brutas e escrever um Briefing Executivo. Seja direto. Não inclua introduções como "Aqui está o resumo".
    """

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        # Atualizado para o modelo que você mostrou no print
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', 
            contents=[system_instruction, prompt_content]
        )
        return response.text
    except Exception as e:
        return f"Erro fatal na geração do relatório via IA: {e}"

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
    print("--- 🚀 Iniciando v7.1 (Batch + Gemini 2.5) ---")
    
    feed = feedparser.parse(RSS_URL)
    news_buffer = [] 
    
    count = 0
    for entry in feed.entries:
        if count >= MAX_ITEMS: break
        
        print(f"\n📰 Processando: {entry.title}")
        
        # 1. Resolver URL
        clean_url = resolve_url_ddg(entry.title)
        if not clean_url:
            print("   -> Pulei (Sem link)")
            continue

        # 2. Extrair Conteúdo (Camuflado)
        content = extract_content_robust(clean_url)
        
        # 3. Guardar no Buffer
        news_buffer.append({
            'title': entry.title,
            'url': clean_url,
            'content': content
        })
        
        count += 1
        time.sleep(2) 

    # 4. Gerar Relatório Final
    if news_buffer:
        final_report = generate_final_report(news_buffer)
        
        # Salvar e Enviar
        with open("briefing_diario.md", "w", encoding="utf-8") as f:
            f.write(final_report)
        
        send_telegram(final_report)
        print("\n✅ Relatório enviado com sucesso!")
    else:
        print("\n⚠️ Nenhuma notícia processada.")

if __name__ == "__main__":
    main()