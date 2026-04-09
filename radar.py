import pandas as pd
import requests
import json
import io
import os

API_KEY = os.environ.get("SCRAPER_API_KEY")

# Alvo mais simples e direto para leitura
url_alvo = "https://www.dadosdemercado.com.br/dividendos"

def atualizar_dividendos():
    print("Iniciando o túnel Premium (ScraperAPI)...")
    
    # Usando premium=true para IPs residenciais imbatíveis e retirando o render (mais rápido)
    url_tunel = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url_alvo}&premium=true"
    
    try:
        print(f"Solicitando os dados de {url_alvo}...")
        resposta = requests.get(url_tunel)
        
        print(f"Status da conexão: {resposta.status_code}")
        
        html_lido = io.StringIO(resposta.text)
        tabelas = pd.read_html(html_lido)
        
        df_correto = None
        for tb in tabelas:
            # Identifica a tabela certa automaticamente
            if 'Data Com' in tb.columns or 'Pagamento' in tb.columns:
                df_correto = tb
                break
                
        if df_correto is not None:
            dados_limpos = []
            print("Tabela encontrada! Extraindo os dados...")
            
            for index, row in df_correto.iterrows():
                ativo = str(row.get('Ativo', row.get('ATIVO', '')))
                tipo = str(row.get('Tipo', row.get('TIPO', '')))
                data_com = str(row.get('Data Com', row.get('DATA COM', '')))
                data_pagamento = str(row.get('Pagamento', row.get('PAGAMENTO', '')))
                valor = str(row.get('Valor', row.get('VALOR', '')))
                
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
            # O Raio-X: mostra os primeiros 500 caracteres do site para sabermos o que o robô viu
            print("Visão do robô (Raio-X do HTML):", resposta.text[:500])

    except Exception as e:
        print(f"Erro técnico na captura: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("ERRO: A chave SCRAPER_API_KEY não foi encontrada nas variáveis do GitHub.")
    else:
        atualizar_dividendos()
