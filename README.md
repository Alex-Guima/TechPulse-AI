# TechPulse AI — Fase 1 + Fase 2: Coleta e Persistência de Notícias

## Descrição do projeto

TechPulse AI é um projeto de portfólio cujo objetivo final é ser um agente
inteligente capaz de coletar notícias de tecnologia, resumi-las com IA,
identificar tendências, responder perguntas via RAG e disponibilizar tudo
isso por API e dashboard.

**A Fase 1** construiu a base de coleta: buscar notícias de múltiplas
fontes e padronizá-las em um único modelo de domínio (`Article`).

**A Fase 2** (esta etapa) adiciona a camada de persistência: os artigos
coletados agora são salvos em um banco **PostgreSQL**, com deduplicação
por URL, gerenciamento de schema via **Alembic** e estatísticas de
execução. Ainda não há IA, API web, dashboard, autenticação, cache ou
qualquer funcionalidade além da coleta e persistência.

## Arquitetura

O fluxo de dados agora inclui a etapa de persistência:

```
Fonte → Collector → Normalizer → Article → NewsCollectorService → ArticleRepository → PostgreSQL
                                                                  ↳ Estatísticas → Terminal
```

- **Collectors**: buscam dados brutos na fonte (RSS ou API). Não limpam,
  não resumem, não classificam — apenas coletam.
- **Normalizers**: convertem os dados brutos de cada fonte no modelo
  único `Article`. Toda lógica de transformação vive aqui.
- **Article** (`app/models/article.py`): modelo Pydantic único que
  representa qualquer notícia, independentemente da origem (modelo de
  **domínio**, sem qualquer relação com o banco de dados). `id` é
  sempre a chave primária no banco (preenchida pelo `ArticleRepository`);
  `external_id` é o identificador original da fonte (guid de RSS, id do
  Hacker News etc.), preenchido pelos normalizadores — os dois nunca se
  misturam.
- **NewsCollectorService**: orquestra a execução de todos os coletores e
  normalizadores (`collect_all`), e também a persistência dos artigos
  coletados (`collect_and_persist`). Depende apenas de
  `ArticleRepositoryProtocol` (`app/repositories/article_repository_protocol.py`),
  uma abstração formal (`typing.Protocol`) — nunca de SQLAlchemy ou do
  tipo concreto do repositório.
- **ArticleRepository** (`app/repositories/article_repository.py`): único
  ponto de acesso ao PostgreSQL, implementando `ArticleRepositoryProtocol`.
  Converte entre `Article` (domínio) e `ArticleModel` (ORM) — todo método
  público recebe e retorna exclusivamente objetos de domínio, nunca o
  tipo ORM. Persiste de forma idempotente por URL
  (`INSERT ... ON CONFLICT DO NOTHING`) e isola falhas artigo a artigo em
  `save_many`, registrando-as em `SaveManyResult.failures` sem
  interromper a persistência dos demais.
- **ArticleModel** (`app/database/models.py`): modelo SQLAlchemy da tabela
  `articles`, deliberadamente separado do modelo de domínio `Article`.
- **Settings** (`app/config/settings.py`): configuração centralizada via
  Pydantic Settings, lendo o `.env`.
- **utils**: funções puras e reutilizáveis (limpeza de texto, remoção de
  HTML, parsing de datas).

Essa separação garante baixo acoplamento: novas fontes podem ser
adicionadas criando apenas um novo collector + normalizer, e a camada de
persistência pode evoluir (trocar de banco, adicionar cache, etc.) sem
que o `NewsCollectorService` precise mudar.

## Estrutura de pastas

```text
techpulse-ai/
├── alembic/
│   ├── env.py                    # Integra migrations com Settings/Base
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_create_articles_table.py
│       └── 0002_add_external_id_to_articles.py
├── app/
│   ├── collectors/
│   │   ├── base.py               # Contrato abstrato BaseCollector
│   │   ├── rss_collector.py      # Coletor genérico de RSS (TechCrunch)
│   │   ├── github_collector.py   # Coletor do GitHub Blog (herda RSSCollector)
│   │   ├── hackernews_collector.py
│   │   └── devto_collector.py
│   ├── config/
│   │   └── settings.py           # Configuração centralizada (Pydantic Settings)
│   ├── database/
│   │   ├── base.py               # Base declarativa do SQLAlchemy
│   │   ├── models.py             # ArticleModel (ORM, separado do domínio)
│   │   ├── engine.py             # Engine/session factory (lazy)
│   │   ├── session.py            # session_scope() — commit/rollback centralizados
│   │   └── exceptions.py         # Exceções específicas de persistência
│   ├── models/
│   │   └── article.py            # Modelo de domínio único (Pydantic)
│   ├── normalizers/
│   │   ├── rss_normalizer.py
│   │   ├── github_normalizer.py
│   │   ├── hackernews_normalizer.py
│   │   └── devto_normalizer.py
│   ├── repositories/
│   │   ├── article_repository.py          # ArticleRepository (Repository Pattern)
│   │   └── article_repository_protocol.py # ArticleRepositoryProtocol (abstração formal)
│   ├── services/
│   │   └── news_collector_service.py
│   ├── utils/
│   │   ├── dates.py
│   │   └── text.py
│   └── main.py
├── tests/
├── alembic.ini
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

## Tecnologias

- Python 3.12+
- Pydantic — validação e tipagem do modelo `Article`
- feedparser — leitura de feeds RSS/Atom
- requests — chamadas HTTP às APIs (Hacker News, Dev.to)
- BeautifulSoup4 — remoção de HTML dos textos coletados
- python-dotenv — configuração via variáveis de ambiente
- pytest — testes unitários
- **pydantic-settings** — configuração centralizada e tipada (Fase 2)
- **SQLAlchemy 2.0** — ORM para persistência no PostgreSQL (Fase 2)
- **Alembic** — versionamento e migrations do schema do banco (Fase 2)
- **psycopg2-binary** — driver de conexão com o PostgreSQL (Fase 2)

## Instalação

```bash
git clone <repositorio>
cd techpulse-ai
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuração do PostgreSQL

1. Tenha um PostgreSQL acessível (local, Docker externo ao projeto, ou
   serviço gerenciado). Esta fase não usa Docker nem SQLite.
2. Crie o banco de desenvolvimento (nome definido em `DATABASE_NAME`
   no `.env`, padrão `techpulse`):

   ```bash
   createdb techpulse
   ```

3. Ajuste, se necessário, as credenciais no `.env`:

   ```env
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=techpulse
   DATABASE_USER=postgres
   DATABASE_PASSWORD=postgres
   DATABASE_ECHO=false
   ```

   `DATABASE_ECHO=true` ativa o log das queries SQL executadas pelo
   SQLAlchemy — útil para depuração.

## Execução das migrations

O schema do banco é gerenciado exclusivamente pelo Alembic (não usamos
`create_all()` como solução definitiva). Com o `.env` configurado:

```bash
alembic upgrade head
```

Para reverter a última migration:

```bash
alembic downgrade -1
```

Para criar uma nova migration (após alterar `app/database/models.py`):

```bash
alembic revision --autogenerate -m "descrição da mudança"
```

## Como executar

```bash
python -m app.main
```

A saída no terminal mostra, para cada artigo coletado: título, fonte,
data de publicação e URL — seguido de um relatório com as estatísticas
da execução (fontes consultadas, artigos encontrados, novos registros,
duplicados ignorados, **falhas ao persistir**, total persistido e tempo
de execução). Uma falha ao persistir um artigo específico (ex: dado
inválido) não interrompe a persistência dos demais.

## Como rodar os testes

```bash
pytest
```

Os testes cobrem o modelo `Article`, o contrato `BaseCollector`, todos os
normalizadores e o `NewsCollectorService` — usando fontes e repositórios
falsos (fakes), sem necessidade de acesso à rede ou a um banco real.

Os testes do `ArticleRepository` (`tests/test_article_repository.py`)
precisam de um **PostgreSQL de teste** dedicado, por padrão nomeado
`<DATABASE_NAME>_test` (ex: `techpulse_test`):

```bash
createdb techpulse_test
```

Se esse banco não estiver acessível, esses testes são **pulados
automaticamente** (não falham) — o restante da suíte roda normalmente.
Os testes de rollback/erros de conexão (`tests/test_database_session.py`)
usam apenas mocks e não dependem de banco algum.

## Escopo do projeto

**Fase 1 (concluída):** coleta de TechCrunch, Hacker News, GitHub Blog e
Dev.to; padronização em `Article`; impressão no terminal para validação.

**Fase 2 (esta etapa):** persistência em PostgreSQL via SQLAlchemy 2.0;
schema gerenciado por Alembic; `ArticleRepository` com deduplicação por
URL; estatísticas de coleta/persistência; tratamento de erros específico
(conexão, timeout, falha de inserção).

**Fora de escopo (propositalmente, ainda):** FastAPI, Streamlit, Docker,
IA, OpenAI, embeddings, RAG, chatbot, Telegram, cache, autenticação. Esses
itens serão tratados em etapas futuras do projeto.
