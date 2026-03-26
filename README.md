# Dinamica Budget — Backend API

> **Sistema de orçamentação de obras on-premise** que substitui processos manuais de copy/paste em planilhas Excel por uma API centralizada com motor de busca inteligente em cascata de 4 fases.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Stack Tecnológica](#stack-tecnológica)
- [Arquitetura](#arquitetura)
- [Modelo de Dados V2](#modelo-de-dados-v2)
- [Motor de Busca em Cascata (4 Fases)](#motor-de-busca-em-cascata-4-fases)
- [Endpoints da API](#endpoints-da-api)
- [Autenticação e RBAC](#autenticação-e-rbac)
- [Fluxo de Homologação](#fluxo-de-homologação)
- [Sistema de Auditoria](#sistema-de-auditoria)
- [Módulos ML (On-Premise)](#módulos-ml-on-premise)
- [Migrations Alembic](#migrations-alembic)
- [Setup e Instalação](#setup-e-instalação)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Testes](#testes)
- [Plano de Implementação V2](#plano-de-implementação-v2)
- [Riscos Técnicos e Mitigações](#riscos-técnicos-e-mitigações)

---

## Visão Geral

O **Dinamica Budget** é uma aplicação backend on-premise para empresas de construção civil que precisam:

- **Buscar serviços TCPO** a partir de texto livre (ex: "escavação manual solo argiloso")
- **Gerenciar itens próprios** (PROPRIA) por cliente, com fluxo de homologação
- **Aprender com confirmações** do usuário via associações inteligentes que se consolidam com o tempo
- **Explodir composições TCPO** (estrutura pai-filho com insumos, horas, materiais)
- **Registrar histórico** de buscas por cliente com rastreabilidade total
- **Auditar alterações** de preço e status com log imutável em JSONB

A solução é totalmente **on-premise**: nenhum dado sai da rede interna. O modelo de linguagem (`all-MiniLM-L6-v2`) roda localmente via `sentence-transformers`.

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Framework Web | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async + asyncpg) |
| Banco de Dados | PostgreSQL 16 |
| Busca Vetorial | pgvector (HNSW, Vector(384)) |
| Busca Fuzzy | pg_trgm + GIN index |
| Embeddings | Sentence Transformers `all-MiniLM-L6-v2` (on-premise) |
| Autenticação | JWT (access 30min + refresh 7 dias) |
| Migrações | Alembic (async) |
| Logging | structlog (JSON estruturado) |
| Validação | Pydantic v2 |
| Container | Docker + Docker Compose |

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                         FastAPI App                              │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│  │  auth.py    │   │  busca.py    │   │  homologacao.py    │   │
│  │  /login     │   │  /servicos   │   │  /pendentes        │   │
│  │  /refresh   │   │  /associar   │   │  /aprovar          │   │
│  └─────────────┘   └──────┬───────┘   │  /itens-proprios   │   │
│                            │           └────────────────────┘   │
│                   ┌────────▼────────┐                           │
│                   │  busca_service  │  ← Orquestrador Cascata   │
│                   │  (4 fases)      │                           │
│                   └────────┬────────┘                           │
│          ┌─────────────────┼─────────────────┐                  │
│          ▼                 ▼                 ▼                  │
│  ┌───────────────┐ ┌─────────────┐ ┌────────────────┐          │
│  │ assoc_repo    │ │ servico_repo│ │ embed_repo     │          │
│  │ (fase 0+1)    │ │ (fase 2)    │ │ (fase 3)       │          │
│  └───────┬───────┘ └──────┬──────┘ └───────┬────────┘          │
└──────────┼────────────────┼────────────────┼───────────────────┘
           │                │                │
           ▼                ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│                        PostgreSQL 16                             │
│                                                                  │
│  associacao_inteligente   servico_tcpo + pg_trgm   tcpo_embeddings│
│  (texto_normalizado)      (GIN index)               (pgvector)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Estrutura de Pastas

```
dinamica-budget/
├── app/
│   ├── main.py                          # FastAPI factory + lifespan + middleware
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/
│   │       ├── auth.py
│   │       ├── busca.py                 # /busca/servicos + /busca/associar
│   │       ├── servicos.py              # catálogo TCPO + explosão composição
│   │       ├── homologacao.py           # fluxo de aprovação V2
│   │       └── admin.py                 # compute-embeddings, cache-refresh
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings (.env)
│   │   ├── database.py                  # AsyncEngine + session factory
│   │   ├── security.py                  # JWT encode/decode + bcrypt
│   │   ├── dependencies.py              # Depends: get_db, get_current_user
│   │   ├── logging.py                   # JSON structured logging (structlog)
│   │   ├── audit_hooks.py               # SQLAlchemy after_flush hooks (V2)
│   │   └── exceptions.py               # DinamicaException hierarchy + handlers
│   ├── models/
│   │   ├── enums.py                     # Todos os Enum centralizados (V2)
│   │   ├── base.py                      # DeclarativeBase + TimestampMixin
│   │   ├── cliente.py
│   │   ├── categoria_recurso.py
│   │   ├── servico_tcpo.py              # + campos de governança V2
│   │   ├── composicao_tcpo.py           # explosão pai-filho
│   │   ├── tcpo_embeddings.py
│   │   ├── historico_busca_cliente.py
│   │   ├── associacao_inteligente.py    # Substitui associacao_tcpo (V2)
│   │   ├── auditoria_log.py             # Log imutável JSONB (V2)
│   │   └── usuario.py                   # + UsuarioPerfil + external_id_ad (V2)
│   ├── schemas/
│   │   ├── common.py
│   │   ├── auth.py
│   │   ├── busca.py                     # DTOs oficiais + score_confianca (V2)
│   │   ├── servico.py
│   │   └── homologacao.py               # DTOs homologação (V2)
│   ├── services/
│   │   ├── busca_service.py             # Orquestrador 4 fases (V2)
│   │   ├── auth_service.py
│   │   ├── homologacao_service.py       # Workflow aprovação (V2)
│   │   ├── associacao_service.py
│   │   ├── servico_catalog_service.py   # + DFS anti-loop + price roll-up (V2)
│   │   └── embedding_sync_service.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── cliente_repository.py
│   │   ├── servico_tcpo_repository.py   # + fuzzy_search_scoped (V2)
│   │   ├── tcpo_embeddings_repository.py
│   │   ├── historico_repository.py
│   │   └── associacao_repository.py     # + normalize_text + fortalecer (V2)
│   └── ml/
│       ├── embedder.py                  # Singleton SentenceTransformer
│       ├── vector_search.py             # pgvector cosine similarity
│       └── fuzzy_search.py             # pg_trgm (primary) + rapidfuzz (fallback)
├── alembic/versions/
│   ├── 001_create_base_tables.py
│   ├── 002_pgvector_extension.py
│   ├── 003_tcpo_embeddings_table.py
│   ├── 004_gin_fulltext_index.py
│   └── 005_v2_governance_rbac_audit.py  # Governança + RBAC + Auditoria
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

---

## Modelo de Dados V2

### `cliente`
| Campo | Tipo | Restrições |
|---|---|---|
| id | UUID (PK) | v4 |
| nome_fantasia | VARCHAR(255) | NOT NULL |
| cnpj | VARCHAR(14) | UNIQUE, NOT NULL |
| created_at | TIMESTAMP | server_default=now() |
| is_active | BOOLEAN | DEFAULT TRUE |

### `usuario`
| Campo | Tipo | Restrições |
|---|---|---|
| id | UUID (PK) | v4 |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| nome | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| is_admin | BOOLEAN | DEFAULT FALSE |
| external_id_ad | VARCHAR(255) | UNIQUE (AD/LDAP) |
| created_at | TIMESTAMP | |

### `usuario_perfil` (RBAC — V2)
| Campo | Tipo | Restrições |
|---|---|---|
| id | UUID (PK) | v4 |
| usuario_id | UUID (FK) | → usuario.id |
| cliente_id | UUID (FK) | → cliente.id |
| perfil | ENUM | CRIADOR / APROVADOR / ADMIN |

### `categoria_recurso`
| Campo | Tipo | Restrições |
|---|---|---|
| id | INT (PK) | |
| descricao | VARCHAR(100) | NOT NULL |
| tipo_custo | VARCHAR(50) | HORISTA / MENSALISTA / GLOBAL |

### `servico_tcpo` (catálogo central + governança V2)
| Campo | Tipo | Restrições |
|---|---|---|
| id | UUID (PK) | v4 |
| codigo_origem | VARCHAR(50) | NOT NULL, INDEX |
| descricao | TEXT | NOT NULL |
| unidade_medida | VARCHAR(20) | NOT NULL |
| custo_unitario | DECIMAL(15,4) | NOT NULL |
| categoria_id | INT (FK) | → categoria_recurso.id |
| cliente_id | UUID (FK, nullable) | NULL = item global TCPO |
| origem | ENUM | TCPO / PROPRIA |
| status_homologacao | ENUM | PENDENTE / APROVADO / REPROVADO |
| aprovado_por_id | UUID (FK, nullable) | → usuario.id |
| data_aprovacao | TIMESTAMP | nullable |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |
| deleted_at | TIMESTAMP | NULL = ativo (soft delete) |

> Itens TCPO globais têm `cliente_id = NULL` e `origem = TCPO`. Itens criados por clientes têm `origem = PROPRIA` e iniciam com `status_homologacao = PENDENTE`.

### `composicao_tcpo` (explosão pai-filho)
| Campo | Tipo | Restrições |
|---|---|---|
| id | UUID (PK) | v4 |
| servico_pai_id | UUID (FK) | → servico_tcpo.id, INDEX |
| insumo_filho_id | UUID (FK) | → servico_tcpo.id |
| quantidade_consumo | DECIMAL(10,4) | NOT NULL |

> Inserção validada por DFS anti-loop antes de cada INSERT. Custo pai PROPRIA recalculado automaticamente quando custo filho muda.

### `tcpo_embeddings` (pgvector)
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (FK = PK) | = servico_tcpo.id (1:1) |
| vetor | Vector(384) | all-MiniLM-L6-v2 |
| metadata | JSONB | `{descricao, categoria_id}` |

> Índice: `HNSW (m=16, ef_construction=64)` com `vector_cosine_ops`

### `historico_busca_cliente`
| Campo | Tipo | Restrições |
|---|---|---|
| id | UUID (PK) | v4 |
| cliente_id | UUID (FK) | → cliente.id |
| texto_busca | TEXT | NOT NULL |
| usuario_origem | VARCHAR(100) | NOT NULL |
| criado_em | TIMESTAMP | server_default=now() |

### `associacao_inteligente` (V2 — substitui associacao_tcpo)
| Campo | Tipo | Restrições |
|---|---|---|
| id | UUID (PK) | v4 |
| cliente_id | UUID (FK) | → cliente.id |
| texto_busca_original | VARCHAR(255) | NOT NULL |
| texto_busca_normalizado | VARCHAR(255) | NOT NULL, INDEX |
| servico_tcpo_id | UUID (FK) | → servico_tcpo.id |
| origem_associacao | ENUM | MANUAL_USUARIO / IA_CONSOLIDADA |
| confiabilidade_score | DECIMAL(3,2) | |
| frequencia_uso | INT | DEFAULT 1 |
| status_validacao | ENUM | SUGERIDA / VALIDADA / CONSOLIDADA |
| created_at | TIMESTAMP | |

> `status_validacao` evolui: SUGERIDA → VALIDADA (1ª confirmação) → CONSOLIDADA (3+ confirmações). Fase 1 faz circuit break apenas em CONSOLIDADA.

### `auditoria_log` (V2)
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| tabela | VARCHAR(100) | ex: "servico_tcpo" |
| registro_id | UUID | ID do registro alterado |
| operacao | ENUM | CRIAR / ATUALIZAR / DELETAR / APROVAR / REPROVAR |
| campo_alterado | VARCHAR(100) | ex: "custo_unitario" |
| dados_anteriores | JSONB | snapshot antes |
| dados_novos | JSONB | snapshot depois |
| usuario_origem | VARCHAR(100) | |
| criado_em | TIMESTAMP | server_default=now() |

---

## Motor de Busca em Cascata (4 Fases)

```
POST /api/v1/busca/servicos
{cliente_id, texto_busca, limite_resultados=5, threshold_score=0.65}
          │
          ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  NORMALIZAÇÃO: strip → lower → remove acentos NFD → collapse   │
 └─────────────────────────────────────────────────────────────────┘
          │
          ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  FASE 0: Itens PROPRIOS do Cliente (APROVADOS)                  │
 │  SELECT * FROM servico_tcpo                                     │
 │  WHERE cliente_id = :cid AND origem = 'PROPRIA'                 │
 │    AND status_homologacao = 'APROVADO'                          │
 │    AND deleted_at IS NULL                                       │
 │  + pg_trgm similarity score                                     │
 │                                                                 │
 │  score > threshold → origem_match = 'PROPRIA_CLIENTE'          │
 │  Prioridade máxima — retorna se encontrar                       │
 └─────────────────────────────────────────────────────────────────┘
          │ (se nenhum resultado)
          ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  FASE 1: Associação Inteligente (Circuit Break em CONSOLIDADA)  │
 │  SELECT * FROM associacao_inteligente                           │
 │  WHERE cliente_id = :cid                                        │
 │    AND texto_busca_normalizado = :texto_norm                    │
 │    AND status_validacao = 'CONSOLIDADA'                         │
 │                                                                 │
 │  encontrou → score=1.0, origem='ASSOCIACAO_DIRETA'             │
 │  Chama fortalecer() em toda associação encontrada               │
 └─────────────────────────────────────────────────────────────────┘
          │ (se nenhum circuit break)
          ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  FASE 2: Busca Fuzzy Global (pg_trgm)                           │
 │  SELECT id, descricao, similarity(descricao, :texto) AS score  │
 │  FROM servico_tcpo                                              │
 │  WHERE similarity(descricao, :texto) > 0.85                    │
 │    AND deleted_at IS NULL                                       │
 │    AND status_homologacao = 'APROVADO'                          │
 │  ORDER BY score DESC LIMIT :limite                              │
 │                                                                 │
 │  score > 0.85 → origem='FUZZY'                                  │
 │  Safe para multi-worker (Gunicorn/Uvicorn)                      │
 └─────────────────────────────────────────────────────────────────┘
          │ (se nenhum resultado ou score insuficiente)
          ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  FASE 3: Busca Semântica (pgvector + all-MiniLM-L6-v2)         │
 │  embedding = embedder.encode(texto_normalizado)                 │
 │  SELECT id, metadata, 1-(vetor<=>:emb) AS sim                  │
 │  FROM tcpo_embeddings ORDER BY sim DESC LIMIT :limite          │
 │  WHERE 1-(vetor<=>:emb) >= threshold_score (0.65)              │
 │                                                                 │
 │  origem='IA_SEMANTICA'                                          │
 └─────────────────────────────────────────────────────────────────┘
          │
          ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  Background Task (não bloqueia response):                       │
 │  INSERT INTO historico_busca_cliente                            │
 └─────────────────────────────────────────────────────────────────┘
          │
          ▼
 BuscaServicoResponse {
   texto_buscado, resultados[],
   metadados: {tempo_processamento_ms, id_historico_busca}
 }
```

### DTOs Oficiais

**Request:**
```python
class BuscaServicoRequest(BaseModel):
    cliente_id: UUID
    texto_busca: str
    limite_resultados: int = 5
    threshold_score: float = 0.65
```

**Response:**
```python
class ResultadoBusca(BaseModel):
    id_tcpo: UUID
    codigo_origem: str
    descricao: str
    unidade: str
    custo_unitario: float
    score: float
    score_confianca: float        # V2
    origem_match: str             # 'PROPRIA_CLIENTE' | 'ASSOCIACAO_DIRETA' | 'FUZZY' | 'IA_SEMANTICA'
    status_homologacao: str       # V2

class BuscaServicoResponse(BaseModel):
    texto_buscado: str
    resultados: List[ResultadoBusca]
    metadados: dict  # {"tempo_processamento_ms": int, "id_historico_busca": UUID}
```

---

## Endpoints da API

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/auth/login` | — | email+senha → JWT access + refresh |
| POST | `/api/v1/auth/refresh` | — | Renova access token |
| POST | `/api/v1/busca/servicos` | JWT | Motor cascata 4 fases |
| POST | `/api/v1/busca/associar` | JWT | Criar/fortalecer associação inteligente |
| GET | `/api/v1/servicos/` | JWT | Lista paginada com filtros |
| GET | `/api/v1/servicos/{id}` | JWT | Detalhe do serviço |
| GET | `/api/v1/servicos/{id}/composicao` | JWT | Explosão TCPO (insumos + custos) |
| POST | `/api/v1/servicos/` | JWT | Criar serviço (PROPRIA → PENDENTE) |
| PUT | `/api/v1/servicos/{id}` | JWT | Atualizar serviço |
| DELETE | `/api/v1/servicos/{id}` | JWT | Soft delete |
| GET | `/api/v1/homologacao/pendentes` | JWT (APROVADOR+) | Lista itens PENDENTE do cliente |
| POST | `/api/v1/homologacao/aprovar` | JWT (APROVADOR+) | Aprovar ou reprovar item |
| POST | `/api/v1/homologacao/itens-proprios` | JWT | Criar item próprio (inicia como PENDENTE) |
| POST | `/api/v1/admin/compute-embeddings` | Admin | Batch encode em massa |
| POST | `/api/v1/admin/cache/refresh` | Admin | Recarrega catálogo |
| GET | `/health` | — | Status do servidor (inclui flag do modelo ML) |

---

## Autenticação e RBAC

### JWT
- **Access token**: 30 minutos, payload `{sub: user_id, client_id, exp}`
- **Refresh token**: 7 dias, revogação por hash armazenado no banco
- Bcrypt para hashing de senhas

### Perfis por Cliente (`usuario_perfil`)
| Perfil | Permissões |
|---|---|
| `CRIADOR` | Buscar serviços, criar itens PROPRIA, confirmar associações |
| `APROVADOR` | Tudo do CRIADOR + aprovar/reprovar itens PENDENTE do cliente |
| `ADMIN` | Tudo do APROVADOR + gerenciar usuários do cliente |
| `is_admin=True` (global) | Bypass total, acesso a todos os clientes e rotas `/admin` |

> RBAC verificado por query em `usuario_perfil` a cada requisição protegida. `is_admin` global faz bypass direto.

### AD/LDAP
O campo `external_id_ad` em `usuarios` permite integração futura com Active Directory sem quebra de contrato.

---

## Fluxo de Homologação

```
Usuário CRIADOR cria item PROPRIA
          │
          ▼
  servico_tcpo inserido com:
  origem = 'PROPRIA'
  status_homologacao = 'PENDENTE'
  cliente_id = <cliente do usuário>
          │
          ▼
  Não aparece em buscas (filtro status_homologacao = 'APROVADO')
  Não gera embedding (EmbeddingSyncService aguarda aprovação)
          │
          ▼
  APROVADOR/ADMIN consulta GET /homologacao/pendentes
          │
          ├─ POST /homologacao/aprovar {status: 'APROVADO'}
          │     → status_homologacao = 'APROVADO'
          │     → EmbeddingSyncService.sync(servico_id)  ← gera embedding
          │     → auditoria_log registra aprovação
          │
          └─ POST /homologacao/aprovar {status: 'REPROVADO'}
                → status_homologacao = 'REPROVADO'
                → Item permanece invisível nas buscas
```

---

## Sistema de Auditoria

Implementado via **SQLAlchemy `after_flush` hooks** em `app/core/audit_hooks.py`.

### Eventos Monitorados
- Alteração de `servico_tcpo.custo_unitario` → registra valores anterior e novo
- Alteração de `servico_tcpo.status_homologacao` → registra transição de status
- Aprovação/reprovação de itens via `HomologacaoService`

### Como Funciona
```python
# Em main.py lifespan:
register_audit_hooks(engine)

# Hook captura automaticamente:
@event.listens_for(Session, "after_flush")
def after_flush(session, flush_context):
    for obj in session.dirty:
        if isinstance(obj, ServicoTcpo):
            # detecta campos alterados → insere em auditoria_log
```

Todos os registros em `auditoria_log` são imutáveis (sem UPDATE/DELETE na tabela).

---

## Módulos ML (On-Premise)

### `app/ml/embedder.py`
- **Singleton** `Embedder`, carregado no lifespan FastAPI (`startup`)
- Modelo: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensões)
- Cache local via `SENTENCE_TRANSFORMERS_HOME` (sem acesso à internet)
- `encode(text: str) → list[float]` — vetor normalizado
- `encode_batch(texts, batch_size=64)` para pré-computação em massa
- Flag `ready: bool` exposta no `/health`

### `app/ml/fuzzy_search.py`
- **Primário**: `pg_trgm similarity()` no PostgreSQL
  - Query: `WHERE similarity(descricao, :texto) > 0.85`
  - Índice GIN habilita performance adequada
  - **Safe para multi-worker** (Gunicorn/Uvicorn)
- **Fallback**: `rapidfuzz` in-memory (ativável por feature flag)
- Threshold padrão: **0.85** (mais restritivo que o semântico)

### `app/ml/vector_search.py`
- Stateless `VectorSearcher`
- Query pgvector: `1 - (vetor <=> :query_vec) >= threshold`
- Usa índice HNSW para ANN (Approximate Nearest Neighbors)
- Retorna `(servico_tcpo_id, score, metadata_jsonb)`

### Sincronia de Embeddings
```
EmbeddingSyncService.sync(servico_id):
  ├─ CREATE → encode(descricao) → INSERT INTO tcpo_embeddings
  ├─ UPDATE → re-encode → UPDATE tcpo_embeddings SET vetor=..., metadata=...
  └─ DELETE (soft) → DELETE FROM tcpo_embeddings WHERE id = servico_id
```
Evita Orphan IDs: embeddings de itens deletados são removidos imediatamente.

---

## Migrations Alembic

| # | Arquivo | O que faz |
|---|---|---|
| 001 | `create_base_tables` | `cliente`, `categoria_recurso`, `servico_tcpo`, `composicao_tcpo`, `historico_busca_cliente`, `associacao_tcpo`, `usuario` |
| 002 | `pgvector_extension` | `CREATE EXTENSION IF NOT EXISTS vector` |
| 003 | `tcpo_embeddings_table` | Tabela `tcpo_embeddings` + Vector(384) + índice HNSW |
| 004 | `gin_fulltext_index` | `CREATE EXTENSION pg_trgm` + GIN index em `servico_tcpo.descricao` |
| 005 | `v2_governance_rbac_audit` | Enums V2, `external_id_ad`, `usuario_perfil`, colunas de governança em `servico_tcpo`, substitui `associacao_tcpo` por `associacao_inteligente`, cria `auditoria_log` |

### Executar Migrations
```bash
alembic upgrade head
```

### Reverter
```bash
alembic downgrade -1
```

---

## Setup e Instalação

### Pré-requisitos
- Python 3.11+
- Docker + Docker Compose
- PostgreSQL 16 com extensões `pgvector` e `pg_trgm`

### 1. Clone e Ambiente Virtual
```bash
git clone <repo>
cd dinamica-budget
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Banco de Dados (Docker)
```bash
docker compose up db -d
```

### 3. Variáveis de Ambiente
```bash
cp .env.example .env
# editar .env com as credenciais do banco
```

### 4. Migrations
```bash
alembic upgrade head
```

### 5. Modelo ML (Download One-Time)
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
# Define SENTENCE_TRANSFORMERS_HOME no .env para cache local
```

### 6. Iniciar API
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Seed + Pré-computar Embeddings
```bash
# Após popular servico_tcpo com dados TCPO:
curl -X POST http://localhost:8000/api/v1/admin/compute-embeddings \
  -H "Authorization: Bearer <admin_token>"
```

### Swagger UI
Acesse `http://localhost:8000/docs`

---

## Variáveis de Ambiente

```bash
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dinamica_budget

# JWT
SECRET_KEY=sua_chave_secreta_muito_longa_e_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Modelo ML
SENTENCE_TRANSFORMERS_HOME=./models/cache
ML_MODEL_NAME=all-MiniLM-L6-v2

# Busca
FUZZY_THRESHOLD=0.85
SEMANTIC_THRESHOLD=0.65
DEFAULT_SEARCH_LIMIT=5

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Testes

### Estrutura
```
app/tests/
├── conftest.py          # fixtures: db async, client, tokens por perfil
├── unit/
│   ├── test_busca_service.py
│   ├── test_associacao_repository.py
│   └── test_homologacao_service.py
└── integration/
    ├── test_busca_endpoints.py
    ├── test_auth_endpoints.py
    └── test_homologacao_endpoints.py
```

### Verificação End-to-End
```bash
# 1. alembic upgrade head
# 2. Seed: 10 serviços TCPO + compute-embeddings
# 3. POST /auth/login → token JWT
# 4. POST /busca/servicos (texto ≈ descrição) → FUZZY, score > 0.85
# 5. POST /busca/associar (confirmar resultado)
# 6. POST /busca/servicos (mesmo texto) → ASSOCIACAO_DIRETA, score=1.0
# 7. GET /servicos/{id}/composicao → insumos com totais
# 8. Verificar historico_busca_cliente → 2 registros
# 9. DELETE servico → embedding removido de tcpo_embeddings
```

---

## Plano de Implementação V2

### Fase Atual: Motor de Busca + Governança + Auditoria

**Concluído:**
- [x] Estrutura base do projeto (FastAPI + SQLAlchemy async)
- [x] Modelos de dados V2 com campos de governança
- [x] Enums centralizados (`app/models/enums.py`)
- [x] `AssociacaoInteligente` com `frequencia_uso` e `status_validacao`
- [x] `AuditoriaLog` com JSONB imutável
- [x] `UsuarioPerfil` para RBAC por cliente
- [x] `external_id_ad` para integração AD/LDAP futura
- [x] Motor de busca em cascata 4 fases (`busca_service.py`)
- [x] Normalização de texto (strip → lower → NFD → collapse)
- [x] `EmbeddingSyncService` (garante consistência tcpo_embeddings)
- [x] `HomologacaoService` com fluxo PENDENTE → APROVADO/REPROVADO
- [x] DFS anti-loop em `composicao_tcpo`
- [x] Recálculo automático de custo pai quando filho muda (PROPRIA)
- [x] Audit hooks via SQLAlchemy `after_flush`
- [x] 5 migrations Alembic (001–005)
- [x] `.claude/launch.json` para dev servers

### Fase 2 (Próxima): Catálogo e Relatórios
- [ ] Import em massa de catálogo TCPO (CSV/Excel)
- [ ] Export de orçamento por cliente (PDF/Excel)
- [ ] Histórico de versões de preço por serviço
- [ ] Dashboard de uso por cliente (top buscas, top associações)

### Fase 3: Integração e Notificações
- [ ] Webhook para notificar APROVADOR quando novo item PENDENTE
- [ ] Integração com AD/LDAP para login corporativo
- [ ] API pública para integração com sistemas de orçamento externos
- [ ] Rate limiting por cliente

### Fase 4: ML Avançado
- [ ] Re-treinamento periódico de embeddings com dados do histórico de busca
- [ ] Score de confiança baseado em frequência histórica de confirmações
- [ ] Sugestão automática de categoria para novos itens PROPRIA
- [ ] Detecção de itens duplicados no catálogo (cosine similarity > 0.95)

### Fase 5: Observabilidade e SRE
- [ ] Métricas Prometheus (latência por fase de busca, hit rate por origem_match)
- [ ] Tracing distribuído (OpenTelemetry)
- [ ] Alertas de Orphan IDs no banco vetorial
- [ ] SLA de disponibilidade com circuit breaker externo

---

## Riscos Técnicos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Orphan IDs no banco vetorial | Busca semântica retorna UUID inativo | `EmbeddingSyncService` em toda mutação do catálogo |
| Modelo ML não carregado no startup | API retorna 503 para buscas semânticas | Flag `ready=False` no `/health`; `SENTENCE_TRANSFORMERS_HOME` local |
| HNSW index build lento em tabela populada | Downtime durante migration 003 | `CREATE INDEX CONCURRENTLY` + `maintenance_work_mem=1GB` |
| Alembic não reconhece tipo Vector | Migration falha | Custom type hook em `alembic/env.py` |
| Background task de histórico falha silenciosamente | Histórico incompleto | Logging estruturado na task; alerta em falha (não bloqueia response) |
| Soft delete sem filtro | Itens deletados aparecem em buscas | `WHERE deleted_at IS NULL` obrigatório em todos os SELECTs |
| Loop infinito em composição TCPO | Stack overflow no recálculo de custo | DFS com conjunto `visitados` antes de todo INSERT |
| RBAC não verificado em novo endpoint | Escalada de privilégio | `Depends(require_perfil(...))` como decorator padrão nos routers V2 |
| Fuzzy search bloqueando CPU em catálogo grande | Latência alta na fase 2 | GIN index em `servico_tcpo.descricao` via migration 004 |
| Tokens JWT não revogados | Sessão inválida continua ativa | Hash do refresh token armazenado no banco; revogação explícita |

---

## Documentação da API

Com o servidor rodando, acesse:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

*Dinamica Budget — Backend API v2.0 | On-Premise | FastAPI + PostgreSQL + pgvector*
