import requests
import json
import time
import hmac
import hashlib

# Credenciais fornecidas
ACCESS_TOKEN = "EAALs2f7SWj4BQjpXvwSL67OvaYJvEMdnsUQSRVPtSGHJsHTmcXM4MlUQBVJvVFxHHZAmdtWsxYUIE5C50ldTucFgWVE3tcO1mBkjUVrZABv1SLeLV9iSMNU8m4V9VeMSSHkn2CJ1oVbmdpZAe7DSCR8dn5JxuDyRP2WfmK9HDTyX4HYmBTZCAAWn2uP0IiVgYtJtDfrPW4ZBq2RkJyE5nw7Ai1ZCCiKPlfWzxY3F0HLgHHCF985DW8zqdV6Xw7PRZCYVo0T5jwkX6T7O0dDPgFeheetRoUjU9qdYgZDZD"
APP_SECRET = "8db972b645ceeb61f21642de6622aa92"
API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}/ads_archive"

def gerar_appsecret_proof(token, app_secret):
    return hmac.new(
        app_secret.encode('utf-8'),
        msg=token.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

def buscar_anuncios(termo_busca):
    proof = gerar_appsecret_proof(ACCESS_TOKEN, APP_SECRET)
    params = {
        'access_token': ACCESS_TOKEN,
        'appsecret_proof': proof,
        'search_terms': termo_busca,
        'ad_type': 'ALL',
        'ad_active_status': 'ACTIVE',
        'fields': 'ad_creation_time,ad_creative_bodies,ad_creative_link_titles,ad_creative_link_descriptions,publisher_platforms,page_name',
        'limit': 5
    }
    
    # Remove country for a test or set to BR if needed. 
    # API for 'ALL' usually requires country if searching by terms.
    params['ad_reached_countries'] = "['BR']"

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        if 'error' in data:
            print(f"Erro ao buscar '{termo_busca}': {json.dumps(data['error'], indent=2)}")
            return []
        return data.get('data', [])
    except Exception as e:
        print(f"Exceção ao buscar '{termo_busca}': {e}")
        return []

def testar_token():
    url = f"https://graph.facebook.com/{API_VERSION}/me"
    proof = gerar_appsecret_proof(ACCESS_TOKEN, APP_SECRET)
    params = {
        'access_token': ACCESS_TOKEN,
        'appsecret_proof': proof
    }
    resp = requests.get(url, params=params)
    print("Teste Token /me:", resp.json())

def main():
    testar_token()
    
    # Termos de busca baseados nos concorrentes de Passo Fundo identificados
    termos = [
        "Somare Pizzaria",
        "Don Gentil Pizzaria",
        "Didio's Burger",
        "Big Xis",
        "Honshu Sushi",
        "Assados Ávila",
        "Restaurante Passo Fundo",
        "Delivery Passo Fundo"
    ]
    
    resultados_agrupados = {}
    
    print("Iniciando busca na Meta Ads Library API...")
    
    for termo in termos:
        print(f"Buscando: {termo}...")
        anuncios = buscar_anuncios(termo)
        
        if anuncios:
            print(f"  -> Encontrados {len(anuncios)} anúncios.")
            # Filtrar para garantir que seja relevante (pode vir coisa de outras cidades com mesmo nome)
            # Como a API busca texto livre, vamos tentar filtrar por contexto se possível, 
            # mas vamos salvar tudo para análise agora.
            resultados_agrupados[termo] = anuncios
        else:
            print("  -> Nenhum anúncio ativo encontrado.")
        
        time.sleep(1) # Respeitar rate limit

    # Salvar raw data
    with open('meta_ads_raw.json', 'w', encoding='utf-8') as f:
        json.dump(resultados_agrupados, f, indent=4, ensure_ascii=False)
    
    print("\nColeta finalizada. Dados salvos em meta_ads_raw.json")

if __name__ == "__main__":
    main()
