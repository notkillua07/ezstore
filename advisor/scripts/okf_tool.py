"""Build and check the EZStore OKF (Open Knowledge Format v0.2) bundle.

Usage (from the repo root, backend running on localhost:8080):

    python advisor/scripts/okf_tool.py products   # regenerate products/*.md from the backend API
    python advisor/scripts/okf_tool.py index      # regenerate every index.md
    python advisor/scripts/okf_tool.py validate   # OKF conformance check (spec section 11)
    python advisor/scripts/okf_tool.py all        # products + index + validate

Spec: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from decimal import Decimal
from pathlib import Path

import yaml

BUNDLE = Path(__file__).resolve().parent.parent / "knowledge" / "ezstore"
PRODUCER = "ezstore-okf-builder/0.1"
OKF_VERSION = "0.2"
RESERVED = {"index.md", "log.md"}

CATEGORIES = {
    "EQ": ("Office equipment", "辦公設備"),
    "NT": ("Networking", "網路設備"),
    "SP": ("Office supplies", "辦公耗材"),
    "SW": ("Software and services", "軟體與服務"),
}
LEVEL_FACTORS = [("vip", Decimal("0.80")), ("standard", Decimal("0.90")), ("new", Decimal("1.00"))]
SECTION_TITLES = {"policies": "Policies and business rules", "guides": "Guides", "products": "Products"}

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.S)
_LINK = re.compile(r"\]\(([^)\s#:]+\.md)(?:#[^)]*)?\)")


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_concept(path: Path) -> tuple[dict, str]:
    match = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("missing YAML frontmatter")
    meta = yaml.safe_load(match.group(1)) or {}
    if not isinstance(meta, dict):
        raise ValueError("frontmatter is not a mapping")
    return meta, match.group(2)


def write_concept(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    head = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, width=1000)
    path.write_text(f"---\n{head}---\n\n{body.strip()}\n", encoding="utf-8")


def fetch_products(api: str) -> list[dict]:
    with urllib.request.urlopen(f"{api}/products?page_size=100", timeout=10) as resp:
        return json.load(resp)["data"]


def product_body(p: dict) -> str:
    price = Decimal(str(p["list_price"]))
    rows = "\n".join(
        f"| `{level}` | {factor} | {(price * factor).normalize():f} |" for level, factor in LEVEL_FACTORS
    )
    english, chinese = CATEGORIES.get(p["product_number"][:2], ("Other", "其他"))
    return f"""# Details

| Field | Value |
|-------|-------|
| Product number | {p["product_number"]} |
| Name | {p["name"]} |
| Category | {english} ({chinese}) |
| Supplier | {p["supplier"]} |
| List price (TWD) | {price.normalize():f} |
| Description | {p.get("description") or "-"} |

# Unit price by customer level

With the default pricing factor of each [customer level](../policies/customer-levels.md)
(`unit_price = list_price × factor`, see [pricing computation](../policies/pricing-computation.md)):

| Level | Factor | Unit price (TWD) |
|-------|--------|------------------|
{rows}

A quotation can use a different factor; the quotation itself is the source of truth for the final price.
"""


def build_products(api: str) -> int:
    products = fetch_products(api)
    out = BUNDLE / "products"
    for old in out.glob("*.md"):
        if old.name not in RESERVED:
            old.unlink()
    stamp = now_utc()
    stale = (dt.datetime.now(dt.UTC) + dt.timedelta(days=30)).replace(microsecond=0)
    for p in products:
        english, _ = CATEGORIES.get(p["product_number"][:2], ("Other", "其他"))
        meta = {
            "type": "Product",
            "title": f'{p["name"]} ({p["product_number"]})',
            "description": f'{english}; list price {Decimal(str(p["list_price"])).normalize():f} TWD; supplier {p["supplier"]}.',
            "resource": f'{api}/products/{p["id"]}',
            "tags": ["product", english.lower().replace(" ", "-")],
            "status": "stable",
            "generated": {"by": PRODUCER, "at": stamp},
            "stale_after": stale.isoformat().replace("+00:00", "Z"),
            "sources": [
                {
                    "id": "backend-api",
                    "resource": f'{api}/products/{p["id"]}',
                    "title": "EZStore backend REST API",
                    "last_modified": p["updated_at"],
                }
            ],
        }
        write_concept(out / f'{p["product_number"]}.md', meta, product_body(p))
    return len(products)


def concepts(bundle: Path) -> list[Path]:
    return sorted(p for p in bundle.rglob("*.md") if p.name not in RESERVED)


def entry(path: Path, base_dir: Path) -> str:
    """Index entry with a link relative to the index file's folder (works in editors and on GitHub)."""
    meta, _ = read_concept(path)
    link = Path(os.path.relpath(path, base_dir)).as_posix()
    title = meta.get("title") or path.stem
    desc = meta.get("description")
    return f"- [{title}]({link})" + (f" — {desc}" if desc else "")


def build_indexes(bundle: Path = BUNDLE) -> None:
    sections = sorted(d for d in bundle.iterdir() if d.is_dir())
    for section in sections:
        name = SECTION_TITLES.get(section.name, section.name.title())
        lines = [f"# {name}", ""] + [entry(p, section) for p in concepts(section)]
        (section / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    root = [
        "---",
        f'okf_version: "{OKF_VERSION}"',
        "---",
        "",
        "# EZStore knowledge bundle",
        "",
        "Business rules, product catalog and agent capabilities of the EZStore quotation system,",
        "used by the EZStore Sales Advisor agent. Format: Open Knowledge Format (OKF) v0.2.",
    ]
    for section in sections:
        root += ["", f"## {SECTION_TITLES.get(section.name, section.name.title())}", ""]
        root += [entry(p, bundle) for p in concepts(section)]
    (bundle / "index.md").write_text("\n".join(root) + "\n", encoding="utf-8")


def validate(bundle: Path = BUNDLE) -> list[str]:
    """Return errors per OKF v0.2 section 11; broken links are printed as warnings only (6.1)."""
    errors: list[str] = []
    for path in concepts(bundle):
        rel = path.relative_to(bundle).as_posix()
        try:
            meta, body = read_concept(path)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{rel}: {e}")
            continue
        if not str(meta.get("type") or "").strip():
            errors.append(f"{rel}: frontmatter has no non-empty 'type'")
        if meta.get("status") not in (None, "draft", "stable", "deprecated"):
            errors.append(f"{rel}: invalid status {meta.get('status')!r}")
        for target in _LINK.findall(body):
            resolved = bundle / target.lstrip("/") if target.startswith("/") else path.parent / target
            if not resolved.exists():
                print(f"warning: {rel} links to missing {target}")
    for index in bundle.rglob("index.md"):
        text = index.read_text(encoding="utf-8")
        if text.startswith("---") and index.parent != bundle:
            errors.append(f"{index.relative_to(bundle).as_posix()}: only the root index.md may have frontmatter")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["products", "index", "validate", "all"])
    parser.add_argument("--api", default="http://localhost:8080/api/v1", help="EZStore backend API base URL")
    args = parser.parse_args()

    if args.command in ("products", "all"):
        print(f"products: wrote {build_products(args.api)} concepts")
    if args.command in ("index", "all"):
        build_indexes()
        print("index: regenerated index.md files")
    if args.command in ("validate", "all"):
        errors = validate()
        for err in errors:
            print("error:", err)
        print(f"validate: {len(concepts(BUNDLE))} concepts, {len(errors)} errors")
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())