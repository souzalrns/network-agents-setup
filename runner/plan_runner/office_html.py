"""Escritório 2D (OFFICE-A3, v0): o snapshot do office.py numa página HTML autónoma.

Sem servidor, sem rede, sem JavaScript e sem custo: um ficheiro que abre em qualquer browser
(também no telemóvel). Três níveis na mesma página:
  1. empresa: as 2 alas, cada departamento com TODOS os agentes em miniatura;
  2. departamento: os lugares, com o que cada um faz e os agentes maiores;
  3. lugar: a tabela dos agentes (estado, evento, run, passo, hora, se também está no MCP).

Os avatares são os "cápsula" do protótipo (desenho original, SVG puro): a cor e o símbolo
dizem o departamento; a antena, os olhos, a boca, o braço e o balão dizem o estado.
O estado também vai sempre em texto (nunca só pela cor).

CLI:  cd runner && python -m plan_runner.office --html ../pilots/office/index.html [--label TEXTO] RUN_DIR...
"""
from __future__ import annotations

from html import escape
from typing import Any

STATE_LABEL = {
    "error": "erro",
    "needs": "precisa de ti",
    "working": "a trabalhar",
    "thinking": "a pensar",
    "idle": "à espera",
    "untracked": "sem telemetria",
}
STATE_COLOR = {
    "error": "#DC2626", "needs": "#F97316", "working": "#2563EB",
    "thinking": "#A855F7", "idle": "#9CA3AF", "untracked": "#D1D5DB",
}
WING_LABEL = {"funcoes": "Ala das funções", "negocios": "Ala dos negócios"}

# Departamento -> (cor do corpo, símbolo na barriga). Um departamento novo sem tema usa o neutro.
THEME = {
    "direcao": ("#475569", "star"),
    "marketing": ("#FF8A3D", "megaphone"),
    "comercial": ("#0D9488", "tag"),
    "atendimento": ("#60A5FA", "chat"),
    "financas": ("#2FB67C", "euro"),
    "juridico": ("#8B5CF6", "scale"),
    "software": ("#4F7CFF", "code"),
    "seguranca": ("#EF4444", "shield"),
    "pesquisa": ("#22B8CF", "lens"),
    "trading": ("#F2C230", "chart"),
    "jogos": ("#EC4899", "gamepad"),
    "documentacao": ("#A3E635", "page"),
    "negocio-construcao": ("#C2410C", "house"),
    "negocio-viannalegal": ("#7C3AED", "scale"),
    "negocio-imobiliario": ("#0EA5E9", "house"),
    "negocio-produto": ("#6366F1", "code"),
    "negocio-formacao": ("#22C55E", "cap"),
    "negocio-saude": ("#F43F5E", "heart"),
}
NEUTRAL = ("#94A3B8", "star")

_ICON = {
    "megaphone": '<polygon points="53,101 53,107 57,107 66,111 66,97 57,101"/>',
    "code": '<polyline points="56,100 52,104 56,108"/><polyline points="64,100 68,104 64,108"/><line x1="61.5" y1="99" x2="58.5" y2="109"/>',
    "scale": '<line x1="60" y1="97" x2="60" y2="111"/><line x1="54" y1="99" x2="66" y2="99"/><path d="M51 105 L54 99 L57 105 Z"/><path d="M63 105 L66 99 L69 105 Z"/><line x1="56" y1="111" x2="64" y2="111"/>',
    "lens": '<circle cx="58" cy="102" r="4.5"/><line x1="61.5" y1="105.5" x2="66" y2="110"/>',
    "euro": '<circle cx="60" cy="104" r="7"/><text x="60" y="107.4" style="fill:#111827;stroke:none;font:700 9.5px system-ui,sans-serif;text-anchor:middle">€</text>',
    "chart": '<polyline points="52,109 57,103 61,106 68,98"/><polyline points="63.5,98 68,98 68,102.5"/>',
    "gamepad": '<rect x="51" y="99.5" width="18" height="9.5" rx="4.75"/><line x1="55.5" y1="102" x2="55.5" y2="106.5"/><line x1="53.25" y1="104.25" x2="57.75" y2="104.25"/>',
    "shield": '<path d="M60 96 L67 99 V104 C67 108 64 110.5 60 112 C56 110.5 53 108 53 104 V99 Z"/>',
    "page": '<path d="M55 97 H63 L66 100 V111 H55 Z"/><line x1="57.5" y1="102" x2="63.5" y2="102"/><line x1="57.5" y1="105" x2="63.5" y2="105"/>',
    "star": '<path d="M60 96 L62.2 101.8 L68 104 L62.2 106.2 L60 112 L57.8 106.2 L52 104 L57.8 101.8 Z"/>',
    "tag": '<path d="M52 98 H61 L68 105 L61 112 L52 112 Z"/><circle cx="56" cy="102" r="1.3"/>',
    "chat": '<path d="M52 98 H68 V107 H59 L55 111 V107 H52 Z"/>',
    "house": '<path d="M52 104 L60 97 L68 104"/><path d="M54.5 102.5 V111 H65.5 V102.5"/><line x1="60" y1="111" x2="60" y2="106"/>',
    "cap": '<path d="M50 102 L60 98 L70 102 L60 106 Z"/><path d="M55 104 V108 C57 110 63 110 65 108 V104"/>',
    "heart": '<path d="M60 111 C53 106 51 102.5 53.5 99.5 C55.5 97.5 58.5 98 60 100.5 C61.5 98 64.5 97.5 66.5 99.5 C69 102.5 67 106 60 111 Z"/>',
}

_EYES = {
    "working": '<circle cx="48" cy="50" r="11" class="w"/><circle cx="72" cy="50" r="11" class="w"/>'
               '<circle cx="49" cy="54.5" r="5" class="k"/><circle cx="73" cy="54.5" r="5" class="k"/>'
               '<path d="M54 73 H66" class="m"/>',
    "thinking": '<circle cx="48" cy="50" r="11" class="w"/><circle cx="72" cy="50" r="11" class="w"/>'
                '<circle cx="45" cy="45.5" r="5" class="k"/><circle cx="69" cy="45.5" r="5" class="k"/>'
                '<path d="M54 74 Q60 71 66 73" class="m"/>',
    "needs": '<circle cx="48" cy="50" r="12" class="w"/><circle cx="72" cy="50" r="12" class="w"/>'
             '<circle cx="48" cy="50" r="6.5" class="k"/><circle cx="72" cy="50" r="6.5" class="k"/>'
             '<circle cx="50.5" cy="47.5" r="2" style="fill:#fff"/><circle cx="74.5" cy="47.5" r="2" style="fill:#fff"/>'
             '<ellipse cx="60" cy="75" rx="4" ry="5" class="k"/>',
    "error": '<circle cx="48" cy="50" r="11" class="w"/><circle cx="72" cy="50" r="11" class="w"/>'
             '<g style="stroke:#DC2626;stroke-width:2.8;stroke-linecap:round">'
             '<line x1="43.5" y1="45.5" x2="52.5" y2="54.5"/><line x1="52.5" y1="45.5" x2="43.5" y2="54.5"/>'
             '<line x1="67.5" y1="45.5" x2="76.5" y2="54.5"/><line x1="76.5" y1="45.5" x2="67.5" y2="54.5"/></g>'
             '<path d="M52 75 Q56 71 60 75 Q64 79 68 75" class="m"/>',
    "idle": '<path d="M39 51 Q48 57 57 51" class="m"/><path d="M63 51 Q72 57 81 51" class="m"/>'
            '<path d="M55 72 Q60 75 65 72" class="m"/>',
    "untracked": '<circle cx="48" cy="50" r="11" class="w"/><circle cx="72" cy="50" r="11" class="w"/>'
                 '<circle cx="48" cy="50" r="4" style="fill:#9CA3AF"/><circle cx="72" cy="50" r="4" style="fill:#9CA3AF"/>'
                 '<path d="M54 73 H66" class="m"/>',
}
_BUBBLE = {"thinking": ("• • •", "#7E22CE"), "needs": ("!", "#C2410C"), "idle": ("z", "#4B5563")}

_CSS = """
:root{--ground:#F3F4F6;--card:#FFFFFF;--ink:#111827;--muted:#4B5563;--line:#E5E7EB}
@media (prefers-color-scheme: dark){:root{--ground:#0B1020;--card:#151B2E;--ink:#F3F4F6;--muted:#A7B0C0;--line:#26304A}}
*{box-sizing:border-box}body{margin:0;background:var(--ground);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1280px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:30px;margin:0 0 4px}h2{font-size:20px;margin:32px 0 12px}h3{font-size:17px;margin:0}
.muted{color:var(--muted)}.banner{background:#FFF7ED;color:#7C2D12;border:1px solid #FDBA74;border-radius:12px;padding:10px 14px;margin:12px 0}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 4px}.pill{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;background:var(--card);border:1px solid var(--line);font-size:13px;font-weight:600;white-space:nowrap}
.dot{width:9px;height:9px;border-radius:999px;display:inline-block}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:8px;color:inherit;text-decoration:none}
a.card:hover,a.card:focus-visible{outline:2px solid #2563EB;outline-offset:2px}
.head{display:flex;justify-content:space-between;align-items:center;gap:8px}
.minis{display:flex;flex-wrap:wrap;gap:2px}.seatline{font-size:12px;color:var(--muted);margin-top:2px}
.dept{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin:14px 0;scroll-margin-top:12px}
.seat{border-top:1px solid var(--line);padding:12px 0 4px}
.agents{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0}
.agent{display:flex;flex-direction:column;align-items:center;width:92px;text-align:center;font-size:11px;word-break:break-word}
details summary{cursor:pointer;color:var(--muted);font-size:13px;min-height:32px;display:flex;align-items:center}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
.empty{color:var(--muted);font-style:italic}
svg .w{fill:#fff;stroke:#111827;stroke-width:2.5}svg .k{fill:#111827}svg .m{fill:none;stroke:#111827;stroke-width:2.6;stroke-linecap:round}
@media (prefers-reduced-motion: reduce){svg animate,svg animateTransform{display:none}}
"""


def theme(dept_id: str) -> tuple[str, str]:
    return THEME.get(dept_id, NEUTRAL)


def avatar(color: str, icon: str, state: str, size: int, label: str) -> str:
    """Um agente em SVG (o estilo cápsula do protótipo). `label` vai para o leitor de ecrã."""
    h = round(size * 140 / 120)
    untracked = state == "untracked"
    led = STATE_COLOR.get(state, "#9CA3AF")
    body_style = f"fill:{color};stroke:#111827;stroke-width:3" + (";opacity:.45;stroke-dasharray:6 4" if untracked else "")
    led_fill = "#FFFFFF" if untracked else led
    blink = {"working": ("1;0.25;1", "1s"), "needs": ("1;0.4;1", "0.7s")}.get(state)
    anim = f'<animate attributeName="opacity" values="{blink[0]}" dur="{blink[1]}" repeatCount="indefinite"/>' if blink else ""
    arm = ('<g style="fill:none;stroke:#111827;stroke-width:3;stroke-linecap:round"><path d="M90 80 Q106 70 104 54"/>'
           f'<circle cx="104" cy="51" r="4.5" style="fill:{color};stroke-width:2.5"/></g>') if state == "needs" else \
          ('<g style="fill:none;stroke:#111827;stroke-width:3;stroke-linecap:round"><path d="M90 86 Q102 94 99 106"/>'
           f'<circle cx="99" cy="108" r="4" style="fill:{color};stroke-width:2.5"/></g>')
    bubble = ""
    if state in _BUBBLE:
        txt, col = _BUBBLE[state]
        bubble = ('<circle cx="86" cy="24" r="2.5" style="fill:#fff;stroke:#111827;stroke-width:1.8"/>'
                  '<rect x="86" y="2" width="30" height="18" rx="9" style="fill:#fff;stroke:#111827;stroke-width:2"/>'
                  f'<text x="101" y="15.5" style="fill:{col};font:700 12px system-ui,sans-serif;text-anchor:middle">{txt}</text>')
    return (
        f'<svg viewBox="0 0 120 140" width="{size}" height="{h}" role="img" aria-label="{escape(label)}">'
        f"<title>{escape(label)}</title>"
        '<ellipse cx="60" cy="135" rx="30" ry="4.5" style="fill:rgba(17,24,39,.12)"/>'
        '<rect x="47" y="122" width="10" height="11" rx="4" style="fill:#374151;stroke:#111827;stroke-width:2.5"/>'
        '<rect x="63" y="122" width="10" height="11" rx="4" style="fill:#374151;stroke:#111827;stroke-width:2.5"/>'
        f"{arm}"
        '<g style="fill:none;stroke:#111827;stroke-width:3;stroke-linecap:round"><path d="M30 86 Q18 94 21 106"/>'
        f'<circle cx="21" cy="108" r="4" style="fill:{color};stroke-width:2.5"/></g>'
        '<line x1="60" y1="21" x2="60" y2="10" style="stroke:#111827;stroke-width:3;stroke-linecap:round"/>'
        f'<circle cx="60" cy="7" r="5" style="fill:{led_fill};stroke:#111827;stroke-width:2">{anim}</circle>'
        f'<rect x="28" y="20" width="64" height="106" rx="32" style="{body_style}"/>'
        '<path d="M36 40 Q40 28 52 25" style="fill:none;stroke:rgba(255,255,255,.55);stroke-width:3.5;stroke-linecap:round"/>'
        f"{_EYES.get(state, _EYES['idle'])}"
        '<circle cx="60" cy="104" r="12" style="fill:#fff;stroke:#111827;stroke-width:2.5"/>'
        f'<g style="fill:none;stroke:#111827;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round">{_ICON.get(icon, _ICON["star"])}</g>'
        f"{bubble}</svg>"
    )


def _n(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def _when(iso: str) -> str:
    """2026-10-24T02:24:02.09+00:00 -> 24/10/2026 02:24 UTC (o resto fica como veio)."""
    try:
        date, time = iso.split("T", 1)
        y, m, d = date.split("-")
        return f"{d}/{m}/{y} {time[:5]} UTC"
    except ValueError:
        return iso


def _short(agent_id: str) -> str:
    return agent_id.split(":", 1)[-1].split(".", 1)[-1]


def _pill(state: str | None) -> str:
    if state is None:
        return '<span class="pill">sem agentes ainda</span>'
    return f'<span class="pill"><span class="dot" style="background:{STATE_COLOR[state]}"></span>{STATE_LABEL[state]}</span>'


def _label(agent: dict[str, Any], dept_name: str) -> str:
    return f"Agente IA {agent['id']} ({dept_name}): {STATE_LABEL.get(agent['state'], agent['state'])}"


def render(snapshot: dict[str, Any], label: str | None = None) -> str:
    depts = snapshot.get("departments") or []
    total = snapshot.get("agent_count", 0)
    counts: dict[str, int] = {}
    for d in depts:
        for s in d["seats"]:
            for a in s["agents"]:
                counts[a["state"]] = counts.get(a["state"], 0) + 1

    out = ['<!doctype html><html lang="pt"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           f"<title>Escritório dos Agentes</title><style>{_CSS}</style></head><body><main>",
           "<h1>Escritório dos Agentes</h1>",
           f'<p class="muted">{_n(total, "agente IA", "agentes IA")} · {_n(len(depts), "departamento", "departamentos")} · gerado em {escape(_when(str(snapshot.get("generated_at", ""))))}. '
           "Cada estado vem de um evento real do runner; os agentes do MCP de produção ainda não emitem eventos.</p>"]
    if label:
        out.append(f'<div class="banner">{escape(label)}</div>')
    out.append('<div class="legend">')
    for st in STATE_LABEL:
        out.append(f'<span class="pill">{avatar("#CBD5E1", "star", st, 22, STATE_LABEL[st])}{STATE_LABEL[st]} · {counts.get(st, 0)}</span>')
    out.append("</div>")

    # Nível 1 — empresa
    for wing in ("funcoes", "negocios"):
        out.append(f"<h2>{WING_LABEL[wing]}</h2><div class=\"grid\">")
        for d in (x for x in depts if x.get("wing") == wing):
            color, icon = theme(d["id"])
            minis = "".join(
                avatar(color, icon, a["state"], 30, _label(a, d["name"])) for s in d["seats"] for a in s["agents"]
            ) or '<span class="empty">sem agentes ainda</span>'
            lead = f' · lead: {escape(d["lead"])}' if d.get("lead") else ""
            out.append(
                f'<a class="card" href="#d-{escape(d["id"])}"><div class="head"><h3>{escape(d["name"])}</h3>{_pill(d["state"])}</div>'
                f'<div class="seatline">{_n(d["agent_count"], "agente", "agentes")} · {_n(len(d["seats"]), "lugar", "lugares")}{lead}</div>'
                f'<div class="minis">{minis}</div></a>'
            )
        out.append("</div>")

    # Níveis 2 e 3 — departamento e lugar
    out.append("<h2>Departamentos</h2>")
    for d in depts:
        color, icon = theme(d["id"])
        out.append(f'<section class="dept" id="d-{escape(d["id"])}"><div class="head"><h3>{escape(d["name"])}</h3>{_pill(d["state"])}</div>')
        if not d["seats"]:
            out.append('<p class="empty">Sem agentes ainda.</p>')
        for s in d["seats"]:
            out.append(f'<div class="seat"><div class="head"><strong>{escape(s["name"])}</strong>{_pill(s["state"])}</div>'
                       f'<div class="muted">{escape(s["does"])}</div><div class="agents">')
            for a in s["agents"]:
                out.append(f'<div class="agent">{avatar(color, icon, a["state"], 64, _label(a, d["name"]))}{escape(_short(a["id"]))}</div>')
            out.append('</div><details><summary>Ver estado de cada agente</summary><div class="tbl"><table>'
                       "<tr><th>Agente</th><th>Estado</th><th>Último evento</th><th>Run</th><th>Passo</th><th>Hora</th><th>No MCP</th></tr>")
            for a in s["agents"]:
                cells = [a["id"], STATE_LABEL.get(a["state"], a["state"]), a.get("event") or "—", a.get("run_id") or "—",
                         a.get("step_id") or "—", _when(a["at"]) if a.get("at") else "—", a.get("mcp") or "—"]
                out.append("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in cells) + "</tr>")
            out.append("</table></div></details></div>")
        out.append("</section>")
    if snapshot.get("unattributed"):
        out.append(f'<h2>Passos sem dono ({len(snapshot["unattributed"])})</h2><ul>')
        for u in snapshot["unattributed"]:
            out.append(f"<li>{escape(str(u.get('action')))} (run {escape(str(u.get('run_id')))}, passo {escape(str(u.get('step_id')))})</li>")
        out.append("</ul>")
    out.append("</main></body></html>")
    return "".join(out)
