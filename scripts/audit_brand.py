#!/usr/bin/env python3
"""Audit distributable desktop/CLI/UI and Windows packaging for legacy branding.

The ONLY exempt paths are legal attribution: LICENSE-*, NOTICE, ATTRIBUTION.md,
and docs/provenance/. Internal cadcraft-* crate identifiers are not product names.
Source-code comments are not distributable strings; Windows resource LegalCopyright
is an intentionally retained legal attribution, never a product/marketing field.
"""
from pathlib import Path
import re

PRODUCT = re.compile(
    r"CADCraft|CADCRAFT SAMPLE|ArtCraft|getartcraft\.com|discord\.gg/artcraft|"
    r"ai\.storyteller\.cadcraft|CADCRAFT_CONFIG_DIR|cadcraft://|cadcraft(?:-cli)?\.exe|"
    r"cadcraft(?:-cli)?\s+(?:--version|info|convert|run|commands|mcp|perf|sample)|"
    r"app-icon[/\\]cadcraft|cadcraft-(?:256|macos-512)\.png",
)
SCOPES = ("apps/cadcraft", "apps/cadcraft-cli", "crates", "packaging/windows")
TEXT_SUFFIXES = {".rs", ".toml", ".tsv", ".wxs", ".ps1", ".md"}


def audit_brand(root: Path) -> list[str]:
    """Return source-positioned findings for forbidden distributable identity."""
    paths = [root / "README.md"]
    for scope in SCOPES:
        directory = root / scope
        if directory.exists():
            paths.extend(p for p in directory.rglob('*') if p.is_file() and p.suffix in TEXT_SUFFIXES)
    violations = []
    for path in sorted(paths):
        if not path.is_file():
            continue
        in_tests = False
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if path.suffix == '.rs' and line.strip() == '#[cfg(test)]':
                in_tests = True
            if in_tests:
                continue
            trimmed = line.lstrip()
            if trimmed.startswith(("//", "#", "<!--", "*", "-->")):
                continue
            if path.name == 'build.rs' and '"LegalCopyright"' in line:
                continue
            if PRODUCT.search(line):
                violations.append(f"{path.relative_to(root)}:{number}: {line.strip()[:160]}")
    return violations


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = audit_brand(root)
    for finding in findings:
        print(finding)
    print(f"brand audit: {len(findings)} violation(s)")
    return bool(findings)


if __name__ == '__main__':
    raise SystemExit(main())
