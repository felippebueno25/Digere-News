#!/usr/bin/env python3
"""
Script de teste para a funcionalidade de deduplicação.
Não requer chaves de API (Gemini, Telegram) para testar o core.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta, timezone

# Simular configurações
HISTORY_FILE = ".news_history.json"
HISTORY_DAYS = 7

def get_news_hash(title, url):
    """Gera hash MD5 da notícia."""
    key = f"{title.lower().strip()}|{url.lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()

def load_history():
    """Carrega histórico."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_history(history):
    """Salva histórico."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"✅ Histórico salvo com {len(history)} entradas")

def is_duplicate(title, url, history):
    """Verifica duplicata."""
    return get_news_hash(title, url) in history

def test_basic_deduplication():
    """Teste 1: Deduplicação básica"""
    print("\n" + "="*60)
    print("TESTE 1: Deduplicação Básica")
    print("="*60)
    
    # Limpar histórico anterior
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    
    history = load_history()
    print(f"Histórico inicial: {len(history)} entradas")
    
    # Primeira notícia
    title1 = "Lula assina decreto sobre reforma tributária"
    url1 = "https://g1.globo.com/noticia-1"
    
    print(f"\n[1] Processando: {title1}")
    if is_duplicate(title1, url1, history):
        print("    ❌ ERRO: Deveria ser nova!")
    else:
        print("    ✅ Nova notícia detectada corretamente")
        # Adicionar ao histórico
        news_hash = get_news_hash(title1, url1)
        history[news_hash] = {
            'title': title1,
            'url': url1,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    # Mesma notícia novamente
    print(f"\n[2] Reprocessando: {title1}")
    if is_duplicate(title1, url1, history):
        print("    ✅ Duplicata detectada corretamente")
    else:
        print("    ❌ ERRO: Deveria ser duplicata!")
    
    # Notícia diferente
    title2 = "BC aumenta taxa Selic"
    url2 = "https://bcb.gov.br/noticia-2"
    
    print(f"\n[3] Processando: {title2}")
    if is_duplicate(title2, url2, history):
        print("    ❌ ERRO: Deveria ser nova!")
    else:
        print("    ✅ Nova notícia detectada corretamente")
        news_hash = get_news_hash(title2, url2)
        history[news_hash] = {
            'title': title2,
            'url': url2,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    save_history(history)

def test_title_variations():
    """Teste 2: Variações de título"""
    print("\n" + "="*60)
    print("TESTE 2: Variações de Título (Normalização)")
    print("="*60)
    
    history = load_history()
    
    # Título original
    title1 = "Lula assina decreto sobre reforma tributária"
    url = "https://g1.globo.com/noticia"
    
    hash1 = get_news_hash(title1, url)
    print(f"\nTítulo original: {title1}")
    print(f"Hash: {hash1}")
    
    # Variações que DEVERIAM ser consideradas iguais (normalização)
    variations = [
        "LULA ASSINA DECRETO SOBRE REFORMA TRIBUTÁRIA",  # Maiúsculas
        "lula  assina  decreto  sobre  reforma  tributária",  # Espaços extras
        "  Lula assina decreto sobre reforma tributária  ",  # Espaços ao redor
    ]
    
    for title2 in variations:
        hash2 = get_news_hash(title2, url)
        is_same = hash1 == hash2
        status = "✅ Mesma" if is_same else "❌ Diferente"
        print(f"\n{status}: '{title2}'")
        print(f"Hash: {hash2}")

def test_url_variations():
    """Teste 3: Variações de URL"""
    print("\n" + "="*60)
    print("TESTE 3: Variações de URL (HTTP vs HTTPS, etc)")
    print("="*60)
    
    title = "Notícia importante"
    
    urls = [
        "https://g1.globo.com/noticia",
        "HTTPS://G1.GLOBO.COM/NOTICIA",  # Maiúsculas
        "https://G1.GLOBO.COM/noticia",  # URL parcialmente maiúscula
    ]
    
    hashes = []
    for i, url in enumerate(urls, 1):
        hash_val = get_news_hash(title, url)
        hashes.append(hash_val)
        print(f"\n[{i}] URL: {url}")
        print(f"    Hash: {hash_val}")
    
    if len(set(hashes)) == 1:
        print("\n✅ Todas as URLs normalizadas para mesmo hash")
    else:
        print("\n⚠️ URLs resultaram em hashes diferentes (esperado)")

def test_history_persistence():
    """Teste 4: Persistência em JSON"""
    print("\n" + "="*60)
    print("TESTE 4: Persistência em JSON")
    print("="*60)
    
    # Salvar histórico
    history = {
        "hash1": {
            "title": "Notícia 1",
            "url": "https://exemplo.com/1",
            "timestamp": "2026-01-07T15:30:00"
        },
        "hash2": {
            "title": "Notícia 2",
            "url": "https://exemplo.com/2",
            "timestamp": "2026-01-07T12:00:00"
        }
    }
    
    save_history(history)
    
    # Recarregar e verificar
    loaded = load_history()
    print(f"\nEntradas carregadas: {len(loaded)}")
    
    for hash_id, entry in loaded.items():
        print(f"\n  {hash_id}:")
        print(f"    Título: {entry['title']}")
        print(f"    URL: {entry['url']}")
        print(f"    Timestamp: {entry['timestamp']}")
    
    if len(loaded) == 2:
        print("\n✅ Histórico persistido corretamente")
    else:
        print("\n❌ ERRO na persistência")

def test_file_size():
    """Teste 5: Tamanho do arquivo"""
    print("\n" + "="*60)
    print("TESTE 5: Tamanho do Arquivo de Histórico")
    print("="*60)
    
    if os.path.exists(HISTORY_FILE):
        size_bytes = os.path.getsize(HISTORY_FILE)
        size_kb = size_bytes / 1024
        
        history = load_history()
        
        print(f"\nEntradas: {len(history)}")
        print(f"Tamanho: {size_bytes} bytes ({size_kb:.2f} KB)")
        
        if size_bytes > 100_000:  # 100 KB
            print("⚠️ Arquivo > 100 KB (considere limpar histórico)")
        else:
            print("✅ Tamanho adequado")
        
        # Estimar
        if len(history) > 0:
            bytes_per_entry = size_bytes / len(history)
            entries_for_1mb = 1_000_000 / bytes_per_entry
            print(f"\nEstimativa: ~{entries_for_1mb:.0f} entradas para 1 MB")

def cleanup():
    """Limpa arquivos de teste"""
    print("\n" + "="*60)
    print("LIMPEZA")
    print("="*60)
    
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        print(f"✅ {HISTORY_FILE} removido")
    else:
        print(f"ℹ️ {HISTORY_FILE} não encontrado")

if __name__ == "__main__":
    print("\n🧪 TESTES DE DEDUPLICAÇÃO - Digere-News v8.0")
    print("="*60)
    
    try:
        test_basic_deduplication()
        test_title_variations()
        test_url_variations()
        test_history_persistence()
        test_file_size()
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES CONCLUÍDOS")
        print("="*60)
        
        # Perguntar se deseja limpar
        response = input("\nDeseja remover arquivos de teste? (s/n): ").lower()
        if response == 's':
            cleanup()
        else:
            print(f"\nℹ️ Arquivo {HISTORY_FILE} preservado para inspeção")
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
