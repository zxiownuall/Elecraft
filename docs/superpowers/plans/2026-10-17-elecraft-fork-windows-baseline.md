# Elecraft Fork and Windows Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a separately branded, attributed Elecraft Rust fork that builds and launches on Windows, opens a synthetic DXF, and does not alter CADCraft/CADMATIC sources or user projects.

**Architecture:** Retain CADCraft's internal crate names and layered engine/UI initially; change the externally visible desktop/CLI executable names, application identity, settings/log directories, Windows resources and icon. Import only an allowlisted source snapshot with a hash manifest. This plan covers the independent fork and Windows baseline only; DXF-preservation hardening, PostgreSQL registry, and native `.drw`/`.mdb` feasibility each require their own separately reviewed plan and gate.

**Tech Stack:** Rust 2024, Cargo, eframe/egui, existing CADCraft workspace, Windows x64 Rust toolchain, Python 3 stdlib for one-time source import and original icon generation.

## Global Constraints

- Canonical project: `/opt/data/agent/elecraft` (`Z:\Agent\elecraft`); source snapshot: `/opt/data/agent/cadmatic/cadcraft-main`; the source has no Git metadata. Do not claim an upstream commit ID.
- Installed CADMATIC and `UserData` are read-only behavior/config references. No binary decompilation, no proprietary assets, fonts, symbols, menus, database contents, license files or help text in Elecraft.
- CADCraft code is MIT OR Apache-2.0; retain its LICENSE files, NOTICE and contributor attribution. Its ArtCraft marks are *not* covered; remove them from Elecraft binaries and distributable assets. Refer to CADCraft authors in plain-text attribution without suggesting endorsement.
- Windows-first; build and run on an actual Windows PC before declaring a working desktop artifact. This Linux session has no `cargo`/`rustc`; toolchain availability on Windows is unverified. Do not substitute an unrun command for a successful build.
- Keep the root Git repository and existing approved spec. Work in an isolated worktree for implementation if practical; never copy a worktree's `.git` into the source snapshot. Make small commits after each passing task.
- Follow `rust-skills`, test-driven-development, verification-before-completion, and Windows packaging/testing skills when executing; this plan does not assert that those tools or tests have run.
- No production PostgreSQL, remote host configuration, project mutation, or distribution/installer execution in this plan. A portable local build and temporary synthetic DXF are sufficient.

## File map and interfaces

- `scripts/import_cadcraft_snapshot.py`: one-way, allowlisted copy plus SHA-256 manifest; accepts `--source` and `--dest`, refuses existing destination source directories. `docs/provenance/cadcraft-snapshot.json` records each copied file hash and the source root/URL, but no fake revision.
- `scripts/make_elecraft_icon.py`: deterministic original PNG/ICO generator; outputs `assets/app-icon/elecraft-256.png` and `assets/app-icon/elecraft.ico`. Design a simple original geometric E mark, not a traced CADCraft/CADMATIC logo.
- `apps/cadcraft/Cargo.toml`, `apps/cadcraft-cli/Cargo.toml`: leave package/internal dependency names intact; add `[[bin]]` names `elecraft` and `elecraft-cli` and adjust default-run. `apps/cadcraft/build.rs`, `src/main.rs`, `src/workspace.rs`, `src/logging.rs`: Windows resources, visible identity and isolated settings/log paths.
- `crates/ui-egui/src/credits.rs`, `crates/ui-egui/src/menus.rs`, related About/help code: inspect and replace visible ArtCraft/CADCraft product identity and outbound links without touching attribution/licensing. `docs/control-protocol.md` is copied because tests use `include_str!`; update its executable examples.
- `ATTRIBUTION.md`, `NOTICE`, `LICENSE-MIT`, `LICENSE-APACHE`: retain legal provenance; add rows for original Elecraft icon. `README.md`: new Elecraft usage and upstream attribution. `scripts/audit_brand.py`: fail if distributable binary/resource inputs still contain prohibited ArtCraft marks or if build references the old app icon.
- `docs/elecraft/windows-baseline-validation.md`: record Windows toolchain version, command results, executable location, smoke steps and limitations. Runtime logs/settings must not write to `%APPDATA%\CADCraft`.

---

### Task 1: Import a reproducible, legally separated source snapshot

**Files:** Create `scripts/import_cadcraft_snapshot.py`, `docs/provenance/cadcraft-snapshot.json`, `tests/test_import_snapshot.py`; import `crates/`, `apps/`, `xtask/`, `packaging/windows/`, `.cargo/`, `Cargo.toml`, `Cargo.lock`, `.gitignore`, `rustfmt.toml`, `clippy.toml`, `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE`, `ATTRIBUTION.md`, `docs/control-protocol.md`. Do not import `docs/brand/`, original `assets/app-icon/`, screenshots, `UserData/`, or any CADMATIC tree.

**Interfaces:** Consumes: source root and empty target source paths. Produces: `import_snapshot(source: Path, dest: Path) -> dict` with sorted relative path → SHA-256 pairs; all copied source files match manifest hashes. Subsequent tasks consume the imported workspace and manifest.

- [ ] **Step 1: Write failing import-policy tests.** In `tests/test_import_snapshot.py`, use stdlib `unittest` and a `TemporaryDirectory` source with `Cargo.toml`, `crates/geom/src/lib.rs`, `docs/brand/mark.svg`, `assets/app-icon/cadcraft.ico`, `LICENSE-MIT`, and `.git/config`. Test that `import_snapshot` copies allowlisted items, skips three disallowed paths, records exact SHA-256, and refuses a second import if `crates/` exists. Example assertion: `self.assertNotIn('docs/brand/mark.svg', manifest['files'])`.
- [ ] **Step 2: Verify red.** Run `python3 -m unittest discover -s tests -p 'test_import_snapshot.py' -v`. Expected: import error for missing `scripts.import_cadcraft_snapshot`.
- [ ] **Step 3: Implement minimal importer.** Use the following algorithm in `scripts/import_cadcraft_snapshot.py` (add argparse `--source` and `--dest`, `if __name__ == '__main__'`):

```python
from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

DIRS = ('crates', 'apps', 'xtask', '.cargo', 'packaging/windows')
FILES = ('Cargo.toml', 'Cargo.lock', '.gitignore', 'rustfmt.toml',
         'clippy.toml', 'LICENSE-MIT', 'LICENSE-APACHE', 'NOTICE',
         'ATTRIBUTION.md', 'docs/control-protocol.md')

def import_snapshot(source: Path, dest: Path) -> dict:
    source, dest = source.resolve(), dest.resolve()
    if not source.is_dir() or source == dest or source in dest.parents or dest in source.parents:
        raise ValueError('source and destination must be distinct directories')
    selected = []
    for name in DIRS:
        root = source / name
        if not root.is_dir() or (dest / name).exists():
            raise FileExistsError(name)
        selected.extend(p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts)
    for name in FILES:
        p = source / name
        if not p.is_file() or (dest / name).exists():
            raise FileExistsError(name)
        selected.append(p)
    for p in selected:  # preflight before writing any destination file
        rel = p.relative_to(source)
        parts = [source.joinpath(*rel.parts[:i]) for i in range(1, len(rel.parts) + 1)]
        if any(x.is_symlink() for x in parts):
            raise ValueError(f'symlink in source: {rel}')
    files = {}
    for p in sorted(selected):
        rel = p.relative_to(source)
        data = p.read_bytes()
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        files[rel.as_posix()] = hashlib.sha256(data).hexdigest()
    manifest = {'source': str(source), 'url': 'https://github.com/storytold/cadcraft',
                'captured_utc': datetime.now(timezone.utc).isoformat(), 'files': files}
    out = dest / 'docs/provenance/cadcraft-snapshot.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')
    return manifest
```

Before running on the real tree, inspect the allowlist and preflight result; expand it only for an evidenced missing include/build dependency, recording each expansion in the manifest and tests.
- [ ] **Step 4: Verify green and provenance.** Rerun the unittest; run importer with `--source '/opt/data/agent/cadmatic/cadcraft-main' --dest '/opt/data/agent/elecraft'`. Run a manifest verification script over every imported path (read bytes; compare SHA-256; assert no manifest path starts `docs/brand/` or `assets/app-icon/`). Assert `.git` still belongs solely to Elecraft. Do not print contents of imported test fixtures.
- [ ] **Step 5: Commit.** `git add scripts tests docs/provenance crates apps xtask packaging/windows .cargo Cargo.toml Cargo.lock .gitignore rustfmt.toml clippy.toml LICENSE-MIT LICENSE-APACHE NOTICE ATTRIBUTION.md docs/control-protocol.md && git commit -m 'chore: import attributed CADCraft source snapshot'`. If the copied sources contain unclear licensed fixtures or marks, stop before commit and trim the allowlist with a recorded reason.

### Task 2: Distinct Elecraft identity and original asset

**Files:** Create `scripts/make_elecraft_icon.py`, `scripts/audit_brand.py`, `assets/app-icon/elecraft-256.png`, `assets/app-icon/elecraft.ico`, `tests/test_brand.py`, `README.md`; modify `apps/cadcraft/{Cargo.toml,build.rs,src/main.rs,src/workspace.rs,src/logging.rs}`, `apps/cadcraft-cli/{Cargo.toml,src/main.rs}`, `crates/ui-egui/src/{credits.rs,menus.rs}`, `ATTRIBUTION.md`, and additional About/help files found in the audit.

**Interfaces:** Consumes imported workspace; produces `elecraft` and `elecraft-cli` executable targets. Produces `audit_brand(root: Path) -> list[str]`, where an empty list means no prohibited visible product identity or asset dependency in distributable inputs; legal attribution files are exempt. Preserve internal `cadcraft-*` Rust crate IDs to avoid unnecessary workspace-wide rename.

- [ ] **Step 1: Write red tests.** Assert `apps/cadcraft/Cargo.toml` declares a `[[bin]] name = "elecraft"`, `apps/cadcraft-cli/Cargo.toml` declares `elecraft-cli`, Windows config paths end in `Elecraft`, and `audit_brand(root)` finds old app icon includes or product title. Assert generated icon is a decodable square 256×256 PNG and ICO embeds an original generated image. Test that upstream author attribution remains in `NOTICE`.
- [ ] **Step 2: Run `python3 -m unittest discover -s tests -p 'test_brand.py' -v`**; expect the target names and icon assertions to fail.
- [ ] **Step 3: Generate an original mark and change binary/resource metadata.** Use Python stdlib `zlib`, `struct`, `binascii` to render a 256×256 solid dark-blue square with an original high-contrast geometric E made of rectangles, then write PNG chunks (`IHDR`, `IDAT`, `IEND`) and a single-image ICO containing that PNG. The ICO header is `struct.pack('<HHH', 0, 1, 1)` plus `struct.pack('<BBBBHHII', 0, 0, 0, 0, 1, 32, len(png), 22)`. Do not derive pixels from CADCraft or CADMATIC assets. In `Cargo.toml` set `default-run = "elecraft"` and `[[bin]] name = "elecraft"; path = "src/main.rs"` (similarly for CLI). In `build.rs`, point `set_icon` and `rerun-if-changed` at `../../assets/app-icon/elecraft.ico`; set `ProductName`, `FileDescription`, `OriginalFilename`, `InternalName` to Elecraft values while retaining contributor copyright without claiming Elecraft authorship of upstream code. In `main.rs`, point `include_bytes!` at the generated Elecraft PNG; use `Elecraft` for window title and `elecraft` for version string.
- [ ] **Step 4: Isolate settings and visible UI.** Change `config_dir_from`/`workspace.rs` to `%APPDATA%\\Elecraft` on Windows and `ELECRAFT_CONFIG_DIR` override; preserve legacy CADCraft settings read-only (do not auto-migrate them). Update their existing unit tests to assert Elecraft paths. Update `logging.rs` to `elecraft.log`. In `apps/cadcraft-cli/src/main.rs:665-667`, replace `outln!("cadcraft-cli {}", env!("CARGO_PKG_VERSION"));` with `outln!("elecraft-cli {}", env!("CARGO_PKG_VERSION"));`, and update its usage/help prefix to `elecraft-cli`. Search UI and Windows build inputs for `ArtCraft`, `getartcraft.com`, `discord.gg/artcraft`, `ai.storyteller.cadcraft`, original app icon paths, and obsolete title; replace only user-visible identity, not license notices or internal crate names. Add an audit with a documented allowlist restricted to legal attribution (`LICENSE-*`, `NOTICE`, `ATTRIBUTION.md`, `docs/provenance/`) and assert zero matches in runtime/packaging paths. Replace About/help links with Elecraft-local documentation or remove them until an Elecraft destination exists.
- [ ] **Step 5: Verify and commit.** Run brand unittests, `python3 scripts/audit_brand.py`, `git diff --check`; on Windows, `cargo test --locked -p cadcraft --bin elecraft` and `cargo test --locked -p cadcraft-cli --bin elecraft-cli`. Do not claim complete rebrand until a built exe and UI title are inspected. Stage the changed Task 2 files with `git add apps/cadcraft apps/cadcraft-cli crates/ui-egui/src/credits.rs crates/ui-egui/src/menus.rs assets/app-icon scripts/make_elecraft_icon.py scripts/audit_brand.py tests/test_brand.py README.md ATTRIBUTION.md`; inspect `git diff --cached --stat` for any additional About/help file, stage that exact path, then `git commit -m 'feat: establish independent Elecraft application identity'`.

### Task 3: Windows build and exercised baseline

**Files:** Create `docs/elecraft/windows-baseline-validation.md` and `scripts/windows/verify-baseline.ps1`; update Task 2's files only if a build/test finds a defect. No installer/MSI or code-signing work in this phase.

**Interfaces:** Consumes `elecraft.exe`, `elecraft-cli.exe`, synthetic DXF generated by Elecraft CLI or directly written from a minimal documented DXF sample. Produces a command log and paths to verified Windows executables and generated drawing. No claims of real-file DXF fidelity.

- [ ] **Step 1: Check prerequisites on a Windows PC.** From PowerShell, run `rustc --version`, `cargo --version`, `git --version` and record actual output and exit codes. Install any missing toolchain by an approved/user-accessible method; do not mark the task passing if it is unavailable. Copy the fork from `Z:\Agent\elecraft` to `%USERPROFILE%\Documents\elecraft` before building so Windows build artifacts are local. Do not copy target/ or `.git` if using a snapshot workflow; if using Git worktrees, preserve the worktree's metadata and confirm it points to the intended branch.
- [ ] **Step 2: Write smoke script that fails until binaries work.** In `scripts/windows/verify-baseline.ps1`, write the executable core below. Run from the *local* Documents copy; keep output/exit codes in the validation record. The source CLI documents both `run --sample --save` and `info` (`apps/cadcraft-cli/src/main.rs:6,61,65,296-344`).

```powershell
$ErrorActionPreference = 'Stop'
function Invoke-Checked([string]$label, [scriptblock]$body) {
    & $body
    if ($LASTEXITCODE -ne 0) { throw "$label failed with exit $LASTEXITCODE" }
}
Invoke-Checked 'format' { cargo fmt --all -- --check }
Invoke-Checked 'clippy' { cargo clippy --locked --workspace --all-targets -- -D warnings }
Invoke-Checked 'tests' { cargo test --locked --workspace }
Invoke-Checked 'build' { cargo build --release --locked -p cadcraft -p cadcraft-cli }
$desktop = Join-Path (Get-Location) 'target\release\elecraft.exe'
$cli = Join-Path (Get-Location) 'target\release\elecraft-cli.exe'
if (!(Test-Path $desktop) -or !(Test-Path $cli)) { throw 'Elecraft executables missing' }
$version = & $cli --version
if ($LASTEXITCODE -ne 0 -or $version -notmatch '^elecraft-cli ') { throw "wrong CLI identity: $version" }
$tmp = Join-Path $env:TEMP ('elecraft-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null
$dxf = Join-Path $tmp 'sample.dxf'
Invoke-Checked 'synthetic DXF' { & $cli run --sample --save $dxf }
if (!(Test-Path $dxf) -or (Get-Item $dxf).Length -eq 0) { throw 'DXF missing or empty' }
Invoke-Checked 'read DXF' { & $cli info $dxf }
Write-Output "Windows CLI smoke passed; sample: $dxf"
```

Do not silently ignore a CLI error. Do not delete the sample before its GUI verification.
- [ ] **Step 3: Run script, diagnose failures, and repeat.** Execute `powershell -ExecutionPolicy Bypass -File scripts\windows\verify-baseline.ps1` from the *local* Documents copy; record each output/exit code. Fix only baseline defects in this task; if prerequisite installation, unavailable CI dependencies, or upstream failures block it, report the blocker accurately. Check that the source locations on `Z:` were not changed during local build.
- [ ] **Step 4: Exercise GUI on Windows.** Launch `elecraft.exe --sample`, verify the Elecraft title/icon, pan/zoom, basic command input, close/reopen, and `%APPDATA%\Elecraft` settings/logs; check `%APPDATA%\CADCraft` has not changed from Elecraft's run. Open the script's synthetic DXF in the GUI and inspect a rendered result. Record environment, test artifact paths, outcomes and known limitations in `docs/elecraft/windows-baseline-validation.md`. Use a reachable Windows session rather than inferring GUI operation from a build.
- [ ] **Step 5: Commit verified baseline.** `git diff --check`, run `python3 scripts/audit_brand.py` on the canonical fork, check `git status`, then commit script/docs and any fixes. The gate is green only when a real Windows build, CLI read, and GUI launch all succeeded; otherwise leave task open with evidence.

## Subsequent independently planned phases

- **DXF reliability:** a new spec-aligned plan for semantic open/edit/save/reopen preservation, conflict detection, autosave/recovery audit, permission-cleared real corpus, dependency reporting and Windows failure matrix. Do not treat Task 3's synthetic smoke as this gate.
- **PostgreSQL project registry:** a separate plan for the same schema against local Windows and directly IP-connected remote PostgreSQL, credential/TLS policy, transactional metadata and Windows/UNC paths. Ask before configuring a production service or changing access.
- **Native project feasibility:** a separate read-only research plan for isolated `.drw`/`.mdb` copies of `Z:\Agent\cadmatic\POsiva valoverhoprojekti\POsiva valoverhoprojekti 2`; only proceed to implementation if geometry/relationships are evidenced. Keep originals byte-identical and write edited outputs solely to DXF + PostgreSQL.

## Execution handoff

Use a fresh subagent per task with specification and exact repo paths; review spec compliance and code quality after each task, verify artifacts independently, and keep code in an isolated worktree where feasible. Report blockers before widening scope. Do not call the whole Elecraft design complete when only the Windows baseline passes.
