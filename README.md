# Milheiro API

API em Flask utilizada para consultar o site [seats.aero](https://seats.aero/) e retornar a tabela de disponibilidade de assentos utilizando web scraping feito com `requests` + `BeautifulSoup`.

## Requisitos

- Python 3.11+
- Dependências listadas em `requirements.txt`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Como executar localmente

```bash
export FLASK_APP=wsgi:app
flask run --debug
```

Endpoints disponíveis:

- `GET /healthz` – usado pelo Render para verificar se o serviço está no ar.
- `GET /scraper?origin=GRU&destination=MIA&date=2024-07-01` – retorna um JSON com os dados encontrados no seats.aero. Todos os parâmetros são obrigatórios e os códigos de aeroporto devem estar no formato IATA (3 letras).

Variáveis de ambiente opcionais:

- `SEATS_AERO_URL` – altera o domínio consultado (default: `https://seats.aero/search`).
- `HTTP_TIMEOUT` – tempo máximo (em segundos) para a requisição HTTP (default: `30`).

## Deploy no Render

O arquivo `render.yaml` já traz uma configuração mínima para criar um serviço web Python. Depois de criar o repositório no GitHub:

1. Acesse o dashboard do Render e escolha **New +** → **Blueprint**.
2. Informe a URL do repositório e selecione o arquivo `render.yaml` como blueprint.
3. O Render instalará as dependências com `pip install -r requirements.txt` e iniciará a aplicação usando `gunicorn wsgi:app`.

A aplicação ficará disponível em um endereço público e poderá ser consultada com qualquer cliente HTTP.
