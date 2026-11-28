#!/usr/bin/env python3
"""Lê o JSON-lines do gosom/google-maps-scraper e grava na tabela `leads` do Supabase.

Uso: leads_to_supabase.py <results.json> <query> [nicho]

- Sem SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY faz só um resumo (dry-run) e sai com 0.
- Duplicados (mesmo place_key) são ignorados: nunca sobrescreve o status de um lead já trabalhado.
- Só stdlib, para não gastar tempo de instalação no runner.
"""
from __future__ import annotations

import http.client
import json
import os
import sys
import urllib.parse


def parse_line(raw: dict, query: str, nicho: str | None) -> dict | None:
    nome = (raw.get("title") or "").strip()
    if not nome:
        return None
    morada = raw.get("address") or ""
    place_key = raw.get("place_id") or raw.get("data_id") or raw.get("cid") or f"{nome}|{morada}"
    emails = [e.strip() for e in (raw.get("emails") or []) if isinstance(e, str) and e.strip()]
    # o gosom escreve "longtitude" (typo no upstream); aceitar as duas grafias
    lon = raw.get("longtitude", raw.get("longitude"))
    return {
        "place_key": str(place_key),
        "query": query,
        "nicho": nicho or None,
        "nome": nome,
        "categoria": raw.get("category") or None,
        "morada": morada or None,
        "telefone": raw.get("phone") or None,
        "website": raw.get("website") or None,
        "email": emails[0] if emails else None,
        "emails": emails,
        "rating": raw.get("review_rating") or None,
        "reviews": raw.get("review_count") or None,
        "latitude": raw.get("latitude") or None,
        "longitude": lon or None,
        "maps_url": raw.get("link") or None,
    }


def load(path: str, query: str, nicho: str | None) -> list[dict]:
    rows: dict[str, dict] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = parse_line(json.loads(line), query, nicho)
            except json.JSONDecodeError:
                continue
            if not row:
                continue
            old = rows.get(row["place_key"])
            # em duplicados fica a linha mais completa
            if old is None or sum(v is not None for v in row.values()) > sum(v is not None for v in old.values()):
                rows[row["place_key"]] = row
    return list(rows.values())


def upload(rows: list[dict], url: str, key: str) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise SystemExit("SUPABASE_URL tem de começar por https://")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore-duplicates,return=minimal",
    }
    conn = http.client.HTTPSConnection(parts.hostname, parts.port or 443, timeout=60)
    try:
        for i in range(0, len(rows), 200):
            conn.request(
                "POST",
                "/rest/v1/leads?on_conflict=place_key",
                body=json.dumps(rows[i : i + 200]),
                headers=headers,
            )
            resp = conn.getresponse()
            resp.read()
            if resp.status >= 300:
                raise SystemExit(f"Supabase respondeu {resp.status}")
    finally:
        conn.close()


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    path, query = sys.argv[1], sys.argv[2]
    nicho = sys.argv[3] if len(sys.argv) > 3 else None
    rows = load(path, query, nicho)
    com_email = sum(1 for r in rows if r["email"])
    com_site = sum(1 for r in rows if r["website"])
    print(f"Encontrados: {len(rows)} | com site: {com_site} | com email: {com_email}")
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not rows:
        return 0
    if not url or not key:
        print("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY em falta: dry-run, nada gravado.")
        return 0
    upload(rows, url, key)
    print("Gravado na tabela leads (duplicados ignorados).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
