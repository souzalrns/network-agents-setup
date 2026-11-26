"""M-006: liga o pacote do publicador (`publish_package`) ao Postiz (agendador open source, AGPL-3.0).

Contrato (docs/ops/POSTIZ.md):

- **Determinístico, sem modelo:** o texto enviado é o do pacote aprovado, nunca reescrito por um LLM.
- **Só com prova no run:** recusa enviar se o run não tiver (1) o passo `publish_package` e o passo
  `compliance_check` concluídos, (2) a compliance a ver o pacote e com `veredicto: aprovado`,
  (3) um `human_gate_resolved` com `approve`/`edit` num passo `plan_approve` que depende dos dois, e
  (4) o pacote e a compliance iguais, byte a byte, ao que foi aprovado (sha256 gravado na aprovação, M-009).
- **Simula por omissão:** sem `--send` não há rede; escreve `artifacts/postiz-envio.json` com o que
  seria enviado. Com `--send` cria **rascunhos** no Postiz (`type: draft`); só `--schedule` agenda.
  Publicar já (`type: now`) não existe aqui.
- **Por post, fail-closed:** data no passado, `[[A DEFINIR]]` na legenda, ficheiro fora do run, rede sem
  integração única ou identificação obrigatória em falta → esse post fica `recusado`, com o motivo.
- **Idempotente:** cada post tem um sha256 do payload; um post já enviado não volta a ser enviado.
- **Segredos:** `POSTIZ_API_KEY` e `POSTIZ_API_URL` só do ambiente; a chave nunca vai para ficheiros
  nem eventos. Sem URL por omissão: o destino é o Postiz que o operador instalou.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import jsonschema
import yaml

from .events import EventLog

REPORT = "artifacts/postiz-envio.json"
MAX_POSTS = 30  # o Postiz limita o create a ~90 pedidos/hora por instância
APPROVED = ("approve", "edit")
PLACEHOLDER = "[[A DEFINIR]]"
NETWORKS: dict[str, tuple[str, ...]] = {  # rede do pacote -> `identifier` das integrações do Postiz
    "instagram": ("instagram", "instagram-standalone"),
    "facebook": ("facebook",),
    "linkedin": ("linkedin", "linkedin-page"),
    "x": ("x",),
    "twitter": ("x",),
    "youtube": ("youtube",),
    "tiktok": ("tiktok",),
    "threads": ("threads",),
    "pinterest": ("pinterest",),
    "bluesky": ("bluesky",),
    "mastodon": ("mastodon",),
}

# Contrato verificado no código do Postiz (gitroomhq/postiz-app@bd8353f, 2026-11-03): CreatePostDto e
# providers-settings/*.dto.ts. O Instagram exige `post_type`; estes exigem campos que só o pacote pode dar.
DEFAULT_SETTINGS: dict[str, dict[str, Any]] = {
    "instagram": {"post_type": "post"},
    "instagram-standalone": {"post_type": "post"},
    "tiktok": {"content_posting_method": "DIRECT_POST"},  # "UPLOAD" não publica (fica na caixa do TikTok)
}
REQUIRED_SETTINGS: dict[str, tuple[str, ...]] = {
    "youtube": ("title", "type"),
    "pinterest": ("board",),
    "tiktok": ("privacy_level", "title"),
}
AI_LABEL = re.compile(r"\b(ia|ai)\b|intelig[eê]ncia artificial", re.IGNORECASE)

PACKAGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["posts"],
    "properties": {
        "posts": {"type": "array", "maxItems": MAX_POSTS, "items": {
            "type": "object",
            "required": ["rede", "quando", "legenda"],
            "properties": {
                "rede": {"type": "string", "minLength": 1},
                "quando": {"type": "string", "minLength": 10},
                "fuso": {"type": "string"},
                "legenda": {"type": "string", "minLength": 1},
                "ficheiros": {"type": "array", "items": {"type": "string"}},
                "alt": {"type": ["array", "object", "string"]},
                "hashtags": {"type": "array", "items": {"type": "string"}},
                "identificacoes": {"type": "array", "items": {"type": "string"}},
                "integracao": {"type": "string"},
                "settings": {"type": "object"},
            },
        }},
        "fora": {"type": "array"},
    },
}


class PostizError(RuntimeError):
    """Falta prova no run, o pacote é inválido ou o Postiz respondeu com erro: nada (mais) é enviado."""


# --------------------------------------------------------------------------- transporte (injectável)

Send = Callable[..., tuple[int, Any]]


def httpx_send(method: str, url: str, *, headers: dict[str, str], json_body: Any = None,
               file: tuple[str, bytes] | None = None, timeout: float = 30.0) -> tuple[int, Any]:
    import httpx

    files = {"file": file} if file else None
    r = httpx.request(method, url, headers=headers, json=json_body, files=files, timeout=timeout)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, r.text[:500]


@dataclass(frozen=True)
class Client:
    base_url: str
    api_key: str
    send: Send = httpx_send

    def _call(self, method: str, path: str, **kw: Any) -> Any:
        status, body = self.send(method, self.base_url.rstrip("/") + path, headers={"Authorization": self.api_key}, **kw)
        if status >= 400:
            raise PostizError(f"Postiz {method} {path}: HTTP {status}: {str(body)[:300]}")
        return body

    def integrations(self) -> list[dict[str, Any]]:
        body = self._call("GET", "/integrations")
        return body if isinstance(body, list) else []

    def upload(self, name: str, data: bytes) -> dict[str, Any]:
        body = self._call("POST", "/upload", file=(name, data))
        if not isinstance(body, dict) or not body.get("path"):
            raise PostizError(f"upload de {name}: resposta sem `path`")
        return {"id": body.get("id"), "path": body["path"]}

    def create(self, payload: dict[str, Any]) -> Any:
        return self._call("POST", "/posts", json_body=payload)


# --------------------------------------------------------------------------- prova no run


def _events(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "events.jsonl"
    if not path.is_file():
        raise PostizError("o run não tem events.jsonl")
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _depends(steps: dict[str, dict[str, Any]], sid: str, target: str) -> bool:
    deps = steps[sid].get("depends_on") or []
    return target in deps or any(_depends(steps, d, target) for d in deps if d in steps)


def evidence(run_dir: Path) -> dict[str, Any]:
    """Confirma a prova exigida e devolve os passos e ficheiros. Levanta PostizError com o motivo."""
    status_path, plan_path = run_dir / "status.json", run_dir / "plan.yaml"
    if not status_path.is_file() or not plan_path.is_file():
        raise PostizError("não é um directório de run (falta status.json ou plan.yaml)")
    status = json.loads(status_path.read_text(encoding="utf-8-sig"))
    raw_steps = (yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}).get("steps") or []
    steps = {s["id"]: s for s in raw_steps}
    pkg = [s for s in raw_steps if s.get("action") == "publish_package"]
    comp = [s for s in raw_steps if s.get("action") == "compliance_check"]
    if len(pkg) != 1 or len(comp) != 1:
        raise PostizError("o plano tem de ter exactamente 1 passo publish_package e 1 passo compliance_check")
    pkg, comp = pkg[0], comp[0]
    done = set(status.get("completed") or [])
    for s in (pkg, comp):
        if s["id"] not in done:
            raise PostizError(f"o passo `{s['id']}` não está concluído")
    if pkg["output_artifact"] not in (comp.get("inputs") or []):
        raise PostizError("a compliance não recebeu o pacote de publicação como input")
    verdict = json.loads((run_dir / comp["output_artifact"]).read_text(encoding="utf-8"))
    if not isinstance(verdict, dict) or verdict.get("veredicto") != "aprovado":
        raise PostizError(f"compliance sem `veredicto: aprovado` (veio {verdict.get('veredicto') if isinstance(verdict, dict) else verdict!r})")

    gates = [sid for sid, s in steps.items() if s.get("action") == "plan_approve"
             and _depends(steps, sid, pkg["id"]) and _depends(steps, sid, comp["id"])]
    run_id = status.get("run_id")
    last: dict[str, Any] | None = None
    for evt in _events(run_dir):
        if evt.get("type") == "human_gate_resolved" and evt.get("run_id") == run_id \
                and (evt.get("payload") or {}).get("step_id") in gates:
            last = evt
    if last is None or last["payload"].get("decision") not in APPROVED:
        raise PostizError("sem aprovação humana registada (human_gate_resolved approve) depois do pacote e da compliance")
    # M-009: o que se envia tem de ser byte a byte o que foi aprovado (sha256 gravado na aprovação)
    fp = last["payload"].get("fingerprint") or {}
    if fp.get("plan_sha256") != hashlib.sha256(plan_path.read_bytes()).hexdigest():
        raise PostizError("o plano do run mudou depois da aprovação humana (ou a aprovação não tem impressão digital)")
    approved = fp.get("artifacts") or {}
    for s in (pkg, comp):
        rel = s["output_artifact"]
        if rel not in approved:
            raise PostizError(f"a aprovação não regista o conteúdo de `{rel}` (aprovação sem impressão digital): aprova outra vez")
        if hashlib.sha256((run_dir / rel).read_bytes()).hexdigest() != approved[rel]:
            raise PostizError(f"`{rel}` foi alterado depois da aprovação humana")
    return {"run_id": run_id, "package": pkg["output_artifact"], "compliance": comp["output_artifact"],
            "gate": last["payload"]["step_id"], "approved_at": last["at"]}


# --------------------------------------------------------------------------- pacote -> payloads


def _when_utc(post: dict[str, Any]) -> datetime:
    when = datetime.fromisoformat(post["quando"].replace("Z", "+00:00"))
    if when.tzinfo is None:
        if not post.get("fuso"):
            raise ValueError("`quando` sem fuso e sem `fuso`")
        try:
            when = when.replace(tzinfo=ZoneInfo(post["fuso"]))
        except ZoneInfoNotFoundError as e:
            raise ValueError(f"fuso desconhecido: {post['fuso']}") from e
    return when.astimezone(UTC)


def _content(post: dict[str, Any]) -> str:
    """Legenda + hashtags + identificações em falta, em HTML (o Postiz guarda o conteúdo do editor em HTML)."""
    text = post["legenda"].strip()
    extra = [t for t in (post.get("hashtags") or []) + (post.get("identificacoes") or []) if t and t not in text]
    lines = text.splitlines() + ([""] + [" ".join(extra)] if extra else [])
    return "".join(f"<p>{html.escape(line, quote=False)}</p>" if line.strip() else "<p></p>" for line in lines)


def _ai_labelled(post: dict[str, Any]) -> bool:
    return bool(AI_LABEL.search(" ".join(post.get("identificacoes") or [])))


def _settings(ident: str, post: dict[str, Any]) -> dict[str, Any]:
    settings = {**DEFAULT_SETTINGS.get(ident, {}), **(post.get("settings") or {})}
    if ident == "tiktok" and "video_made_with_ai" not in settings:
        settings["video_made_with_ai"] = _ai_labelled(post)  # AI Act, art. 50: o rótulo do TikTok segue o pacote
    missing = [k for k in REQUIRED_SETTINGS.get(ident, ()) if not settings.get(k)]
    if missing:
        raise ValueError(f"{ident} exige settings: {', '.join(missing)}")
    settings.pop("__type", None)
    return {**settings, "__type": ident}


def _alts(post: dict[str, Any], files: list[str]) -> list[str]:
    alt = post.get("alt")
    if isinstance(alt, str):
        out = [alt] * len(files)
    elif isinstance(alt, dict):
        out = [alt.get(f) or alt.get(Path(f).name) or "" for f in files]
    else:
        out = list(alt or []) + [""] * len(files)
    out = [str(a).strip() for a in out[:len(files)]]
    if any(not a for a in out):
        raise ValueError("ficheiros sem texto alternativo")
    return out


def _integration(rede: str, explicit: str | None, overrides: dict[str, str],
                 available: list[dict[str, Any]] | None) -> str | None:
    """Id da integração do Postiz. Na simulação (`available is None`) fica por resolver até ao envio."""
    key = rede.strip().lower()
    idents = NETWORKS.get(key)
    if not idents and not (explicit or key in overrides):
        raise ValueError(f"rede não suportada: {rede}")
    if explicit:
        return explicit
    if key in overrides:
        return overrides[key]
    if available is None:
        return None
    found = [i for i in available if i.get("identifier") in idents and not i.get("disabled")]
    if len(found) != 1:
        raise ValueError(f"{len(found)} integrações activas do Postiz para `{rede}`: indica qual com --integration {key}=<id>")
    return str(found[0]["id"])


def _safe_file(run_dir: Path, rel: str) -> Path:
    raw = run_dir / rel
    p, root = raw.resolve(), run_dir.resolve()
    if root not in p.parents or raw.is_symlink() or not p.is_file():
        raise ValueError(f"ficheiro fora do run ou inexistente: {rel}")
    return p


def build(run_dir: Path, package: dict[str, Any], *, schedule: bool, overrides: dict[str, str],
          available: list[dict[str, Any]] | None, now: datetime) -> list[dict[str, Any]]:
    """Um item por post: payload pronto (sem imagens enviadas ainda) ou recusa com motivo."""
    items = []
    for n, post in enumerate(package["posts"]):
        item: dict[str, Any] = {"post": n, "rede": post["rede"]}
        try:
            when = _when_utc(post)
            if when <= now:
                raise ValueError(f"data no passado: {when.isoformat()}")
            if PLACEHOLDER in post["legenda"]:
                raise ValueError(f"legenda com {PLACEHOLDER}")
            names = list(post.get("ficheiros") or [])
            files = [_safe_file(run_dir, f) for f in names]
            alts = _alts(post, names)
            iid = _integration(post["rede"], post.get("integracao"), overrides, available)
            ident = next((i.get("identifier") for i in available or [] if str(i.get("id")) == iid),
                         (NETWORKS.get(post["rede"].strip().lower()) or (post["rede"].lower(),))[0])
            payload = {
                "type": "schedule" if schedule else "draft",
                "date": when.isoformat().replace("+00:00", "Z"),
                "shortLink": False,
                "tags": [],
                "posts": [{"integration": {"id": iid or "(resolvida no envio)"},
                           "value": [{"content": _content(post), "image": []}],
                           "settings": _settings(ident, post)}],
            }
        except (ValueError, KeyError) as e:
            items.append({**item, "estado": "recusado", "motivo": str(e)})
            continue
        canon = json.dumps({"payload": payload, "files": [str(f.relative_to(run_dir.resolve())) for f in files]},
                           sort_keys=True, ensure_ascii=False)
        items.append({**item, "estado": "pronto", "quando_utc": payload["date"], "integracao": iid,
                      "ficheiros": [[str(f), a] for f, a in zip(files, alts, strict=True)], "payload": payload,
                      "sha256": hashlib.sha256(canon.encode()).hexdigest()})
    return items


# --------------------------------------------------------------------------- envio


def dispatch(run_dir: Path, *, send: bool = False, schedule: bool = False, overrides: dict[str, str] | None = None,
             client: Client | None = None, now: datetime | None = None) -> dict[str, Any]:
    run_dir = Path(run_dir)
    ev = evidence(run_dir)
    package = json.loads((run_dir / ev["package"]).read_text(encoding="utf-8"))
    try:
        jsonschema.validate(package, PACKAGE_SCHEMA)
    except jsonschema.ValidationError as e:
        raise PostizError(f"pacote inválido: {e.message}") from e
    if send and client is None:
        url, key = os.environ.get("POSTIZ_API_URL"), os.environ.get("POSTIZ_API_KEY")
        if not url or not key:
            raise PostizError("--send precisa de POSTIZ_API_URL e POSTIZ_API_KEY no ambiente")
        client = Client(url, key)
    available = client.integrations() if send else None
    items = build(run_dir, package, schedule=schedule, overrides=overrides or {}, available=available,
                  now=now or datetime.now(UTC))

    report_path = run_dir / REPORT
    previous = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    sent = {i["sha256"]: i for i in previous.get("items", []) if i.get("estado") in ("enviado", "ja_enviado")}
    report: dict[str, Any] = {"run_id": ev["run_id"],
                              "modo": ("agendar" if schedule else "rascunho") if send else "simulacao",
                              "aprovacao": {"passo": ev["gate"], "em": ev["approved_at"]}, "items": items}

    def save() -> None:
        counts: dict[str, int] = {}
        for i in items:
            counts[i["estado"]] = counts.get(i["estado"], 0) + 1
        report["contagens"] = counts
        report_path.parent.mkdir(parents=True, exist_ok=True)
        clean = {**report, "items": [{k: v for k, v in i.items() if k != "ficheiros"} for i in items]}
        report_path.write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    failed = False
    for item in items:
        if item["estado"] != "pronto":
            continue
        if item["sha256"] in sent:
            item.update(estado="ja_enviado", postiz=sent[item["sha256"]].get("postiz"))
        elif not send:
            item["estado"] = "simulado"
        elif failed:
            item.update(estado="nao_enviado", motivo="parado depois de um erro do Postiz")
        else:
            try:
                images = [{**client.upload(Path(f).name, Path(f).read_bytes()), "alt": a} for f, a in item["ficheiros"]]
                item["payload"]["posts"][0]["value"][0]["image"] = images
                item.update(estado="enviado", postiz=client.create(item["payload"]))
            except PostizError as e:
                failed = True
                item.update(estado="erro", motivo=str(e))
        save()  # depois de cada envio: um erro a meio nunca leva a reenviar o que já foi
    save()
    items[:] = [{k: v for k, v in i.items() if k != "ficheiros"} for i in items]
    counts = report["contagens"]
    EventLog(run_dir / "events.jsonl").append(
        "postiz_dispatch", ev["run_id"],
        {"modo": report["modo"], "contagens": counts, "sha256": [i.get("sha256") for i in items if i.get("sha256")]},
        actor={"kind": "human", "id": "cli"},
    )
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m plan_runner.postiz",
                                description="Envia o pacote aprovado de um run para o Postiz (simula por omissão).")
    p.add_argument("run_dir", type=Path)
    p.add_argument("--send", action="store_true", help="Envia de facto (rascunhos no Postiz). Precisa de POSTIZ_API_URL e POSTIZ_API_KEY")
    p.add_argument("--schedule", action="store_true", help="Com --send: agenda em vez de criar rascunhos")
    p.add_argument("--integration", action="append", default=[], metavar="REDE=ID", help="Integração do Postiz para uma rede")
    a = p.parse_args(argv)
    if a.schedule and not a.send:
        p.error("--schedule só faz sentido com --send")
    overrides = {}
    for kv in a.integration:
        rede, sep, iid = kv.partition("=")
        if not sep or not iid:
            p.error(f"--integration inválido: {kv}")
        overrides[rede.strip().lower()] = iid.strip()
    try:
        report = dispatch(a.run_dir, send=a.send, schedule=a.schedule, overrides=overrides)
    except (PostizError, OSError, json.JSONDecodeError) as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 1
    print(json.dumps({k: report[k] for k in ("run_id", "modo", "contagens")}, ensure_ascii=False))
    for i in report["items"]:
        print(f"  post {i['post']} ({i['rede']}): {i['estado']}" + (f" — {i['motivo']}" if i.get("motivo") else ""))
    bad = {"recusado", "erro", "nao_enviado"} & set(report["contagens"])
    return 2 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
