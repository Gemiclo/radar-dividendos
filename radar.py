import pandas as pd
import json
import time
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Trocamos o alvo para um site mais amigável para extração
url = "https://www.dadosdemercado.com.br/dividendos"

def atualizar_dividendos():
    print("Iniciando navegador invisível...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=chrome_options)
    
    try:
        print(f"Acessando o portal: {url}")
        navegador.get(url)
        
        # Esperando a página carregar
        print("Aguardando carregamento...")
        time.sleep(5) 
        
        html = navegador.page_source
        html_lido = io.StringIO(html)
        
        print("Procurando tabelas no site...")
        tabelas = pd.read_html(html_lido)
        print(f"Encontrei {len(tabelas)} tabela(s) na página.")
        
        df_correto = None
        
        # O robô agora procura a tabela certa analisando o nome das colunas
        for tb in tabelas:
            # Se a tabela tiver a coluna 'Data Com' ou 'Pagamento', é a que queremos!
            if 'Data Com' in tb.columns or 'Pagamento' in tb.columns:
                df_correto = tb
                break
        
        if df_correto is not None:
            dados_limpos = []
            print("Tabela correta encontrada! Extraindo os dados...")
            
            for index, row in df_correto.iterrows():
                # O .get() tenta pegar a coluna. Se o site mudar o nome para maiúsculo, ajustamos aqui.
                ativo = str(row.get('Ativo', row.get('ATIVO', '')))
                tipo = str(row.get('Tipo', row.get('TIPO', '')))
                data_com = str(row.get('Data Com', row.get('DATA COM', '')))
                data_pagamento = str(row.get('Pagamento', row.get('PAGAMENTO', '')))
                valor = str(row.get('Valor', row.get('VALOR', '')))
                
                # Só adiciona se tiver um ativo válido (para evitar linhas em branco)
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
        else:
            print("Nenhuma tabela de dividendos foi encontrada. O site pode ter bloqueado o acesso.")

    except Exception as e:
        print(f"Erro na captura: {e}")
        
    finally:
        navegador.quit()
        print("Navegador fechado.")

if __name__ == "__main__":
    atualizar_dividendos()
