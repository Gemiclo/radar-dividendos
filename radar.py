import pandas as pd
import requests
import json
import io
import os
import datetime

API_KEY = os.environ.get("SCRAPER_API_KEY")

# 1. Ações (O site Dados de Mercado lista os pagamentos futuros normalmente)
urls_alvo = [
    "https://www.dadosdemercado.com.br/agenda-de-dividendos" 
]

# 2. Construção Inteligente dos Links de FIIs (Mês Atual + Mês Passado)
meses = {1: 'janeiro', 2: 'fevereiro', 3: 'marco', 4: 'abril', 5: 'maio', 6: 'junho', 
         7: 'julho', 8: 'agosto', 9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'}

hoje = datetime.date.today()

# URL do Mês Atual (ex: /2026/abril/)
url_atual = f"https://investidor10.com.br/fiis/dividendos/{hoje.year}/{meses[hoje.month]}/"

# Calcula matematicamente o mês passado para pegar os anúncios do último dia útil
primeiro_dia_mes_atual = hoje.replace(day=1)
data_mes_passado = primeiro_dia_mes_atual - datetime.timedelta(days=1)

# URL do Mês Passado (ex: /2026/marco/)
url_passado = f"https://investidor10.com.br/fiis/dividendos/{data_mes_passado.year}/{meses[data_mes_passado.month]}/"

# Adiciona ao robô as páginas 1, 2 e 3 tanto do mês atual quanto do mês passado
for pagina in range(1, 4):
    urls_alvo.append(f"{url_atual}?page={pagina}")
    urls_alvo.append(f"{url_passado}?page={pagina}")


def atualizar_dividendos():
    print("Iniciando o túnel Premium (ScraperAPI) com Máquina do Tempo...")
    
    dados_totais = [] 

    for url in urls_alvo:
        url_tunel = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url}&premium=true"
        
        try:
            print(f"\nBuscando dados de: {url}")
            resposta = requests.get(url_tunel)
            
            if resposta.status_code != 200:
                print(f"Fim das páginas nesta URL. Status: {resposta.status_code}")
                continue 

            html_lido = io.StringIO(resposta.text)
            
            try:
                tabelas = pd.read_html(html_lido, decimal=',', thousands='.')
            except ValueError:
                print("Nenhuma tabela encontrada nesta página. Passando...")
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
                print("Aviso: Nenhuma tabela válida nesta página.")

        except Exception as e:
            print(f"Erro técnico na captura de {url}: {e}")

    # Remove os duplicados mantendo a integridade da lista final
    dados_unicos = [dict(t) for t in {tuple(d.items()) for d in dados_totais}]

    if len(dados_unicos) > 0:
        with open('dividendos.json', 'w', encoding='utf-8') as f:
            json.dump(dados_unicos, f, indent=4, ensure_ascii=False)
        print(f"\nVITÓRIA ABSOLUTA! {len(dados_unicos)} dividendos únicos salvos no JSON.")
    else:
        print("\nErro crítico: Nenhum dado foi salvo.")

if __name__ == "__main__":
    if not API_KEY:
        print("ERRO: A chave SCRAPER_API_KEY não foi encontrada nas variáveis.")
    else:
        atualizar_dividendos()
