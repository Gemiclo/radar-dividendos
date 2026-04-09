import pandas as pd
import requests
import json
import io
import os

API_KEY = os.environ.get("SCRAPER_API_KEY")

# Agora temos uma lista com as duas fontes (Ações e FIIs)
urls_alvo = [
    "https://www.dadosdemercado.com.br/agenda-de-dividendos", # Ações e BDRs
    "https://investidor10.com.br/fiis/proventos/"             # FIIs
]

def atualizar_dividendos():
    print("Iniciando o túnel Premium (ScraperAPI)...")
    
    dados_totais = [] # Lista mestra que vai guardar tudo

    for url in urls_alvo:
        url_tunel = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url}&premium=true"
        
        try:
            print(f"\nBuscando dados de: {url}")
            resposta = requests.get(url_tunel)
            
            if resposta.status_code != 200:
                print(f"Erro ao acessar {url}. Status: {resposta.status_code}")
                continue # Pula para a próxima URL se der erro

            html_lido = io.StringIO(resposta.text)
            tabelas = pd.read_html(html_lido)
            
            df_correto = None
            for tb in tabelas:
                # Procura por colunas típicas de dividendos em qualquer um dos sites
                if 'Pagamento' in tb.columns or 'Data Com' in tb.columns:
                    df_correto = tb
                    break
                    
            if df_correto is not None:
                contador = 0
                for index, row in df_correto.iterrows():
                    # Mapeia as colunas considerando as diferenças entre os dois sites
                    ativo = str(row.get('Código', row.get('Ativo', '')))
                    tipo = str(row.get('Tipo', 'Rendimento')) # FII costuma ser Rendimento
                    data_com = str(row.get('Registro', row.get('Data Com', '')))
                    data_pagamento = str(row.get('Pagamento', ''))
                    valor = str(row.get('Valor (R$)', row.get('Valor', '')))
                    
                    if ativo and ativo != 'nan' and ativo.strip() != '':
                        dados_totais.append({
                            "ativo": ativo.strip(),
                            "tipo": tipo.strip(),
                            "data_com": data_com.strip(),
                            "data_pagamento": data_pagamento.strip(),
                            "valor": valor.strip()
                        })
                        contador += 1
                
                print(f"Sucesso! {contador} proventos extraídos dessa página.")
            else:
                print("Aviso: Nenhuma tabela encontrada nesta página específica.")

        except Exception as e:
            print(f"Erro técnico na captura de {url}: {e}")

    # Ao final do loop, salva tudo no mesmo JSON
    if len(dados_totais) > 0:
        with open('dividendos.json', 'w', encoding='utf-8') as f:
            json.dump(dados_totais, f, indent=4, ensure_ascii=False)
        print(f"\nVITÓRIA FINAL! {len(dados_totais)} dividendos (Ações + FIIs) salvos no dividendos.json")
    else:
        print("\nErro crítico: Nenhum dado foi salvo no processo.")

if __name__ == "__main__":
    if not API_KEY:
        print("ERRO: A chave SCRAPER_API_KEY não foi encontrada nas variáveis.")
    else:
        atualizar_dividendos()
