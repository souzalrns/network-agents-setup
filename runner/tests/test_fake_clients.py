"""Clientes FICTÍCIOS (scripts/seed_fake_clients.py): a memória de clientes funciona sem dados reais.

Sem BD: determinismo, prefixo FAKE-, contactos não reais, recusa de produção, e o
working_memory.py a ler o MEMORY.md gerado (o que o engine injecta no prompt, S30).
Com BD descartável (fixture `disposable_pg`: RAG_TEST_DATABASE_URL ou testcontainers):
a L4 guarda e devolve os factos de cada cliente no âmbito certo, um cliente nunca vê
os factos de outro, e a limpeza só apaga FAKE-.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("faker")

from plan_runner import memory_l4 as l4  # noqa: E402
from plan_runner import working_memory as wm  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_seed():
    spec = importlib.util.spec_from_file_location("seed_fake_clients", REPO_ROOT / "scripts/seed_fake_clients.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["seed_fake_clients"] = mod  # o @dataclass precisa do módulo registado
    spec.loader.exec_module(mod)
    return mod


seed = _load_seed()


# --------------------------------------------------------------------------- sem BD


def test_geracao_e_deterministica_e_marcada_fake():
    a, b = seed.generate_clients(5, seed=7), seed.generate_clients(5, seed=7)
    assert [c.client_id for c in a] == [c.client_id for c in b]
    assert [c.memory_md() for c in a] == [c.memory_md() for c in b]
    assert seed.generate_clients(5, seed=8)[0].company != a[0].company or seed.generate_clients(5, seed=8)[0].contact_name != a[0].contact_name
    ids = [c.client_id for c in a]
    assert len(set(ids)) == 5 and all(i.startswith("FAKE-") for i in ids)


def test_contactos_nunca_sao_reais():
    for c in seed.generate_clients(12):
        assert seed.RESERVED_EMAIL.search(c.contact_email), c.contact_email  # RFC 2606
        assert "DADOS FICTÍCIOS" in c.memory_md()


def test_ids_sao_ascii_e_legiveis():
    assert seed._slug("Gonçalves Araújo") == "goncalves-araujo"
    assert all(c.client_id.isascii() and " " not in c.client_id for c in seed.generate_clients(10))


def test_n_invalido_e_recusado():
    with pytest.raises(ValueError):
        seed.generate_clients(0)


@pytest.mark.parametrize("url", [
    None, "",
    "postgresql://postgres:x@db.mpsuurqilnhsvbnjmrpm.supabase.co:5432/postgres",
    "postgresql://u:p@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
    "postgresql://u:p@10.0.0.5:5432/db",
    "mysql://u:p@localhost/db",
])
def test_recusa_bd_que_nao_e_local(url):
    with pytest.raises(ValueError):
        seed.assert_safe_database_url(url)


def test_aceita_local_e_host_de_testcontainer():
    assert seed.assert_safe_database_url("postgresql://p:p@localhost:5432/x")
    assert seed.assert_safe_database_url("postgresql://p:p@172.17.0.1:5555/x", extra_hosts=frozenset({"172.17.0.1"}))


def test_nunca_le_o_database_url_do_ambiente(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.x.supabase.co:5432/postgres")
    with pytest.raises(SystemExit):
        seed.main(["--n", "1"])  # sem --memory-root / --database-url / --json: recusa, não cai no env
    assert "supabase" not in capsys.readouterr().out


def test_working_memory_le_o_cliente_ficticio(tmp_path):
    clients = seed.generate_clients(3)
    paths = seed.write_memory_files(clients, tmp_path)
    assert len(paths) == 3
    for c in clients:
        assert wm.resolve_memory_path(tmp_path, c.client_id) == tmp_path / "memory" / c.client_id / "MEMORY.md"
        text = wm.read_memory(c.client_id, repo_root=tmp_path)
        assert c.company in text and c.facts[0] in text
    assert wm.read_memory("FAKE-9999-nao-existe", repo_root=tmp_path) is None


def test_limpeza_de_ficheiros_so_apaga_fake(tmp_path):
    seed.write_memory_files(seed.generate_clients(2), tmp_path)
    real = tmp_path / "memory" / "cliente-real" / "MEMORY.md"
    real.parent.mkdir(parents=True)
    real.write_text("não mexer", encoding="utf-8")
    assert seed.cleanup_files(tmp_path) == 2
    assert real.is_file() and not any(p.name.startswith("FAKE-") for p in (tmp_path / "memory").iterdir())


def test_cli_json_e_ficheiros(tmp_path, capsys):
    assert seed.main(["--n", "2", "--json", "--memory-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert '"client_id": "FAKE-0001-' in out and "MEMORY.md escritos: 2" in out


# --------------------------------------------------------------------------- com BD descartável


def test_l4_guarda_isola_e_limpa_os_clientes_ficticios(db, disposable_pg):
    seed.assert_safe_database_url(disposable_pg["url"], extra_hosts=disposable_pg["hosts"])
    real = l4.remember(db, scope=l4.Scope("project", "cliente-real"), statement="facto real", actor="human:maestro", status="active")
    clients = seed.generate_clients(3)
    rows = seed.insert_l4(db, clients)
    assert len(rows) == sum(len(c.facts) for c in clients)
    assert all(r["status"] == "active" and r["scope_id"].startswith("FAKE-") for r in rows)

    a, b = clients[0], clients[1]
    got_a = l4.recall(db, scopes=[l4.Scope("project", a.client_id)], limit=50)
    assert {r["statement"] for r in got_a} == set(a.facts)
    # isolamento: o âmbito de um cliente nunca devolve factos de outro
    assert not {r["statement"] for r in got_a} & set(b.facts)
    assert all(r["scope_id"] == a.client_id for r in got_a)

    # pesquisa por similaridade dentro do âmbito (embedding determinístico, sem Gemini)
    top = l4.recall(db, scopes=[l4.Scope("project", a.client_id)], query=a.facts[2], limit=1, embed=seed.fake_embed)
    assert top and top[0]["statement"] == a.facts[2]

    # o direito ao esquecimento (forget) funciona nos fictícios
    l4.forget(db, rows[0]["id"], actor="human:maestro", reason="teste de eliminação")
    assert rows[0]["statement"] not in {r["statement"] for r in l4.recall(db, scopes=[l4.Scope("project", a.client_id)], limit=50)}

    # limpeza: só FAKE-, o cliente real fica
    assert seed.cleanup_l4(db) == len(rows)
    with db.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM memory_l4 WHERE scope_id LIKE 'FAKE-%%'")
        assert cur.fetchone()["n"] == 0
        cur.execute("SELECT id FROM memory_l4")
        assert [r["id"] for r in cur.fetchall()] == [real["id"]]
    db.commit()
