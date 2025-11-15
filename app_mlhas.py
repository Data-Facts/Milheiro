from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep

app = Flask(__name__)

# ======================================================
# Função principal de scraping
# ======================================================
def executar_scraper(var_datas, var_orig, var_dest):
    # Monta a URL com os parâmetros
    base_url = "https://seats.aero/search"
    params = {
        "min_seats": 1,
        "applicable_cabin": "any",
        "additional_days": "true",
        "additional_days_num": 14,
        "max_fees": 40000,
        "disable_live_filtering": "false",
        "date": var_datas,
        "origins": var_orig,
        "destinations": var_dest,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # Faz a requisição
    r = requests.get(base_url, headers=headers, params=params)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Procura a tabela principal
    tabela = soup.select_one("table#DataTables_Table_0 tbody")
    if not tabela:
        return pd.DataFrame()

    dados = []
    for linha in tabela.select("tr"):
        colunas = linha.select("td")
        if not colunas:
            continue

        valores = []
        for col in colunas:
            span = col.find("span")
            if span:
                texto_visivel = span.text.strip()
                tooltip = span.get("data-bs-original-title")
                if tooltip:
                    valores.append(f"{texto_visivel} | tooltip: {tooltip}")
                else:
                    valores.append(texto_visivel)
            else:
                valores.append(col.text.strip())

        dados.append(valores)

    df_final = pd.DataFrame(dados)

    # Ajusta colunas e remove duplicatas
    if not df_final.empty:
        df_final = df_final.iloc[:, :9]
        df_final = df_final.drop_duplicates()
        df_final.columns = [
            'Data', 'Ultima_Visualizacao', 'Programa', 'Origem', 'Destino',
            'Economica', 'Premium', 'Executiva', 'PrimeiraClasse'
        ]

    return df_final


# ======================================================
# Rota da API
# ======================================================
@app.route("/scraper", methods=["GET"])
def scraper():
    origin = request.args.get("origin")
    destination = request.args.get("destination")
    date = request.args.get("date")

    if not origin or not destination or not date:
        return jsonify({
            "error": "Parâmetros obrigatórios: origin, destination, date"
        }), 400

    try:
        df = executar_scraper(date, origin, destination)

        if df.empty:
            return jsonify({"mensagem": "Nenhum dado encontrado."}), 200

        # Retorna o DataFrame em JSON
        return jsonify(df.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
