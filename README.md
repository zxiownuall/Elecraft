# Elecraft

Elecraft is an independent, open-source computer-aided design application,
forked from MIT OR Apache-2.0 open-source work. It is not affiliated with
CADMATIC or the original project's trademarks. Original authors and asset
contributors remain credited in [NOTICE](NOTICE) and
[ATTRIBUTION.md](ATTRIBUTION.md); see [provenance](docs/provenance/) for the
source snapshot. No CADMATIC proprietary assets or upstream app icons ship here.

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
