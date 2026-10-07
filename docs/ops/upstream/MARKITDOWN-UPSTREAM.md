# Contribuição upstream no `microsoft/markitdown` (P-22 = Sim, ING-012)

**Estado:** texto preparado pelo Claude (2026-10-07). Quem publica é o DEV, na conta dele: é uma acção pública, e esta sessão não tem acesso ao repo upstream.
**Decisão:** P-22 = Sim (maestro, 2026-10-07), pela opção B: primeiro uma issue ou um comentário; um PR só depois da resposta dos maintainers e com o CLA da Microsoft assinado.

## 1. Verificação antes de publicar (2026-10-07)

Os 2 achados do T6b/T6c (`docs/ops/INGEST-DOCUMENT.md` §5) foram reproduzidos de novo com a versão mais recente, **MarkItDown 0.1.8** (`pip install "markitdown[docx,pdf]"`), num venv isolado e com o script da §4.

| Achado | Reproduz em 0.1.8? | Já existe no upstream? |
|---|---|---|
| A. Tabela DOCX sem `w:tblHeader`: sai com um cabeçalho vazio, e o cabeçalho real passa a 1.ª linha de dados | Sim | **Sim:** [issue #2157](https://github.com/microsoft/markitdown/issues/2157), aberta. O PR #2160, também aberto, trata só do escape de caracteres dessa issue, **não** do cabeçalho da tabela (verificado a 2026-10-07) |
| B. Ficheiro `.pdf` cujos bytes não são PDF: volta como texto, sem erro | Sim | Não encontrado. Mas pode ser o comportamento pretendido (deteção pelo conteúdo) |

## 2. Opções e recomendação

| Opção | O quê | Prós | Contras |
|---|---|---|---|
| A | Uma issue nova com os 2 achados | Um só sítio | O A é duplicado da #2157 (ruído para os maintainers); o B mistura bug com comportamento pretendido |
| **B (RECOMENDADA)** | **Comentário na #2157** com a reprodução mínima em 0.1.8, e nenhuma issue para o B | Junta-se ao fio que já existe, com a evidência mais útil (versão actual, 10 linhas, sem ficheiros anexos), e oferece um PR para a parte do cabeçalho, que ninguém está a corrigir; ruído zero | O B fica só na nossa documentação |
| C | Comentário na #2157 + uma *feature request* para o B (modo estrito: só o conversor do formato declarado) | Cobre os 2 | O nosso adapter já resolve o B sem mudar nada upstream (regista só o conversor do formato); um pedido sem caso de uso forte tende a ficar parado |

**Recomendação: B.** O achado A é o útil e já tem fio aberto, mas a parte do cabeçalho não tem PR: o comentário traz a reprodução na versão actual e oferece-se para a corrigir (o PR só depois de os maintainers responderem, com o CLA). O B não é claramente um bug: o MarkItDown detecta o tipo pelo conteúdo, e o nosso `ingest_document.py` já se protege com o `check_signature` e o registo de um só conversor. Se o maestro quiser mesmo o B, a opção C acrescenta-o como *feature request*, nunca como bug.

## 3. Texto do comentário na #2157 (opção B, em inglês)

> Still reproducible on **markitdown 0.1.8** (Linux, Python 3.12). Minimal repro, no attachments needed:
>
> ```python
> import docx
> from markitdown import MarkItDown
>
> d = docx.Document()
> t = d.add_table(rows=3, cols=2)
> for i, row in enumerate([("Name", "Qty"), ("apple", "3"), ("pear", "5")]):
>     for j, v in enumerate(row):
>         t.cell(i, j).text = v
> d.save("table-no-header.docx")
> print(MarkItDown(enable_plugins=False).convert_local("table-no-header.docx").markdown)
> ```
>
> Output:
>
> ```
> |  |  |
> | --- | --- |
> | Name | Qty |
> | apple | 3 |
> | pear | 5 |
> ```
>
> The table has no `w:tblHeader` on its first row (the python-docx default, and the common case in real Word files), so mammoth emits no `<thead>` and markdownify adds an empty header. Marking the first row as a header (`w:trPr/w:tblHeader`) gives the expected table.
>
> As far as I can see, #2160 covers the escaping part of this issue but not the table header. Would you accept a PR that, for DOCX tables without a header row, uses the first row as the Markdown header (as most readers expect)? I can add tests for both cases (with and without `w:tblHeader`).

## 4. Script de reprodução (os 2 achados)

```python
"""Reproduz os 2 achados contra o MarkItDown instalado. Uso: python -I repro.py <pasta-vazia>"""
import sys
from pathlib import Path

import docx
from markitdown import MarkItDown

out = Path(sys.argv[1])
md = MarkItDown(enable_plugins=False)

p = out / "not-really.pdf"  # B: extensão .pdf, bytes de texto
p.write_bytes(b"this is plain text, not a PDF")
print(repr(md.convert_local(p).markdown[:80]))  # 'this is plain text, not a PDF'

d = docx.Document()  # A: tabela sem w:tblHeader
t = d.add_table(rows=3, cols=2)
for i, row in enumerate([("Name", "Qty"), ("apple", "3"), ("pear", "5")]):
    for j, v in enumerate(row):
        t.cell(i, j).text = v
q = out / "table-no-header.docx"
d.save(q)
print(md.convert_local(q).markdown)  # |  |  | ... | Name | Qty | ...
```

As fixtures sintéticas da plataforma (`runner/tests/fixtures/ingest/docx/generate_simple_synthetic.py`) marcam o cabeçalho com `w:tblHeader`, e o docstring do gerador explica porquê.

## 5. Depois de publicar

- Registar o link do comentário no ING-012 (`docs/initiatives/PENDENCIAS.md`).
- O ING-012 fecha quando o comentário estiver publicado. Se os maintainers aceitarem o PR do cabeçalho, abre-se um item novo para ele (fork na conta do DEV, CLA da Microsoft, testes com e sem `w:tblHeader`).
- Ao subir o pin do MarkItDown (`runner/requirements-ingest.txt`), correr de novo o teste `test_docx_simple_synthetic_*`. Se a correcção entrar no upstream, a tabela passa a sair bem mesmo sem `w:tblHeader`.
