# Contratos de memória (genéricos)

Schemas conceptuais — independentes de vendor. Implementações devem aceitar estes campos mínimos.

---

## remember (L4 write)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "memory.remember",
  "type": "object",
  "required": ["scope", "statement"],
  "properties": {
    "scope": {
      "type": "object",
      "required": ["kind"],
      "properties": {
        "kind": { "enum": ["user", "project", "agent", "org"] },
        "id": { "type": "string" }
      }
    },
    "statement": { "type": "string", "maxLength": 2000 },
    "subject": { "type": "string" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "source_run_id": { "type": "string" },
    "tags": { "type": "array", "items": { "type": "string" } },
    "status": { "enum": ["candidate", "active"], "default": "candidate" }
  }
}
```

- Default recomendado em agents: `status: candidate` até gate humano ou política confiável.  

## recall (L4 read)

```json
{
  "$id": "memory.recall",
  "type": "object",
  "required": ["scope"],
  "properties": {
    "scope": { "$ref": "#/definitions/scope" },
    "query": { "type": "string" },
    "limit": { "type": "integer", "minimum": 1, "maximum": 50, "default": 10 },
    "tags": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Response items:** `id`, `statement`, `confidence`, `updated_at`, `source_run_id?`.

## forget (L4)

```json
{
  "$id": "memory.forget",
  "type": "object",
  "required": ["id"],
  "properties": {
    "id": { "type": "string" },
    "reason": { "type": "string" }
  }
}
```

Soft-delete ou tombstone; não reescrever história L2.

---

## retrieve_knowledge (L5)

```json
{
  "$id": "memory.retrieve_knowledge",
  "type": "object",
  "required": ["kb", "query"],
  "properties": {
    "kb": { "type": "string" },
    "query": { "type": "string" },
    "top_k": { "type": "integer", "default": 8, "maximum": 30 },
    "filters": { "type": "object", "additionalProperties": true },
    "require_citations": { "type": "boolean", "default": true }
  }
}
```

**Hit:** `content`, `score`, `doc_id`, `citation` (`source`, `locator`), `metadata`.

## retrieve_graph (L6, opcional)

```json
{
  "$id": "memory.retrieve_graph",
  "type": "object",
  "required": ["query"],
  "properties": {
    "query": { "type": "string" },
    "max_hops": { "type": "integer", "default": 2, "maximum": 4 },
    "kb_or_graph": { "type": "string" }
  }
}
```

**Response:** paths (nodes/edges) + `source_refs` para L5.

---

## event (L2 append)

```json
{
  "$id": "memory.event",
  "type": "object",
  "required": ["type", "run_id", "at"],
  "properties": {
    "id": { "type": "string" },
    "type": { "type": "string" },
    "run_id": { "type": "string" },
    "plan_id": { "type": "string" },
    "seq": { "type": "integer" },
    "at": { "type": "string", "format": "date-time" },
    "actor": {
      "type": "object",
      "properties": {
        "kind": { "enum": ["agent", "human", "system"] },
        "id": { "type": "string" }
      }
    },
    "payload": { "type": "object" },
    "schema_version": { "type": "integer", "default": 1 }
  }
}
```

---

## skill_candidate (L3 gate)

```json
{
  "$id": "memory.skill_candidate",
  "type": "object",
  "required": ["name", "body_md", "source_run_id"],
  "properties": {
    "name": { "type": "string" },
    "body_md": { "type": "string" },
    "source_run_id": { "type": "string" },
    "status": { "const": "candidate" }
  }
}
```

Promoção para `skills/` = processo humano fora deste contrato.
