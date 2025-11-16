# Milheiro API

Serviço em Flask que consulta o [seats.aero](https://seats.aero/) e expõe os resultados de disponibilidade de assentos via HTTP.
O projeto foi estruturado como uma aplicação Flask padrão (factory, blueprint e handlers de erro) para facilitar o deploy em qualquer
plataforma compatível com WSGI, incluindo o Render.

## Requisitos

- Python 3.11+
- `pip` ou `uv` para instalar as dependências listadas em `requirements.txt`

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Estrutura

```
.
├── app.py            # entrypoint para `python app.py`
├── milheiro/
│   ├── __init__.py   # factory e registro dos blueprints/erros
│   ├── config.py     # configurações carregadas via variáveis de ambiente
│   ├── errors.py     # responses JSON para exceções
│   ├── routes.py     # rotas Flask
│   └── scraper.py    # utilitários de scraping (requests + BeautifulSoup)
├── requirements.txt
├── render.yaml       # blueprint do Render
└── wsgi.py           # entrypoint WSGI usado pelo Gunicorn
```

## Variáveis de ambiente

| Nome | Descrição | Default |
| --- | --- | --- |
| `SEATS_AERO_URL` | URL base do seats.aero a ser consultada | `https://seats.aero/search` |
| `HTTP_TIMEOUT` | Tempo máximo (segundos) para aguardar resposta do seats.aero | `30` |
| `SCRAPER_*` | Ajustam os filtros padrão enviados ao seats.aero (ver `milheiro/config.py`) | valores do site |

Todas as variáveis podem ser configuradas localmente ou no painel do Render sem alterar o código.

## Execução local

### 1. Com o Flask CLI (modo recomendado durante o desenvolvimento)

```bash
export FLASK_APP=wsgi:app
flask run --debug
```

### 2. Via script Python

```bash
python app.py
```

### 3. Via Gunicorn (simulando produção)

```bash
gunicorn wsgi:app
```

Depois de subir o serviço, teste os endpoints:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/healthz
curl "http://127.0.0.1:5000/scraper?origin=GRU&destination=MIA&date=2024-07-01"
```

## Deploy no Render

1. Faça o fork ou envie este repositório para o GitHub.
2. No dashboard do Render clique em **New +** → **Blueprint**.
3. Informe a URL do repositório e confirme o uso do arquivo `render.yaml`.
4. Em **Environment Variables**, configure as variáveis desejadas (por exemplo `SEATS_AERO_URL`).
5. Crie o serviço. O Render executará automaticamente:
   - `pip install -r requirements.txt` durante o build;
   - `gunicorn wsgi:app` como comando de inicialização.
6. Aguarde o provisionamento. Quando o deploy terminar, utilize o endpoint público informado pelo Render:

```bash
curl "https://<sua-instancia>.onrender.com/scraper?origin=GRU&destination=MIA&date=2024-07-01"
```

O arquivo `render.yaml` serve como fonte única da infraestrutura, permitindo reproduzir o mesmo deploy em outros ambientes
compatíveis com containers (Fly.io, Railway, etc.) apenas ajustando o comando de inicialização se necessário.
