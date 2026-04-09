import pandas as pd
import requests
import json
import io
import os

# Pega a chave secreta que guardamos no GitHub
API_KEY = os.environ.get("SCRAPER_API_KEY")
url_alvo = "https://investidor10.com.br/acoes/proventos/"

def atualizar_dividendos():
    print("Iniciando o túnel residencial (ScraperAPI)...")
    
    # O parâmetro render=true garante que o ScraperAPI espere o JavaScript da tabela carregar
    url_tunel = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url_alvo}&render=true"
    
    try:
        print("Solicitando os dados da tabela...")
        resposta = requests.get(url_tunel)
        
        html_lido = io.StringIO(resposta.text)
        tabelas = pd.read_html(html_lido)
        
        # A primeira tabela é a que importa
        df_correto = tabelas[0]
        
        dados_limpos = []
        print("Tabela encontrada! Extraindo os dados...")
        
        for index, row in df_correto.iterrows():
            ativo = str(row.get('Ativo', ''))
            tipo = str(row.get('Tipo', ''))
            data_com = str(row.get('Data Com', ''))
            data_pagamento = str(row.get('Pagamento', ''))
            valor = str(row.get('Valor', ''))
            
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

    except Exception as e:
        print(f"Erro na captura: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("ERRO: A chave SCRAPER_API_KEY não foi encontrada no ambiente.")
    else:
        atualizar_dividendos()
