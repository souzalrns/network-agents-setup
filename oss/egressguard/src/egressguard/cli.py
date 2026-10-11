"""egressguard CLI: safely GET a URL, print its provenance, exit 0/non-zero.

    egressguard get <url> --allow DOMAIN [--allow DOMAIN ...] [--max-bytes N]
                         [--timeout-s S] [--content-type PREFIX ...] [--body] [--json]

Deny-by-default: at least one ``--allow`` is required. On a ``FetchError`` the code
goes to stderr and the exit code is 1. ``--body`` writes the decoded text to stdout;
``--json`` prints the provenance as JSON (never the raw bytes).
"""

from __future__ import annotations

import argparse
import json
import sys

from . import DEFAULT_MAX_BYTES, DEFAULT_TIMEOUT_S, FetchError, __version__, fetch


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="egressguard", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"egressguard {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("get", help="Safely GET a URL from an allowlisted domain")
    g.add_argument("url")
    g.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="DOMAIN",
        help="Allowed domain (repeatable; a domain also covers its subdomains)",
    )
    g.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    g.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    g.add_argument(
        "--content-type",
        action="append",
        default=None,
        metavar="PREFIX",
        help="Restrict to content-type prefixes (repeatable); default: any",
    )
    g.add_argument("--body", action="store_true", help="Write the decoded text to stdout")
    g.add_argument("--json", action="store_true", help="Print provenance as JSON")
    args = ap.parse_args(argv)

    if not args.allow:
        print("error: at least one --allow <domain> is required (deny-by-default)", file=sys.stderr)
        return 2
    try:
        got = fetch(
            args.url,
            allowlist=args.allow,
            timeout_s=args.timeout_s,
            max_bytes=args.max_bytes,
            content_types=args.content_type,
        )
    except FetchError as exc:
        print(f"{exc.code}: {exc.detail}", file=sys.stderr)
        return 1

    meta = {
        "url": got.url,
        "final_url": got.final_url,
        "status": got.status,
        "content_type": got.content_type,
        "bytes": len(got.content),
        "content_hash": got.content_hash,
        "warnings": got.warnings,
    }
    if args.json:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        for k, v in meta.items():
            print(f"{k}: {v}")
    if args.body:
        sys.stdout.write(got.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
