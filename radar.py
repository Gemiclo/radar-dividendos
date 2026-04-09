import pandas as pd
import cloudscraper
import json
import io

url = "https://investidor10.com.br/acoes/proventos/"

def atualizar_dividendos():
    print("Iniciando o Cloudscraper (Evasão de bloqueios)...")
    
    # Configura o robô para imitar perfeitamente um Google Chrome real no Windows
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    try:
        print(f"Acessando o portal: {url}")
        resposta = scraper.get(url)
        
        # O cloudscraper devolve o HTML puro, já passando pela segurança
        html_lido = io.StringIO(resposta.text)
        
        print("Procurando tabelas no site...")
        tabelas = pd.read_html(html_lido)
        
        # A tabela de proventos do Investidor10 geralmente é a primeira
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

        # Salva no JSON
        if len(dados_limpos) > 0:
            with open('dividendos.json', 'w', encoding='utf-8') as f:
                json.dump(dados_limpos, f, indent=4, ensure_ascii=False)
            print(f"BINGO! {len(dados_limpos)} dividendos salvos com sucesso no dividendos.json")
        else:
            print("A tabela foi encontrada, mas estava vazia.")

    except Exception as e:
        print(f"Erro na captura: {e}")

if __name__ == "__main__":
    atualizar_dividendos()
