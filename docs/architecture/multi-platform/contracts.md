# Contratos multi-plataforma (mínimos)

## InboundMessage

```json
{
  "$id": "platform.inbound",
  "type": "object",
  "required": ["message_id", "platform", "channel_identity", "received_at"],
  "properties": {
    "message_id": { "type": "string" },
    "platform": {
      "type": "string",
      "enum": ["cli", "telegram", "slack", "web", "mcp", "api", "cron", "a2a", "other"]
    },
    "channel_identity": {
      "type": "object",
      "required": ["platform", "external_id"],
      "properties": {
        "platform": { "type": "string" },
        "external_id": { "type": "string" }
      }
    },
    "subject_id": { "type": "string" },
    "thread_id": { "type": "string" },
    "text": { "type": "string" },
    "attachments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "uri": { "type": "string" },
          "mime": { "type": "string" },
          "name": { "type": "string" }
        }
      }
    },
    "metadata": { "type": "object" },
    "received_at": { "type": "string", "format": "date-time" }
  }
}
```

## OutboundMessage

```json
{
  "$id": "platform.outbound",
  "type": "object",
  "required": ["platform"],
  "properties": {
    "platform": { "type": "string" },
    "channel_identity": { "type": "object" },
    "subject_id": { "type": "string" },
    "thread_id": { "type": "string" },
    "text": { "type": "string" },
    "blocks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": { "enum": ["paragraph", "code", "list", "approval_request", "link"] },
          "content": {}
        }
      }
    },
    "run_id": { "type": "string" },
    "requires_hitl": { "type": "boolean" }
  }
}
```

## Handoff / resume (HITL)

```json
{
  "$id": "platform.hitl_resume",
  "type": "object",
  "required": ["run_id", "decision"],
  "properties": {
    "run_id": { "type": "string" },
    "decision": { "enum": ["approve", "reject", "edit"] },
    "edited_payload": { "type": "object" },
    "actor_subject_id": { "type": "string" },
    "via_platform": { "type": "string" }
  }
}
```
