# Elecraft

Elecraft is an independent, Windows-first, open-source 2D CAD editor based on
attributed open-source code. The public project home is
[github.com/zxiownuall/Elecraft](https://github.com/zxiownuall/Elecraft).
It is not affiliated with CADMATIC or the original project's trademarks.
Original authors and asset contributors remain credited in [NOTICE](NOTICE)
and [ATTRIBUTION.md](ATTRIBUTION.md); see the [source manifest](docs/provenance/cadcraft-snapshot.json)
and [upstream refresh audit](docs/elecraft/upstream-audit-2026-10-18.md).
No CADMATIC proprietary assets or upstream app icons ship here.

The Rust package names remain `cadcraft` and `cadcraft-cli` for workspace
compatibility; their application binary targets are `elecraft` and
`elecraft-cli`. On Windows, the per-user configuration directory is
`%APPDATA%\Elecraft` (or `ELECRAFT_CONFIG_DIR` when set). Legacy upstream
configuration is not auto-migrated or written. The icon can be regenerated
reproducibly with `python3 scripts/make_elecraft_icon.py` using only the Python
standard library.

The Windows packaging input is `packaging/windows/package.ps1` (WiX v5 and
MSVC build tools required). Do not run an installer without a separate review
of its generated MSI and file associations. The source-level brand check is
`python3 scripts/audit_brand.py` and its tests are in `tests/test_brand.py`.

## What has been done

- Forked the attributed Rust source into an independent Elecraft project,
  with its own executable names, Windows application metadata, configuration
  path, translated About labels, and a reproducible original dark-blue `E`
  icon. Upstream authorship credits and compatible internal crate names
  remain intact.
- Established a synthetic Windows build, command-line and desktop baseline;
  its [validation record](docs/elecraft/windows-baseline-validation.md) is not
  evidence that real third-party DXFs can be saved without loss.
- Reviewed the DXF reliability [design](docs/superpowers/specs/2026-10-18-elecraft-dxf-reliability-design.md):
  ordinary saves must reject unpreserved source content, verify a reopened
  candidate, detect conflicts, and retain recoverable prior versions. These
  safeguards are **design requirements, not yet implemented guarantees**.
- Integrated the scoped source delta from public upstream `main` at
  `b23d362f6af1dd77e319728f1d85882b098626fe` (v0.9.0), retaining
  Elecraft branding and the pinned MIT/Apache-2.0 `craft-docpath` dependency.
  Version `0.9.0-elecraft.1` identifies this fork rather than an upstream
  release. Refused stored xref paths do not authorize a different same-named
  xref; allowed but missing xref paths may still use a same-folder
  filename fallback. A user-selected cross-share xref can become unresolved
  on reopen because the saved path is treated as untrusted. Stored path checks
  are lexical; they do not prove symlink/junction safety or the DXF publication
  contract.

## What remains open

Real licensed DXF compatibility, native Windows/UNC conflict and recovery
failure tests, and an unfiltered interactive Windows validation have **not**
passed. PostgreSQL registry and proprietary native-project import are later,
separately gated milestones. Do not use Elecraft to overwrite irreplaceable
DXF files or treat a successful export as proof of lossless preservation.
