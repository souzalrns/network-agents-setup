"""Clientes FICTÍCIOS para testes da memória de clientes (working memory S30 + L4).

Nunca toca em produção. Gera N clientes com o Faker (seed fixa → sempre os mesmos),
todos com o prefixo `FAKE-` no id, para se limparem com um filtro só.

Onde fica a "memória do cliente" (não há tabela `client_memory`):
- working memory: `<root>/memory/<client_id>/MEMORY.md` (runner/plan_runner/working_memory.py;
  `/memory/*/` está no .gitignore: docs/governance/PRIVACY-POLICY.md §2);
- L4: tabela `memory_l4`, âmbito `project:<client_id>` (runner/plan_runner/memory_l4.py).

Regras de segurança:
- a BD tem de ser dada explicitamente (`--database-url`); o `DATABASE_URL` do ambiente
  (que aponta para o Supabase) NUNCA é lido;
- só aceita Postgres local (localhost, 127.0.0.1, ::1) ou o host de um testcontainer;
  recusa qualquer host do Supabase;
- os e-mails são de domínios reservados (RFC 2606: example.com/.net/.org) e os telefones
  são do Faker: nenhum contacto real;
- a limpeza só apaga linhas `FAKE-` marcadas com `metadata.fake = true`.

Uso:
    python scripts/seed_fake_clients.py --n 5 --memory-root /tmp/fake-run
    python scripts/seed_fake_clients.py --n 5 --database-url postgresql://postgres:postgres@localhost:5432/ragtest
    python scripts/seed_fake_clients.py --cleanup --database-url ... --memory-root /tmp/fake-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "runner"))

from plan_runner import memory_l4 as l4  # noqa: E402

PREFIX = "FAKE-"
SEED_DEFAULT = 4200
ACTOR = "human:seed-fake-clients"
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
RESERVED_EMAIL = re.compile(r"@example\.(com|net|org)$")
SECTORS = ("restaurante", "imobiliária", "clínica dentária", "escritório de advocacia", "loja online", "ginásio")


@dataclass
class FakeClient:
    client_id: str
    company: str
    sector: str
    city: str
    contact_name: str
    contact_email: str
    contact_phone: str
    facts: list[str] = field(default_factory=list)

    def memory_md(self) -> str:
        lines = [
            f"# {self.company} ({self.client_id})",
            "",
            "> DADOS FICTÍCIOS gerados por scripts/seed_fake_clients.py (Faker). Não é um cliente real.",
            "",
            f"- Sector: {self.sector}",
            f"- Cidade: {self.city}",
            f"- Contacto: {self.contact_name} <{self.contact_email}>, {self.contact_phone}",
            "",
            "## Factos do projecto",
        ]
        lines += [f"- {f}" for f in self.facts]
        return "\n".join(lines) + "\n"


def _slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:24] or "cliente"


def generate_clients(n: int, seed: int = SEED_DEFAULT, locale: str = "pt_BR") -> list[FakeClient]:
    """N clientes determinísticos (mesma seed + mesma versão do Faker → mesmos dados)."""
    if n < 1:
        raise ValueError("n tem de ser >= 1")
    from faker import Faker

    fake = Faker(locale)
    fake.seed_instance(seed)
    clients: list[FakeClient] = []
    for i in range(1, n + 1):
        company = fake.company()
        sector = SECTORS[(i - 1) % len(SECTORS)]
        name = fake.name()
        user = _slug(name).replace("-", ".") or f"contacto{i}"
        domain = ("example.com", "example.net", "example.org")[i % 3]
        client = FakeClient(
            client_id=f"{PREFIX}{i:04d}-{_slug(company)}",
            company=company,
            sector=sector,
            city=fake.city(),
            contact_name=name,
            contact_email=f"{user}@{domain}",
            contact_phone=fake.phone_number(),
        )
        client.facts = [
            f"O cliente {company} é um(a) {sector} em {client.city}.",
            f"O público principal tem entre {20 + i % 30} e {45 + i % 20} anos.",
            f"Tom de voz preferido: {('próximo', 'formal', 'técnico')[i % 3]}.",
            f"Orçamento mensal de marketing: {1000 + 250 * i} reais.",
        ]
        clients.append(client)
    return clients


def write_memory_files(clients: list[FakeClient], root: Path) -> list[Path]:
    """Escreve <root>/memory/<client_id>/MEMORY.md (o formato que o working_memory.py lê)."""
    out = []
    for c in clients:
        p = Path(root) / "memory" / c.client_id / "MEMORY.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(c.memory_md(), encoding="utf-8")
        out.append(p)
    return out


def assert_safe_database_url(url: str | None, *, extra_hosts: frozenset[str] = frozenset()) -> str:
    """Só Postgres local ou de testcontainer. Nunca o Supabase. Devolve o URL validado."""
    if not url or not url.strip():
        raise ValueError("--database-url é obrigatório (o DATABASE_URL do ambiente nunca é usado)")
    parts = urlsplit(url.strip())
    if parts.scheme not in ("postgresql", "postgres"):
        raise ValueError("só URLs postgresql://")
    host = (parts.hostname or "").lower()
    if "supabase" in host or "pooler" in host:
        raise ValueError("recusado: host do Supabase (produção). Usa um Postgres descartável")
    if host not in LOCAL_HOSTS | extra_hosts:
        raise ValueError(f"recusado: host {host!r} não é local nem de testcontainer")
    return url.strip()


def fake_embed(text: str) -> list[float]:
    """Embedding determinístico (sem Gemini, custo zero): 768 dims a partir do sha256."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    return [((h[i % 32] / 255.0) - 0.5) for i in range(768)]


def insert_l4(conn: Any, clients: list[FakeClient], *, seed: int = SEED_DEFAULT, embed=fake_embed) -> list[dict[str, Any]]:
    """Cada facto vira uma linha `active` em memory_l4, no âmbito project:<client_id>."""
    rows = []
    for c in clients:
        for fact in c.facts:
            rows.append(l4.remember(
                conn,
                scope=l4.Scope("project", c.client_id),
                statement=fact,
                subject=c.company,
                actor=ACTOR,
                status="active",
                tags=["FAKE", c.sector],
                metadata={"fake": True, "seed": seed, "generator": "seed_fake_clients"},
                embed=embed,
            ))
    return rows


def cleanup_l4(conn: Any) -> int:
    """Apaga SÓ as linhas FAKE- (âmbito + metadata.fake). Usa o desvio de compliance do trigger."""
    with conn.cursor() as cur:
        cur.execute("SET LOCAL memory_l4.allow_delete = 'on'")
        cur.execute(
            "DELETE FROM memory_l4 WHERE scope_id LIKE %s AND (metadata->>'fake') = 'true'",
            (PREFIX + "%",),
        )
        n = cur.rowcount
    conn.commit()
    return n


def cleanup_files(root: Path) -> int:
    base = Path(root) / "memory"
    if not base.is_dir():
        return 0
    gone = 0
    for d in base.iterdir():
        if d.is_dir() and d.name.startswith(PREFIX):
            shutil.rmtree(d)
            gone += 1
    return gone


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)
    ap.add_argument("--memory-root", type=Path, help="pasta onde criar memory/<client_id>/MEMORY.md")
    ap.add_argument("--database-url", help="Postgres LOCAL/descartável com o SQL da L4 aplicado")
    ap.add_argument("--cleanup", action="store_true", help="apaga só os FAKE- (ficheiros e/ou L4)")
    ap.add_argument("--json", action="store_true", help="imprime os clientes gerados em JSON")
    args = ap.parse_args(argv)

    if not (args.memory_root or args.database_url or args.json):
        ap.error("indica --memory-root, --database-url e/ou --json")
    url = assert_safe_database_url(args.database_url) if args.database_url else None

    if args.cleanup:
        if args.memory_root:
            print(f"ficheiros FAKE- apagados: {cleanup_files(args.memory_root)}")
        if url:
            with l4.connect(url) as conn:
                print(f"linhas FAKE- apagadas da memory_l4: {cleanup_l4(conn)}")
        return 0

    clients = generate_clients(args.n, args.seed)
    if args.json:
        print(json.dumps([asdict(c) for c in clients], ensure_ascii=False, indent=2))
    if args.memory_root:
        print(f"MEMORY.md escritos: {len(write_memory_files(clients, args.memory_root))}")
    if url:
        with l4.connect(url) as conn:
            print(f"linhas inseridas na memory_l4: {len(insert_l4(conn, clients, seed=args.seed))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
