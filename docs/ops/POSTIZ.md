# Postiz: do pacote aprovado ao agendamento (M-006)

**O que é:** o passo `publish_package` (agente `marketing.publicador`) entrega um pacote de publicação
em JSON. O comando `python -m plan_runner.postiz` pega nesse pacote e cria os posts no
[Postiz](https://github.com/gitroomhq/postiz-app), o agendador open source (AGPL-3.0) que publica nas
redes. O agente continua a só preparar: quem manda enviar é uma pessoa, com o comando.

**Custo:** zero, se o Postiz correr no teu computador ou num servidor que já tenhas. Só há custo com o
Postiz Cloud (desde 29 $/mês) ou um servidor novo (5 a 20 $/mês), e nenhum é preciso. O acesso de
escrita à API do X pode ser pago do lado do X: se não estiver contratado, não ligues o X no Postiz.

## Garantias (o que o comando recusa)

| Recusa enviar se… | Porquê |
|---|---|
| o run não tem `human_gate_resolved` com `approve` (ou `edit`) num passo `plan_approve` que depende do pacote **e** da compliance | nada sai sem aprovação humana registada |
| a compliance não viu o pacote ou não diz `"veredicto": "aprovado"` | publicidade e IA identificadas (AI Act, art. 50), direitos e consentimento verificados antes |
| o pacote ou a compliance foram alterados depois da aprovação | aprovou-se o que lá estava, não outra coisa |
| o pacote não cumpre o formato (`posts[].rede/quando/legenda`, no máximo 30 posts) | o envio é determinístico: nenhum modelo reescreve o texto |

Por post (o post fica `recusado` com o motivo; o resto do pacote segue):

- data no passado, ou `quando` sem fuso e sem `fuso`;
- `[[A DEFINIR]]` na legenda;
- ficheiro fora do directório do run, symlink ou inexistente; ficheiro sem texto alternativo;
- rede não suportada, ou sem uma integração activa única no Postiz (indica-a com `--integration`);
- YouTube sem `title`/`type`, Pinterest sem `board`, TikTok sem `privacy_level`/`title` em `settings`.

**Modos:** sem `--send` só simula (sem rede) e escreve `artifacts/postiz-envio.json` com o que seria
enviado. `--send` cria **rascunhos** no Postiz, que se revêem lá antes de agendar. `--send --schedule`
agenda. Publicar no momento (`type: now`) não existe neste comando.

**Idempotência e erros:** cada post leva o sha256 do que é enviado. Correr outra vez não reenvia o que
já saiu (`ja_enviado`). Se o Postiz falhar a meio, o relatório guarda o que saiu (`enviado`), o que
falhou (`erro`) e o que ficou por enviar (`nao_enviado`); a nova tentativa envia só o resto.

**Segredos:** `POSTIZ_API_URL` e `POSTIZ_API_KEY` vêm só do ambiente. A chave nunca é escrita no run,
no relatório nem nos eventos. Não há URL por omissão, para nunca enviar para um Postiz que não é o teu.

**Auditoria:** cada execução acrescenta um evento `postiz_dispatch` ao `events.jsonl` do run (modo,
contagens, sha256 dos posts).

## Contrato com o Postiz

Verificado no código, não só na documentação (`gitroomhq/postiz-app@bd8353f`, 2026-11-03):
`CreatePostDto` e `providers-settings/*.dto.ts` da API pública `/public/v1`.

- `POST /posts` com `type` (`draft` ou `schedule`), `date` em ISO 8601 UTC, `shortLink: false`,
  `tags: []` e `posts[]` com `integration.id`, `value[].content` e `value[].image[]`, e `settings.__type`.
- O conteúdo é HTML (o editor do Postiz guarda `<p>`): cada linha da legenda vira um parágrafo, com
  escape. Hashtags e identificações (ex.: `Imagem gerada com IA`, `#pub`) entram no fim, se faltarem.
- Imagens e vídeos vão primeiro a `POST /upload`; o post usa o `id` e o `path` devolvidos, com o `alt`.
- `GET /integrations` dá o `identifier` de cada canal (`instagram`, `facebook`, `linkedin`, `linkedin-page`…).
- Valores por omissão: Instagram `post_type: post`; TikTok `content_posting_method: DIRECT_POST`
  (`UPLOAD` não publica) e `video_made_with_ai` segue as identificações do pacote.
- Limite do Postiz: cerca de 90 pedidos de criação por hora, por instância.

## Instalar o Postiz (grátis, no teu computador)

Precisa de Docker e de 2 GB de RAM livres (o Postiz testa em 2 vCPU / 2 GB; recomenda 4 GB ou mais).

```bash
git clone https://github.com/gitroomhq/postiz-docker-compose
cd postiz-docker-compose
# editar docker-compose.yaml: JWT_SECRET (texto aleatório longo) e, depois de criares a tua conta,
# DISABLE_REGISTRATION: 'true'
docker compose up -d
```

Abre `http://localhost:4007`, cria a conta, liga os canais (cada rede pede uma app de programador,
grátis, na própria plataforma) e copia a API key em Settings → Public API.

**Limites do Postiz local:**

- O computador tem de estar ligado à hora de publicar.
- O Instagram exige sempre imagem ou vídeo, e a Meta vai buscar o ficheiro ao URL do Postiz. Com o
  Postiz só em `localhost`, a Meta não chega lá. Para o Instagram é preciso um endereço público (túnel
  grátis, ex.: Cloudflare Tunnel) ou armazenamento externo (`STORAGE_PROVIDER: cloudflare`, R2 tem
  plano grátis). Posts só de texto (LinkedIn, Facebook, Threads, Bluesky, Mastodon) funcionam sem isto.
- O registo das apps de cada rede (endereços de retorno do login) segue as regras de cada plataforma;
  confirmar na documentação do Postiz para cada canal antes de ligar.

## Usar

```bash
cd runner
# 1. simular (sem rede): mostra o que seria enviado
python -m plan_runner.postiz ../pilots/<run>

# 2. enviar como rascunhos para o teu Postiz
export POSTIZ_API_URL=http://localhost:4007/api/public/v1
export POSTIZ_API_KEY=<a tua chave>
python -m plan_runner.postiz ../pilots/<run> --send

# 3. agendar (depois de rever os rascunhos, ou directamente)
python -m plan_runner.postiz ../pilots/<run> --send --schedule

# mais de um canal da mesma rede: escolher qual
python -m plan_runner.postiz ../pilots/<run> --send --integration linkedin=<id>
```

No PowerShell, as variáveis são `$env:POSTIZ_API_URL = "http://localhost:4007/api/public/v1"` e
`$env:POSTIZ_API_KEY = "<a tua chave>"`.

Saída: `0` quando tudo correu bem; `2` se algum post ficou `recusado`, `erro` ou `nao_enviado`
(ver `artifacts/postiz-envio.json`); `1` se o run foi recusado por inteiro (falta de prova).

Prova: `runner/tests/test_postiz.py` (run real do template Social, Postiz falso, sem rede).
