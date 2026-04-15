import pandas as pd
import requests
import json
import io
import time
from datetime import datetime

# Define o limite matemático para 5 anos atrás
ano_atual = datetime.now().year 
ano_limite = ano_atual - 5      

def baixar_historico_todos_fiis():
    print("Fase 1: Descobrindo todos os FIIs da Bolsa (Via Fundamentus)...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    try:
        resposta_lista = requests.get("https://fundamentus.com.br/fii_resultado.php", headers=headers)
        html_lista = io.StringIO(resposta_lista.text)
        df_lista = pd.read_html(html_lista)[0]
        
        # Linha ativada: vai buscar todos os 500+ fundos da bolsa
        tickers = df_lista['Papel'].tolist()
        print(f"Sucesso! Encontrados {len(tickers)} Fundos Imobiliários na B3.")
    except Exception as e:
        print(f"Erro ao buscar a lista mestre de FIIs: {e}")
        return

    print(f"\nFase 2: Baixando histórico de 5 anos para {len(tickers)} ativos via Fundamentus...")
    print("Isso vai levar alguns minutos. Pode ir pegar um café ☕\n")
    
    dados_historicos = []

    for ticker in tickers:
        ticker_limpo = str(ticker).strip().upper()
        
        url_alvo = f"https://fundamentus.com.br/fii_proventos.php?papel={ticker_limpo}&tipo=2"
        
        try:
            resposta = requests.get(url_alvo, headers=headers)
            
            if resposta.status_code != 200:
                print(f"[{ticker_limpo}] Página indisponível.")
                continue

            html_lido = io.StringIO(resposta.text)
            
            try:
                # O segredo das casas decimais perfeitas está ativado aqui
                tabelas = pd.read_html(html_lido, decimal=',', thousands='.')
            except ValueError:
                print(f"[{ticker_limpo}] Tabela não encontrada no HTML.")
                continue

            tabela_encontrada = False
            for tb in tabelas:
                if 'Última Data Com' in tb.columns or 'Data de Pagamento' in tb.columns:
                    contador_ativo = 0
                    
                    for index, row in tb.iterrows():
                        tipo = str(row.get('Tipo', 'Rendimento'))
                        data_com = str(row.get('Última Data Com', row.get('Data', '')))
                        data_pagamento = str(row.get('Data de Pagamento', ''))
                        valor = str(row.get('Valor', ''))

                        if data_com == 'nan' or data_com == '-' or data_com == '':
                            continue

                        try:
                            ano_com = int(data_com.split('/')[-1])
                            
                            # Filtro atualizado: Apenas dividendos dos últimos 5 anos
                            if ano_com >= ano_limite:
                                dados_historicos.append({
                                    "ativo": ticker_limpo,
                                    "tipo": tipo.strip(),
                                    "data_com": data_com.strip(),
                                    "data_pagamento": data_pagamento.strip(),
                                    "valor": valor.strip()
                                })
                                contador_ativo += 1
                        except ValueError:
                            pass 
                    
                    if contador_ativo > 0:
                        print(f"[{ticker_limpo}] ✔️ {contador_ativo} rendimentos extraídos.")
                        tabela_encontrada = True
                        break
                        
            if not tabela_encontrada:
                print(f"[{ticker_limpo}] Sem histórico de dividendos nos últimos 5 anos.")

        except Exception as e:
            print(f"[{ticker_limpo}] Erro técnico ao ler os dados.")
            
        time.sleep(2)

    dados_unicos = [dict(t) for t in {tuple(d.items()) for d in dados_historicos}]

    if len(dados_unicos) > 0:
        # Atualizei o nome do arquivo final para refletir os 5 anos
        with open('historico_fiis_5_anos.json', 'w', encoding='utf-8') as f:
            json.dump(dados_unicos, f, indent=4, ensure_ascii=False)
        print(f"\n🚀 CARGA CONCLUÍDA! {len(dados_unicos)} rendimentos salvos no historico_fiis_5_anos.json")
    else:
        print("\nErro: Nenhum dado histórico foi salvo no processo.")

if __name__ == "__main__":
    baixar_historico_todos_fiis()