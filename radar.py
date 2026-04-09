import pandas as pd
import requests
import json
import io  # <-- Nova biblioteca nativa do Python adicionada aqui

# URL do portal financeiro
url = "https://investidor10.com.br/acoes/proventos/" 

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def atualizar_dividendos():
    try:
        resposta = requests.get(url, headers=headers)
        
        # Correção: Envolvendo o texto em StringIO para o Pandas não reclamar
        html_lido = io.StringIO(resposta.text)
        
        # O Pandas agora lê usando o StringIO
        tabelas = pd.read_html(html_lido)
        
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

        # Salva o resultado no arquivo JSON
        with open('dividendos.json', 'w', encoding='utf-8') as f:
            json.dump(dados_limpos, f, indent=4, ensure_ascii=False)
            
        print("Arquivo dividendos.json gerado com sucesso!")

    except Exception as e:
        print(f"Erro na captura dos dados: {e}")

if __name__ == "__main__":
    atualizar_dividendos()
