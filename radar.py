import pandas as pd
import requests
import json
import io
import os

API_KEY = os.environ.get("SCRAPER_API_KEY")

# 1. A página de ações não tem paginação forte, então vai normal
urls_alvo = ["https://www.dadosdemercado.com.br/agenda-de-dividendos"]

# 2. Criamos as URLs do Investidor10 da página 1 até a 5
for pagina in range(1, 6):
    urls_alvo.append(f"https://investidor10.com.br/fiis/dividendos/?page={pagina}")

def atualizar_dividendos():
    print("Iniciando o túnel Premium (ScraperAPI) com Paginação...")
    
    dados_totais = [] 

    for url in urls_alvo:
        url_tunel = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url}&premium=true"
        
        try:
            print(f"\nBuscando dados de: {url}")
            resposta = requests.get(url_tunel)
            
            if resposta.status_code != 200:
                print(f"Erro ou fim das páginas em {url}. Status: {resposta.status_code}")
                continue 

            html_lido = io.StringIO(resposta.text)
            
            # Se não houver tabelas (ex: chegou numa página que não existe mais FII), ele ignora e segue
            try:
                tabelas = pd.read_html(html_lido)
            except ValueError:
                print("Nenhuma tabela HTML encontrada nesta página. Passando para a próxima...")
                continue
            
            df_correto = None
            for tb in tabelas:
                if 'Pagamento' in tb.columns or 'Data Pagamento' in tb.columns or 'Data Com' in tb.columns:
                    df_correto = tb
                    break
                    
            if df_correto is not None:
                contador = 0
                for index, row in df_correto.iterrows():
                    
                    ativo_cru = str(row.get('Código', row.get('Ativo', row.get('Empresa', ''))))
                    ativo = ativo_cru.split()[0] if ativo_cru else ''
                    
                    tipo = str(row.get('Tipo', 'Rendimento')) 
                    
                    data_com_cru = str(row.get('Registro', row.get('Data Com', '')))
                    data_com = data_com_cru.replace('Data Com', '').strip()
                    
                    data_pag_cru = str(row.get('Pagamento', row.get('Data Pagamento', '')))
                    data_pagamento = data_pag_cru.replace('Pgto', '').strip()
                    
                    valor_cru = str(row.get('Valor (R$)', row.get('Valor', '')))
                    valor = valor_cru.split('R$')[-1].strip()
                    
                    if ativo and ativo != 'nan' and valor and valor != 'nan':
                        dados_totais.append({
                            "ativo": ativo,
                            "tipo": tipo.strip(),
                            "data_com": data_com,
                            "data_pagamento": data_pagamento,
                            "valor": valor
                        })
                        contador += 1
                
                print(f"Sucesso! {contador} proventos extraídos.")
            else:
                print("Aviso: Nenhuma tabela válida nesta página específica.")

        except Exception as e:
            print(f"Erro técnico na captura de {url}: {e}")

    # Remove duplicatas (caso algum FII apareça em duas páginas por atualização do site)
    dados_unicos = [dict(t) for t in {tuple(d.items()) for d in dados_totais}]

    if len(dados_unicos) > 0:
        with open('dividendos.json', 'w', encoding='utf-8') as f:
            json.dump(dados_unicos, f, indent=4, ensure_ascii=False)
        print(f"\nVITÓRIA ABSOLUTA! {len(dados_unicos)} dividendos (Ações + FIIs) salvos no dividendos.json")
    else:
        print("\nErro crítico: Nenhum dado foi salvo no processo.")

if __name__ == "__main__":
    if not API_KEY:
        print("ERRO: A chave SCRAPER_API_KEY não foi encontrada nas variáveis.")
    else:
        atualizar_dividendos()
