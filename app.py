import os
import re
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
    Envia TODAS as notícias para o Gemini de uma vez só, 
    otimizado para economia de tokens.
    """
    if not GEMINI_KEY: return "⚠️ Erro: API Key não configurada."
    if not news_data: return "⚠️ Nenhuma notícia foi coletada."

    print(f"\n[IA] Gerando relatório consolidado ({len(news_data)} notícias)...")

    # INSTRUÇÃO DO SISTEMA (Compactada)
    # Define o formato de saída desejado e a persona.
    system_instruction = """
    Você é um Analista de Inteligência Sênior do 'Digere-News'.
    Sua missão: Processar notícias brutas e entregar inteligência de alto valor com ZERO ruído e ZERO estafa cognitiva.

    DIRETRIZES DE ESTILO (CRÍTICO):
    1.  **Anti-Clickbait:** Se o título original for vago ou sensacionalista, REESCREVA-O para ser puramente factual e descritivo.
    2.  **Escaneabilidade:** Use **negrito** apenas em: nomes próprios cruciais, números, datas e valores monetários. Isso guia o olho do leitor.
    3.  **Densidade:** Elimine palavras de transição vazias ("no entanto", "além disso", "vale ressaltar"). Vá direto ao ponto.
    4.  **Estrutura Mental:** Para cada notícia, responda implicitamente: "O que houve?" e "Por que isso importa/Qual o contexto?".

    FORMATO DE SAÍDA OBRIGATÓRIO (Markdown):
    🔹 **[Título Claro e Informativo]**
    * **Fato:** [Resumo direto do acontecimento principal em 1 frase. Voz ativa.]
    * **Contexto:** [Por que isso é relevante, histórico breve ou impacto futuro. 1 frase.]
    [Link Original](url)
    ---

    Exemplo de Transformação:
    Entrada: "Governo anuncia nova medida que muda tudo na economia" (Texto sobre aumento da Selic para 12%)
    Saída:
    🔹 **Banco Central eleva taxa Selic para 12% ao ano**
    * **Fato:** O **Copom** decidiu aumentar a taxa básica de juros em **0,5 ponto percentual** para conter a inflação.
    * **Contexto:** É a **3ª alta consecutiva**, encarecendo o crédito e impactando o consumo das famílias.
    [Link Original](...)
    ---
    """

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
        <news>
        Title: {item['title']}
        URL: {item['url']}
        Body: {content_preview}
        </news>
        """

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Modelo econômico
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