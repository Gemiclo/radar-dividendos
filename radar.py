import pandas as pd
import requests
import json
import io
import os

API_KEY = os.environ.get("SCRAPER_API_KEY")

# A URL dos FIIs foi atualizada para a nova rota correta
urls_alvo = [
    "https://www.dadosdemercado.com.br/agenda-de-dividendos", 
    "https://investidor10.com.br/fiis/dividendos/"             
]

def atualizar_dividendos():
    print("Iniciando o túnel Premium (ScraperAPI)...")
    
    dados_totais = [] 

    for url in urls_alvo:
        url_tunel = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url}&premium=true"
        
        try:
            print(f"\nBuscando dados de: {url}")
            resposta = requests.get(url_tunel)
            
            if resposta.status_code != 200:
                print(f"Erro ao acessar {url}. Status: {resposta.status_code}")
                continue 

            html_lido = io.StringIO(resposta.text)
            tabelas = pd.read_html(html_lido)
            
            df_correto = None
            for tb in tabelas:
                # O Investidor10 FIIs usa "Data Pagamento", Dados de Mercado usa "Pagamento"
                if 'Pagamento' in tb.columns or 'Data Pagamento' in tb.columns or 'Data Com' in tb.columns:
                    df_correto = tb
                    break
                    
            if df_correto is not None:
                contador = 0
                for index, row in df_correto.iterrows():
                    
                    # 1. Captura e limpa o Ativo (Investidor10 junta o ticker com o nome, ex: "MXRF11 Maxi Renda")
                    ativo_cru = str(row.get('Código', row.get('Ativo', row.get('Empresa', ''))))
                    ativo = ativo_cru.split()[0] if ativo_cru else ''
                    
                    # 2. Captura o Tipo
                    tipo = str(row.get('Tipo', 'Rendimento')) 
                    
                    # 3. Captura e limpa a Data Com (Remove textos como "Data Com " se houver)
                    data_com_cru = str(row.get('Registro', row.get('Data Com', '')))
                    data_com = data_com_cru.replace('Data Com', '').strip()
                    
                    # 4. Captura e limpa a Data de Pagamento (Remove "Pgto " se houver)
                    data_pag_cru = str(row.get('Pagamento', row.get('Data Pagamento', '')))
                    data_pagamento = data_pag_cru.replace('Pgto', '').strip()
                    
                    # 5. Captura e limpa o Valor (Pega apenas o que vem depois do "R$")
                    valor_cru = str(row.get('Valor (R$)', row.get('Valor', '')))
                    valor = valor_cru.split('R$')[-1].strip()
                    
                    # Só adiciona se tiver um ticker válido e um valor
                    if ativo and ativo != 'nan' and valor and valor != 'nan':
                        dados_totais.append({
                            "ativo": ativo,
                            "tipo": tipo.strip(),
                            "data_com": data_com,
                            "data_pagamento": data_pagamento,
                            "valor": valor
                        })
                        contador += 1
                
                print(f"Sucesso! {contador} proventos extraídos dessa página.")
            else:
                print("Aviso: Nenhuma tabela encontrada nesta página específica.")

        except Exception as e:
            print(f"Erro técnico na captura de {url}: {e}")

    # Salva o arquivo final consolidado
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
