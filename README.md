# Milheiro API

Microserviço em Flask que consulta o [seats.aero](https://seats.aero/) usando `requests` + `BeautifulSoup` e expõe a disponibilidade de assentos como JSON. Todo o scraping acontece em modo headless (sem Selenium) e o projeto foi otimizado para rodar como serviço web no Render.

## Requisitos

- Python 3.11+
- `pip` para instalar as dependências listadas em `requirements.txt`

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Estrutura

```
.
├── app.py            # aplicação Flask padrão com as rotas HTTP
├── milheiro/
│   └── scraper.py    # lógica de scraping reutilizável
├── requirements.txt  # dependências mínimas (Flask, gunicorn, bs4, requests)
├── render.yaml       # blueprint de deploy no Render
└── wsgi.py           # entrypoint WSGI apontado pelo Gunicorn
```

## Variáveis de ambiente

| Nome | Descrição | Default |
| --- | --- | --- |
| `SEATS_AERO_URL` | URL base do seats.aero a ser consultada | `https://seats.aero/search` |
| `HTTP_TIMEOUT` | Tempo máximo (segundos) para aguardar resposta do seats.aero | `30` |
| `SCRAPER_MIN_SEATS` | Quantidade mínima de assentos buscados | `1` |
| `SCRAPER_APPLICABLE_CABIN` | Cabine (`any`, `economy`, `business`, etc.) | `any` |
| `SCRAPER_ADDITIONAL_DAYS` | Expande a busca para datas próximas (`true`/`false`) | `true` |
| `SCRAPER_ADDITIONAL_DAYS_NUM` | Dias extras considerados quando `additional_days=true` | `14` |
| `SCRAPER_MAX_FEES` | Taxas máximas aceitas (em milhas) | `40000` |
| `SCRAPER_DISABLE_LIVE_FILTERING` | Mantém ou não o live filtering do seats.aero | `false` |

Essas variáveis podem ser definidas localmente ou diretamente no painel do Render para personalizar o scraping sem tocar no código.

## Execução local

### 1. Via script Python (modo simples)

```bash
python app.py
```

### 2. Via Flask CLI (mantém auto-reload durante o desenvolvimento)

```bash
export FLASK_APP=app:app
flask run --debug
```

### 3. Via Gunicorn (simulando produção)

```bash
gunicorn wsgi:app
```

Com o serviço em execução, teste os endpoints:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/healthz
curl "http://127.0.0.1:5000/scraper?origin=GRU&destination=MIA&date=2024-07-01"
```

## Deploy no Render

1. Faça um fork ou envie este repositório para o GitHub.
2. No dashboard do Render clique em **New +** → **Blueprint** e informe a URL do repositório.
3. Confirme o uso do `render.yaml` deste projeto.
4. Em **Environment Variables**, configure os valores desejados (por exemplo `SCRAPER_MIN_SEATS`).
5. Crie o serviço. O Render executará automaticamente:
   - `pip install -r requirements.txt` durante o build;
   - `gunicorn wsgi:app` como comando de inicialização.
6. Quando o deploy terminar, teste:

```bash
curl "https://<sua-instancia>.onrender.com/scraper?origin=GRU&destination=MIA&date=2024-07-01"
```

O arquivo `render.yaml` garante que você reproduza o mesmo processo em outros ambientes compatíveis com contêineres (Railway, Fly.io, etc.) bastando manter o mesmo comando de inicialização.
