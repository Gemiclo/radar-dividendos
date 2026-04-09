import pandas as pd
import json
import time
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

url = "https://investidor10.com.br/acoes/proventos/"

def atualizar_dividendos():
    print("Iniciando navegador invisível...")
    
    # Configurações para o Chrome rodar silenciosamente em servidores (GitHub Actions)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Modo invisível atualizado
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    # Instala e abre o Chrome
    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=chrome_options)
    
    try:
        print("Acessando o portal financeiro...")
        navegador.get(url)
        
        # Espera 5 segundos para o JavaScript carregar a tabela e passar por verificações
        print("Aguardando carregamento da tabela...")
        time.sleep(6) 
        
        # Pega o HTML da página DEPOIS de totalmente carregada
        html = navegador.page_source
        html_lido = io.StringIO(html)
        
        # O Pandas agora lê a página já pronta
        tabelas = pd.read_html(html_lido)
        
        if len(tabelas) > 0:
            df = tabelas[0]
            dados_limpos = []
            
            for index, row in df.iterrows():
                dados_limpos.append({
                    "ativo": str(row.get('Ativo', '')),
                    "tipo": str(row.get('Tipo', '')),
                    "data_com": str(row.get('Data Com', '')),
                    "data_pagamento": str(row.get('Pagamento', '')),
                    "valor": str(row.get('Valor', ''))
                })

            with open('dividendos.json', 'w', encoding='utf-8') as f:
                json.dump(dados_limpos, f, indent=4, ensure_ascii=False)
                
            print(f"Sucesso! {len(dados_limpos)} dividendos salvos em dividendos.json")
        else:
            print("Nenhuma tabela encontrada na página carregada.")

    except Exception as e:
        print(f"Erro na captura: {e}")
        
    finally:
        # É importante fechar o navegador no final para não travar o servidor
        navegador.quit()

if __name__ == "__main__":
    atualizar_dividendos()
