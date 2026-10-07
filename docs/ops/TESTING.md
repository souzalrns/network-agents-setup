# Testes: como correr, BD descartável e clientes fictícios

**Regra:** os testes **nunca** tocam em produção (Supabase, Vercel, Gemini). Usam um Postgres descartável, embeddings determinísticos e um Gemini falso. Os dados de clientes são **fictícios** (`FAKE-`).

## 1. Instalação

```bash
cd runner
python -m pip install -r requirements.txt -r requirements-langgraph.txt pytest
python -m pip install -r requirements-test.txt      # Faker + testcontainers (opcional)
```

| Ficheiro | Para quê |
|---|---|
| `requirements.txt` | runner |
| `requirements-langgraph.txt` | motor LangGraph e testes `slow` |
| `requirements-test.txt` | **Faker** (MIT) e **testcontainers** (Apache-2.0), com pins exactos: o Faker com seed fixa só gera os mesmos dados na mesma versão |
| `requirements-ingest.txt` e `requirements-fixtures.txt` | ingestão (MarkItDown) e geradores de fixtures |

## 2. Correr

```bash
cd runner
python -m pytest -q                       # rápidos (o pytest.ini exclui os `slow`)
python -m pytest -q -m slow               # planos reais por subprocess, LangGraph, crash recovery
ruff check plan_runner/ tests/            # o mesmo lint do CI
```

## 3. Postgres + pgvector descartável

Os testes de RAG, L4, proveniência e clientes fictícios precisam de um Postgres com `pgvector`. A fixture `disposable_pg` (`runner/tests/conftest.py`) procura, por esta ordem:

1. **`RAG_TEST_DATABASE_URL`**: um Postgres teu. No CI é o serviço `pgvector/pgvector:pg16` do job `test-rag`.
   ```bash
   RAG_TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ragtest python -m pytest -q
   ```
2. **testcontainers:** sem a variável, arranca um contentor `pgvector/pgvector:pg16`, usa-o e apaga-o no fim. Precisa de Docker a correr e do `requirements-test.txt`.
3. **Nenhum dos dois:** os testes de BD ficam `skipped`.
   - Com `RAG_TEST_REQUIRED=1` (CI), a falta de BD é **erro**: um job nunca fica verde sem ter corrido.

A L4 corre num **schema próprio** por teste, com o SQL versionado aplicado 2 vezes para provar a idempotência. O schema é apagado no fim.

**Nunca** apontes o `RAG_TEST_DATABASE_URL` para o Supabase: os testes criam e apagam schemas.

## 4. Clientes fictícios (`scripts/seed_fake_clients.py`)

**Não há uma tabela `client_memory`.** A memória de um cliente tem 2 formas:
- **working memory:** `memory/<client_id>/MEMORY.md`, lida por `runner/plan_runner/working_memory.py` e injectada no prompt quando o plano tem `client_id` (S30). Está no `.gitignore`;
- **L4:** tabela `memory_l4`, no âmbito `project:<client_id>` (`runner/plan_runner/memory_l4.py`).

O script gera **N clientes fictícios** com o Faker (`pt_BR`, seed fixa 4200) e escreve nas duas:

```bash
# ver os clientes (JSON), sem escrever nada
python scripts/seed_fake_clients.py --n 5 --json

# working memory numa pasta à escolha (fora do repo, ou no repo: memory/*/ está no .gitignore)
python scripts/seed_fake_clients.py --n 5 --memory-root /tmp/fake-run

# L4 num Postgres LOCAL com o SQL da L4 aplicado
python scripts/seed_fake_clients.py --n 5 --database-url postgresql://postgres:postgres@localhost:5432/ragtest

# limpar só os FAKE- (ficheiros e/ou L4)
python scripts/seed_fake_clients.py --cleanup --memory-root /tmp/fake-run --database-url postgresql://...@localhost:5432/ragtest
```

| Garantia | Como |
|---|---|
| Sempre os mesmos dados | `Faker.seed_instance(seed)` + versão fixa do Faker |
| Fácil de limpar | `client_id` com o prefixo **`FAKE-`**; na L4, também `metadata.fake = true` e a etiqueta `FAKE` |
| Nenhum contacto real | e-mails só em `example.com`, `example.net` e `example.org` (RFC 2606); o MEMORY.md diz "DADOS FICTÍCIOS" |
| Nunca em produção | `--database-url` é obrigatório (o `DATABASE_URL` do ambiente nunca é lido); só aceita `localhost`, `127.0.0.1`, `::1` ou o host de um testcontainer; recusa qualquer host do Supabase |
| A limpeza não apaga dados reais | `DELETE` só de `scope_id LIKE 'FAKE-%'` **e** `metadata.fake = true` (desvio de compliance do trigger, `SET LOCAL memory_l4.allow_delete`) |
| Sem custo | embedding determinístico (sha256 → 768 dimensões), sem Gemini |

## 5. O que os testes dos clientes fictícios provam (`runner/tests/test_fake_clients.py`)

**Sem BD:**
- determinismo e prefixo `FAKE-`;
- contactos só em domínios reservados;
- recusa de URLs do Supabase, de hosts remotos e do `DATABASE_URL` do ambiente;
- o `working_memory.py` lê o MEMORY.md gerado;
- a limpeza de ficheiros não toca num cliente real.

**Com BD (`disposable_pg`):**
- cada facto fica `active` no âmbito `project:FAKE-…`;
- **um cliente nunca vê os factos de outro** (isolamento por âmbito);
- a pesquisa por semelhança funciona dentro do âmbito;
- `forget` retira o facto;
- a limpeza apaga só os `FAKE-` e mantém o cliente real.

**No CI:** o job `test` instala o `requirements-test.txt` e corre os testes sem BD. Num runner do GitHub com Docker, corre também o de BD via testcontainers. O job `test-rag` corre-os todos contra o serviço Postgres, com `RAG_TEST_REQUIRED=1`.

## 6. Ligações

- Política de privacidade e separação repo público/privado: `docs/governance/PRIVACY-POLICY.md`.
- L4: `docs/ops/MEMORY-L4.md`.
- Worker e Gemini falso: `docs/ops/WORKER-EXTERNAL.md`.
