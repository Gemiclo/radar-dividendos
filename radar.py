"""
Atualiza dividendos.json com proventos de acoes (Dados de Mercado) e FIIs
(Investidor 10).

Revisao de 17/08/2026. Cada mudanca abaixo foi medida antes de ser aplicada,
nao suposta:

1. REQUISICAO DIRETA PRIMEIRO, tunel como fallback.
   Os dois sites responderam 200 com a tabela completa sem proxy nenhum, apenas
   com User-Agent de navegador. O ScraperAPI passa a ser rede de seguranca. Se o
   IP do GitHub Actions for recusado (datacenter costuma ser bloqueado), a cadeia
   cai sozinha para o tunel e nada se perde.

2. UMA PAGINA POR MES, NAO CINCO.
   A pagina do Investidor 10 devolve o mes inteiro: 165 tickers, de ADSH11 a
   ZAGH11, em 295 linhas de tabela. As paginas 1 e 2 vieram identicas ate o
   ultimo byte (1.709.147) — o site ignora o ?page=. As cinco requisicoes
   traziam a mesma coisa cinco vezes, e 40 dos 110 creditos iam para o lixo.

3. MESCLA EM VEZ DE SOBRESCREVER.
   Antes o JSON era reescrito com o que a execucao conseguisse; falha parcial
   APAGAVA proventos ja coletados. Em 14/08 tres das dez requisicoes falharam.
   Agora o arquivo existente e carregado antes e o resultado e a uniao.

4. TUNEL COMUM ANTES DO PREMIUM.
   premium=true custa 10 creditos por requisicao; comum custa 1. O teste mostrou
   os dois sites respondendo no comum.

5. GUARDA DE ORCAMENTO.
   Consulta o saldo da conta (essa chamada nao consome credito) e recusa o
   premium quando resta pouco, para o pipeline nunca zerar o plano sozinho.

Custo por execucao: 0 credito no caminho feliz, 3 se cair no tunel comum,
30 no premium. Antes eram 110 sempre.
"""

import datetime
import io
import json
import os
from urllib.parse import quote

import pandas as pd
import requests

API_KEY = os.environ.get("SCRAPER_API_KEY")

ARQUIVO_SAIDA = "dividendos.json"

# Abaixo disto o premium fica proibido: melhor pular uma execucao do que ficar
# sem creditos no meio do mes.
RESERVA_DE_CREDITOS = 150

TIMEOUT = 45

CABECALHO_NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}

MESES = {
    1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def montar_urls():
    """Uma URL por fonte. O mes passado entra para pegar anuncios do virada."""
    hoje = datetime.date.today()
    mes_passado = hoje.replace(day=1) - datetime.timedelta(days=1)

    return [
        "https://www.dadosdemercado.com.br/agenda-de-dividendos",
        f"https://investidor10.com.br/fiis/dividendos/{hoje.year}/{MESES[hoje.month]}/",
        f"https://investidor10.com.br/fiis/dividendos/{mes_passado.year}/{MESES[mes_passado.month]}/",
    ]


def creditos_restantes():
    """Saldo da conta no ScraperAPI. Esta consulta nao consome credito."""
    if not API_KEY:
        return 0
    try:
        r = requests.get(
            "http://api.scraperapi.com/account",
            params={"api_key": API_KEY},
            timeout=20,
        )
        if r.status_code != 200:
            return 0
        dados = r.json()
        usados = int(dados.get("requestCount", 0))
        limite = int(dados.get("requestLimit", 0))
        return max(0, limite - usados)
    except Exception as e:
        print(f"  [orcamento] nao foi possivel consultar: {e}")
        return 0


def parece_pagina_valida(html):
    """
    Evita tratar pagina de bloqueio como sucesso.

    Cuidado com falso positivo: a pagina legitima do Investidor 10 carrega o
    script do reCAPTCHA no rodape, entao procurar por 'captcha' acusaria
    bloqueio numa pagina perfeitamente boa. O criterio aqui e a presenca da
    tabela e dos rotulos que o parser usa.
    """
    if not html or len(html) < 5000:
        return False
    if "<table" not in html:
        return False
    return any(rotulo in html for rotulo in ("Pagamento", "Data Com", "Pgto", "Registro"))


def buscar_html(url, permitir_premium):
    """
    Cadeia de tentativas, da mais barata para a mais cara:
      1. direta, sem proxy       -> 0 credito
      2. tunel comum             -> 1 credito
      3. tunel premium           -> 10 creditos (so se permitido)

    Devolve (html, origem) ou (None, motivo).
    """
    # 1. Direta
    try:
        r = requests.get(url, headers=CABECALHO_NAVEGADOR, timeout=TIMEOUT)
        if r.status_code == 200 and parece_pagina_valida(r.text):
            return r.text, "direta"
        print(f"  direta nao serviu (status {r.status_code}), tentando tunel...")
    except Exception as e:
        print(f"  direta falhou ({e}), tentando tunel...")

    if not API_KEY:
        return None, "sem SCRAPER_API_KEY para o fallback"

    # A URL alvo precisa ir codificada: ela pode conter ? e &, que senao viram
    # parametros do proprio ScraperAPI.
    alvo = quote(url, safe="")

    # 2. Tunel comum
    try:
        r = requests.get(
            f"http://api.scraperapi.com/?api_key={API_KEY}&url={alvo}",
            timeout=TIMEOUT * 2,
        )
        if r.status_code == 200 and parece_pagina_valida(r.text):
            return r.text, "tunel comum (1 credito)"
        print(f"  tunel comum nao serviu (status {r.status_code})")
    except Exception as e:
        print(f"  tunel comum falhou: {e}")

    # 3. Tunel premium
    if not permitir_premium:
        return None, "premium bloqueado pela guarda de orcamento"
    try:
        r = requests.get(
            f"http://api.scraperapi.com/?api_key={API_KEY}&url={alvo}&premium=true",
            timeout=TIMEOUT * 2,
        )
        if r.status_code == 200 and parece_pagina_valida(r.text):
            return r.text, "tunel premium (10 creditos)"
        return None, f"premium tambem falhou (status {r.status_code})"
    except Exception as e:
        return None, f"premium falhou: {e}"


def extrair_proventos(html):
    """Le a tabela e devolve a lista de proventos daquela pagina."""
    try:
        tabelas = pd.read_html(io.StringIO(html), decimal=",", thousands=".")
    except ValueError:
        return []

    df = None
    for tb in tabelas:
        colunas = set(tb.columns.astype(str))
        if colunas & {"Pagamento", "Data Pagamento", "Data Com"}:
            df = tb
            break
    if df is None:
        return []

    proventos = []
    for _, linha in df.iterrows():
        ativo_cru = str(linha.get("Código", linha.get("Ativo", linha.get("Empresa", ""))))
        ativo = ativo_cru.split()[0] if ativo_cru.strip() else ""

        tipo = str(linha.get("Tipo", "Rendimento")).strip()

        data_com = str(linha.get("Registro", linha.get("Data Com", ""))).replace("Data Com", "").strip()
        data_pag = str(linha.get("Pagamento", linha.get("Data Pagamento", ""))).replace("Pgto", "").strip()
        valor = str(linha.get("Valor (R$)", linha.get("Valor", ""))).split("R$")[-1].strip()

        if ativo and ativo != "nan" and valor and valor != "nan":
            proventos.append({
                "ativo": ativo,
                "tipo": tipo,
                "data_com": data_com,
                "data_pagamento": data_pag,
                "valor": valor,
            })
    return proventos


def carregar_existente():
    """O que ja foi coletado antes. Sem isso, execucao parcial apaga historico."""
    if not os.path.exists(ARQUIVO_SAIDA):
        return []
    try:
        with open(ARQUIVO_SAIDA, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, list) else []
    except Exception as e:
        print(f"AVISO: nao consegui ler {ARQUIVO_SAIDA} ({e}). Seguindo sem base.")
        return []


def deduplicar(lista):
    """
    Dedupe preservando a ordem.

    Usar set() embaralharia o arquivo a cada execucao, e o git veria o JSON
    inteiro mudando mesmo quando nada mudou — impossivel ver no historico
    quando um provento entrou.
    """
    vistos = set()
    saida = []
    for item in lista:
        chave = (item["ativo"], item["tipo"], item["data_com"],
                 item["data_pagamento"], item["valor"])
        if chave not in vistos:
            vistos.add(chave)
            saida.append(item)
    return saida


def atualizar_dividendos():
    saldo = creditos_restantes()
    permitir_premium = saldo > RESERVA_DE_CREDITOS
    print(f"Creditos restantes no ScraperAPI: {saldo}")
    if not permitir_premium:
        print(f"  premium desabilitado nesta execucao (reserva de {RESERVA_DE_CREDITOS})")

    anteriores = carregar_existente()
    print(f"Proventos ja no arquivo: {len(anteriores)}")

    novos = []
    paginas_ok = 0
    for url in montar_urls():
        print(f"\nBuscando: {url}")
        html, origem = buscar_html(url, permitir_premium)
        if html is None:
            print(f"  FALHOU: {origem}")
            continue

        extraidos = extrair_proventos(html)
        print(f"  OK via {origem} — {len(extraidos)} proventos")
        if extraidos:
            paginas_ok += 1
            novos.extend(extraidos)

    if paginas_ok == 0:
        # Nenhuma fonte respondeu: escrever agora so destruiria o que existe.
        print("\nNenhuma pagina respondeu. Arquivo mantido como estava.")
        return

    total = deduplicar(anteriores + novos)
    acrescentados = len(total) - len(anteriores)

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(total, f, indent=4, ensure_ascii=False)

    print(f"\n{len(total)} proventos no arquivo ({acrescentados} novos nesta execucao).")


if __name__ == "__main__":
    if not API_KEY:
        # Nao e mais fatal: a requisicao direta nao usa o ScraperAPI.
        print("AVISO: SCRAPER_API_KEY ausente — sem fallback se a direta falhar.")
    atualizar_dividendos()
