from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd

app = Flask(__name__)


# =============================
# Função para inicializar o driver
# =============================
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


# =============================
# Função que extrai a tabela
# =============================
def pega_tb(driver):
    wait = WebDriverWait(driver, 15)
    tabela = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#DataTables_Table_0 tbody")))

    linhas = tabela.find_elements(By.TAG_NAME, "tr")
    dados = []

    for linha in linhas:
        colunas = linha.find_elements(By.TAG_NAME, "td")
        if not colunas:
            continue

        valores = []
        for col in colunas:
            span = col.find_elements(By.TAG_NAME, "span")

            if span:
                span = span[0]
                texto_visivel = span.text.strip()
                tooltip = span.get_attribute("data-bs-original-title")

                if tooltip:
                    valores.append(f"{texto_visivel} | tooltip: {tooltip}")
                else:
                    valores.append(texto_visivel)
            else:
                valores.append(col.text.strip())

        dados.append(valores)

    df = pd.DataFrame(dados)
    return df


# =============================
# ROTA PRINCIPAL DO SCRAPER
# =============================
@app.route("/scraper", methods=["GET"])
def scraper():
    try:
        # parâmetros da URL
        var_datas = request.args.get("date")
        var_orig = request.args.get("orig")
        var_dest = request.args.get("dest")

        if not var_datas or not var_orig or not var_dest:
            return jsonify({"error": "Parâmetros faltando! Use date, orig, dest"}), 400

        # monta a URL
        url = (
            f"https://seats.aero/search?min_seats=1&applicable_cabin=any&additional_days=true"
            f"&additional_days_num=14&max_fees=40000&disable_live_filtering=false&date={var_datas}"
            f"&origins={var_orig}&destinations={var_dest}"
        )

        driver = create_driver()
        driver.get(url)
        sleep(2)

        wait = WebDriverWait(driver, 10)

        # captura botões de paginação
        btos = driver.find_elements(
            By.XPATH,
            "//button[contains(@class, 'page-link') "
            "and not(contains(@class, 'next')) "
            "and not(contains(@class, 'previous'))]"
        )

        df_final = pd.DataFrame()

        for i in range(len(btos)):
            btos = driver.find_elements(
                By.XPATH,
                "//button[contains(@class, 'page-link') "
                "and not(contains(@class, 'next')) "
                "and not(contains(@class, 'previous'))]"
            )
            btn = btos[i]

            page_num = btn.text

            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            sleep(1)
            driver.execute_script("arguments[0].click();", btn)
            print(f"Clicou na página: {page_num}")
            sleep(2)

            df_temp = pega_tb(driver)
            df_final = pd.concat([df_final, df_temp], ignore_index=True)

        # organiza e renomeia
        df_final = df_final.iloc[:, :9]
        df_final.drop_duplicates(inplace=True)

        df_final.columns = [
            "Data", "Ultima_Visualizacao", "Programa", "Origem",
            "Destino", "Economica", "Premium", "Executiva", "PrimeiraClasse"
        ]

        driver.quit()

        # retorna como JSON
        return jsonify(df_final.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
