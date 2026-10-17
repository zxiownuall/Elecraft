# Task 2 evidence — independent Elecraft identity

## Scope and implementation

- Kept workspace package/crate IDs `cadcraft*`; declared explicit `elecraft` and `elecraft-cli` executable targets. Desktop title, About/help, native menu, CLI help/version, MCP identity/resources, runtime diagnostics, PDF producer, default plotter labels, font display name, and 12 localization catalogs now use Elecraft. Removed upstream community/about links and catalog marketing strings. Some legacy protocol/env identifiers remain intentionally stable outside the new settings override (see concerns).
- Windows resources now use `assets/app-icon/elecraft.ico`, product/file description and executable metadata Elecraft. `packaging/windows/package.ps1`, `cadcraft.wxs`, and `sign.ps1` stage/sign/package Elecraft executables and names; MSI UpgradeCode and fixed component GUIDs differ from upstream. Internal WiX identifiers and Rust crate IDs remain unchanged. No installer was executed.
- Config and workspace stores use `ELECRAFT_CONFIG_DIR`, `%APPDATA%\Elecraft` (plus new macOS/XDG directories); old settings are neither read nor migrated automatically. Log filename and rotated logs use `elecraft`.
- `scripts/make_elecraft_icon.py` generates its geometric E PNG and single-image ICO solely from Python stdlib `struct`/`zlib`; no raster input or upstream asset is loaded. `ATTRIBUTION.md` lists only present generated icon files and retains upstream contributors for source-generated resources/translations; `NOTICE` remains unchanged. Portable package includes NOTICE and ATTRIBUTION.md.
- `scripts/audit_brand.py` scans desktop/CLI, crate runtime sources and Windows packaging plus README, including TSVs, for upstream product names, URLs, icon paths, config override and executable/resource identities. Excluded legal attribution is confined to `NOTICE`, `ATTRIBUTION.md`, `LICENSE-*`, `docs/provenance/`; build.rs `LegalCopyright` is retained as legal metadata, not a product field. Internal Rust crate identifiers are not forbidden. Source comments and test modules are non-distributable; web target is outside the Windows distributable audit scope.

## TDD evidence

RED, before production edits:

```text
$ python3 -m unittest discover -s tests -p 'test_brand.py' -v
Ran 5 tests in 0.004s
FAILED (failures=2, errors=3)
```

Expected failure details: desktop manifest `default-run = "cadcraft"` instead of `elecraft`; build.rs still used `cadcraft.ico` and upstream Windows identity. Icon and audit module did not yet exist (`FileNotFoundError`). The missing-module errors were expected pre-implementation, not counted as proof of an assertion failure. After writing the audit/icon and expanding tests for MCP/exporter/font identity, the targeted RED run was `Ran 6 tests ... FAILED (failures=2)`: the backend/exporter contract and repository audit still failed against old runtime values. A subsequent focused RED for MCP URI likewise failed only `test_backend_and_exporters_show_current_identity` after the previous cases had gone green.

GREEN, after changes:

```text
$ python3 -m unittest discover -s tests -p 'test_brand.py' -v
Ran 7 tests in 0.454s
OK
$ python3 -m unittest discover -s tests -v
Ran 16 tests in 0.435s
OK
$ python3 scripts/audit_brand.py
brand audit: 0 violation(s)
$ git diff --check
(exit 0, no output)
$ python3 -m py_compile scripts/audit_brand.py scripts/make_elecraft_icon.py tests/test_brand.py
(exit 0, no output)
```

The PNG test decodes and validates signature, IHDR 256×256 RGB, CRCs, zlib pixel rows, background/foreground values and generator byte-for-byte reproducibility; ICO directory and embedded PNG are checked. Tests parse both Cargo manifests with `tomllib`, parse WiX XML with `ElementTree`, verify desktop/CLI source identity, and verify all 12 TSVs preserve unique three-field records and localized About keys. The audit fixture proves it reports legacy icon/title, WiX and translated title while exempting legal attribution and crate IDs.

## Self-review and limitations

- Inspected native desktop, CLI, WiX, PowerShell, localization and downstream crate strings rather than changing crate IDs. Found and fixed secondary settings path in plotters, MCP launch label/server URI, macOS native menu, sign-tool description, and obsolete localized marketing. MSI upgrade GUID isolation prevents an Elecraft installer from upgrading an upstream install. Source-level XML/TOML syntax was checked by tests, not by WiX/Cargo.
- The upstream `CADCraft Stroke` visible font name is now `Elecraft Stroke` while original authorship remains credited. Compatibility of drawings/settings referring to the former font name and built-in plotter labels needs a real application regression check; no migration was implemented.
- `CADCRAFT_CONTROL_PORT`, `CADCRAFT_LOCALE`, `CADCRAFT_BUILD_SHA`, and related non-config environment keys remain in source for compatibility. Other non-Windows targets, notably `apps/cadcraft-web`, are outside Task 2 Windows package scope and still need a separate product-identity pass before any web release.
- No Rust compile, Rust unit/integration test, PowerShell execution, WiX build, executable resource inspection or live GUI validation was performed here. This host reports `Linux`; `cargo`, `rustc`, `pwsh`, `wix` are unavailable. The following checks are **blocked/not passed**, to run on Windows with MSVC and WiX v5 available:
  1. `cargo test --locked -p cadcraft --bin elecraft`
  2. `cargo test --locked -p cadcraft-cli --bin elecraft-cli`
  3. Rust tests for `cadcraft-ui-egui`, `cadcraft-engine`, `cadcraft-mcp`, `cadcraft-io`, `cadcraft-fonts`, and the modified integration tests (actual package names/toolchain resolution must be checked in Cargo before invocation).
  4. `cargo build --release --locked -p cadcraft -p cadcraft-cli --target x86_64-pc-windows-msvc` with resource embedding required; inspect produced PE names, GUI/console subsystem, VERSIONINFO fields, icon and `elecraft-cli.exe --version` / help.
  5. Build WiX via `packaging/windows/package.ps1` in a controlled non-production Windows environment; inspect MSI product/upgrade metadata, file associations, portable zip and legal notices **without installing the MSI**. Signing requires separately reviewed credentials.
  6. Run `elecraft.exe` in a disposable Windows user profile, inspect window/About title, icon and log/config isolation at `%APPDATA%\Elecraft`, and ensure old settings remain untouched.

Task 2 source work is committed, but a Windows build/UI check is required before claiming a complete rebrand or release readiness.

## Review fix: CLI integration binary and MSI legal payload

- Changed only the `CARGO_BIN_EXE_*` references in four CLI integration test files (five invocations) to the declared `elecraft-cli` binary. Existing test comments and executable error messages were not rebranded.
- Inspected `cadcraft.wxs`, `package.ps1`, the CLI manifest, and checked-in package inputs. `NOTICE`, `ATTRIBUTION.md`, `LICENSE-MIT`, `LICENSE-APACHE`, and `README.md` exist; plain `LICENSE` does not. The MSI now installs the five present files in `INSTALLFOLDER`, each with a file key path. The portable zip copies those same staged files. When `CRAFT_FONTS_DIR` supplies `OFL.txt` files, staging happens before WiX and a conditional WiX v5 `Files` harvest includes them in the MSI and portable zip.

Regression evidence (new assertions added before implementation):

```text
RED $ python3 -m unittest discover -s tests -p 'test_brand.py' -v
Ran 9 tests in 0.703s
FAILED (failures=5)
  test_cli_integration_tests_resolve_declared_binary: 4 failing subtests;
  expected CARGO_BIN_EXE_elecraft-cli, found CARGO_BIN_EXE_cadcraft-cli.
  test_msi_and_portable_include_legal_documents: missing
  README.md, NOTICE, ATTRIBUTION.md, LICENSE-MIT, LICENSE-APACHE in WiX File sources.

RED (optional OFL assertion added before that change)
$ python3 -m unittest discover -s tests -p 'test_brand.py' -k test_msi_and_portable_include_legal_documents -v
Ran 1 test in 0.002s
FAILED (failures=1): OFL notices not copied into MSI stage.

GREEN $ python3 -m unittest discover -s tests -p 'test_brand.py' -v
Ran 9 tests in 0.398s
OK
$ python3 -m unittest discover -s tests -v
Ran 18 tests in 0.268s
OK
$ python3 scripts/audit_brand.py
brand audit: 0 violation(s)
$ python3 -m py_compile tests/test_brand.py && git diff --check
(exit 0, no output)
```

This is source-level XML/package-input coverage, not a WiX build or actual archive inspection. `cargo`, `rustc`, `pwsh`, and `wix` are not installed here, so Rust integration compilation and a Windows packaging build remain unverified. No installer was executed. Font naming/audit policy remains outside this fix.
