import pandas as pd
import requests
import json
import io
import os

API_KEY = os.environ.get("SCRAPER_API_KEY")

# A URL correta (agora vai!)
url_alvo = "https://www.dadosdemercado.com.br/agenda-de-dividendos"

def atualizar_dividendos():
    print("Iniciando o túnel Premium (ScraperAPI)...")
    
    url_tunel = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url_alvo}&premium=true"
    
    try:
        print(f"Solicitando os dados de {url_alvo}...")
        resposta = requests.get(url_tunel)
        
        print(f"Status da conexão: {resposta.status_code}")
        
        if resposta.status_code != 200:
            print("Erro: A página não carregou corretamente. Verifique a URL.")
            return

        html_lido = io.StringIO(resposta.text)
        tabelas = pd.read_html(html_lido)
        
        df_correto = None
        for tb in tabelas:
            # O Dados de Mercado usa a coluna 'Pagamento'
            if 'Pagamento' in tb.columns:
                df_correto = tb
                break
                
        if df_correto is not None:
            dados_limpos = []
            print("Tabela encontrada! Extraindo os dados...")
            
            for index, row in df_correto.iterrows():
                # Lendo exatamente os cabeçalhos que o site fornece
                ativo = str(row.get('Código', ''))
                tipo = str(row.get('Tipo', ''))
                data_com = str(row.get('Registro', ''))
                data_pagamento = str(row.get('Pagamento', ''))
                valor = str(row.get('Valor (R$)', ''))
                
                if ativo and ativo != 'nan':
                    dados_limpos.append({
                        "ativo": ativo,
                        "tipo": tipo,
                        "data_com": data_com,
                        "data_pagamento": data_pagamento,
                        "valor": valor
                    })

            if len(dados_limpos) > 0:
                with open('dividendos.json', 'w', encoding='utf-8') as f:
                    json.dump(dados_limpos, f, indent=4, ensure_ascii=False)
                print(f"VITÓRIA! {len(dados_limpos)} dividendos salvos com sucesso no dividendos.json")
            else:
                print("A tabela foi encontrada, mas estava vazia.")
        else:
            print("Erro: Nenhuma tabela de dividendos encontrada.")
            print("Visão do robô (Raio-X do HTML):", resposta.text[:500])

    except Exception as e:
        print(f"Erro técnico na captura: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("ERRO: A chave SCRAPER_API_KEY não foi encontrada nas variáveis.")
    else:
        atualizar_dividendos()
