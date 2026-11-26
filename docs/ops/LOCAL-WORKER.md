# Worker local (sem chave paga, sem sair da máquina)

Corre os passos de um plano num modelo que está no teu computador. Serve qualquer servidor com a API OpenAI
(`/chat/completions`): Ollama, llama.cpp (`llama-server`), LM Studio, vLLM.

## Usar (Ollama, exemplo)

```bash
ollama pull qwen2.5:3b          # uma vez; modelo pequeno, corre em CPU
export LOCAL_LLM_MODEL=qwen2.5:3b
python -m plan_runner run <plano.yaml> --mode external --worker local
```

| Variável | Para quê | Omissão |
|---|---|---|
| `LOCAL_LLM_MODEL` | nome do modelo no servidor (obrigatória) | nenhuma |
| `LOCAL_LLM_URL` | base da API | `http://127.0.0.1:11434/v1` (Ollama) |
| `LOCAL_LLM_API_KEY` | só se o servidor exigir chave | nenhuma |

## O que muda e o que não muda

- **Igual:** prompt, tools, gates humanos, governança local (políticas e recibos), ledger `token_usage.jsonl`.
- **Custo:** 0. O tecto de USD do plano não bloqueia este worker; o tecto de tokens continua a valer.
- **`countTokens`:** estimativa (caracteres ÷ 4), não contagem verificada.
- **Honestidade:** modelos pequenos erram mais o JSON e as tools do que os grandes. Se um passo falhar, fica em
  `waiting_external` com o motivo (por exemplo, servidor desligado), e podes retomá-lo.

## Estado do teste

Verificado com um servidor falso em HTTP real (`runner/tests/test_local_worker.py`). **Ainda não** foi medido com
um modelo real: fazê-lo e registar o resultado é o próximo passo quando houver acesso ao computador.
