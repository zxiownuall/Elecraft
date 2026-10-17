# Elecraft: Windows CAD editor and project-import design

Status: design approved in conversation; written-spec review pending. 2026-10-17.

## Goal and scope

Build Elecraft as an independent Windows-first Rust fork of the source snapshot at `/opt/data/agent/cadmatic/cadcraft-main` (`Z:\Agent\cadmatic\cadcraft-main`). The first usable release opens, edits, saves, and reopens DXF drawings without silently losing supported or preserved content. Then add a PostgreSQL project/drawing registry. A later, separately gated importer reads the example native CADMATIC project without writing back to it.

The output project lives at `/opt/data/agent/elecraft` (`Z:\Agent\elecraft`). This design does not promise complete CADMATIC or Electrical parity, native `.drw` writing, or live multiuser editing of the same DXF. The installed CADMATIC binary distribution is not source code.

## Sources and provenance

- Fork CADCraft's Rust code as a separately maintained project, recording a manifest of source files, their checksums, snapshot date, and original project URL before modification. The local snapshot has no `.git` history; do not invent upstream commit provenance.
- Keep applicable MIT/Apache-2.0 licenses, notices, and attribution. Remove or replace all ArtCraft marks before any Elecraft distribution: `docs/brand/LICENSE-brand.txt` explicitly disallows using them to brand forks. Use original Elecraft artwork and avoid CADMATIC names/marks in product branding.
- Read `/opt/data/agent/cadmatic/CADMATIC Draw 2026H1 FI` and `/opt/data/agent/cadmatic/UserData/eddi.CORP/AppData/Local/Cadmatic/CADMATIC Draw 2026H1 FI` only as references for observed behavior and the user's actual configuration. Do not copy CADMATIC binaries, menus, fonts, symbols, images, license files, databases, or help text into Elecraft. No binary decompilation.
- The native-import research exception permits read-only analysis of isolated copies of project `.drw` and `.mdb` files for interoperability; originals remain untouched. Never publish a user's project files or imported personal/project data as repository fixtures. Prefer public format specifications and independently constructed test data.

## Architecture

Preserve CADCraft's existing crate boundaries: `geom`/`dxf` parse primitives, `doc` owns the drawing model, `io` maps DXF to/from drawings, `engine` owns commands, and `ui-egui`/desktop app present Windows interaction. Add format-preservation checks close to DXF I/O and save orchestration rather than embedding them in UI handlers. Keep headless CLI/control paths testable. Rebrand application identifiers, names, icons, About and packaging separately from the CAD engine; audit asset/license status of each copied file before shipping.

Project registry is a separate domain component with explicit project, drawing-reference, and database-connection types. It stores project names, drawing metadata, search fields, and a Windows or UNC path to each DXF, not file bytes or drawing geometry. It does not become a required dependency for direct File → Open of a DXF. Opening a registry entry resolves and checks its path, then invokes the ordinary DXF open path. The database layer must not write proprietary CADMATIC database files.

Use PostgreSQL for both modes: a local service on the user's Windows PC or a remote server specified by IP/host and port, reached directly by each client. Share one schema, migration sequence, and repository implementation across modes. Configure connections per workspace/project; do not hard-code a production host or credentials. Credentials belong in a Windows-protected secret store, never in project files, logs, or exported drawings. Remote deployments require explicitly configured authentication and encrypted transport; local installs bind to loopback by default. Remote registry paths must be reachable from the particular client PC; network file sharing and access control are separate from PostgreSQL. A missing/inaccessible path is a visible error, not a deleted registry record. Registry concurrency covers metadata transactions, not concurrent editing of one DXF file.

## DXF flow and failure policy

1. Read the source DXF into the document while retaining supported and raw/unknown content that the source reader represents. Record source version, entity and object inventory, stable identifiers, and a loss-risk report.
2. Execute ordinary 2D commands against the document. The initial contract includes opening, pan/zoom, basic entity edit, undo, and Save/Save As; use CADCraft's current tools instead of rebuilding them.
3. Before overwriting an original, serialize to a candidate temporary file in the target directory; parse it back and compare the content that must survive. Differences caused by the requested edit are allowed; unexplained loss of existing supported or retained content blocks overwrite. Report the exact unsupported categories or failed invariants; do not claim universal DXF losslessness.
4. On a clean verification, replace the target using Windows-safe file publication while preserving recovery of the previous version if publication fails. On failure, preserve the original and the unsaved in-memory document. A user-requested, explicitly warned lossy export may be written only to a *new* path; it never overwrites the source.
5. Use bounded parsing, errors instead of panics, and atomic/copy-on-write behavior consistent with CADCraft's safety rules. An unreadable or unsupported DXF is a visible failure, not an empty drawing that can be saved over the source.

## PostgreSQL registry flow and failure policy

Create/open a project, register an accessible drawing path with metadata, search and select entries, then open them through the standard file pipeline. Metadata updates are transactional. Database disconnects and authentication/schema-version errors are explicit; direct DXF file access remains available if PostgreSQL is down. Local mode must provide a documented way to install/start and configure PostgreSQL on Windows; remote mode tests reachability, authentication, TLS policy, and schema compatibility without silently initializing a remote database. Any production/server setup or access-control change requires a separate explicit approval before execution.

## Native project import: later feasibility-gated phase

Acceptance example (read-only): `/opt/data/agent/cadmatic/POsiva valoverhoprojekti/POsiva valoverhoprojekti 2`, containing three `.drw` drawings, one `.dwg`, `EDBProject.mdb`, `projektitiedot.ini`, and a PDF output. Do not assume that file presence proves format support.

- First prove on isolated copies that the `.drw` drawings and MDB project records can be interpreted sufficiently to show drawing geometry, project/drawing relationships, and useful searchable metadata. Use public specifications where available; compare independently with observed CADMATIC UI behavior and the example PDF. If the required interpretation cannot be established, report a blocker and do not claim import support.
- Import is one-way: parse the project into Elecraft's document model and project registry; the original `.drw` and `.mdb` remain untouched. Save subsequent drawing changes as Elecraft DXF files and metadata into PostgreSQL at separately selected destinations. The `.dwg` may use CADCraft's existing bridge, but must pass its own fidelity check before it counts as imported.
- Keep an import report with source path, source format, items imported/skipped, warnings, unresolved references and comparison results. Never silently drop an unreadable drawing, database relationship, or object. No native `.drw`/`.mdb` write-back in this design.

## Milestones and acceptance gates

1. **Independent fork/provenance and Windows baseline:** snapshot provenance; license and mark audit; build and launch an Elecraft-branded Windows binary; existing headless tests and basic UI launch pass. No CADMATIC files enter the repo.
2. **DXF safety:** test distinct synthetic and legitimately supplied DXFs through open → edit → save → reopen. Check supported geometry, layers, text, blocks, and retained unknown data where present; assert that a destructive/lossy candidate refuses overwrite, an interrupted write leaves the original recoverable, and direct DXF access works without a DB. Do not use the user's native project as a DXF fixture.
3. **PostgreSQL registry:** same schema and workflows against local Windows PostgreSQL and a test remote IP PostgreSQL; create/list/search projects and drawing references, open reachable Windows/UNC paths; verify unreachable server, bad credentials, stale schema, and inaccessible path errors. No production DB changes without approval.
4. **Native-import feasibility:** read-only copies and a written evidence report for `.drw`, MDB, and DWG. Proceed to implementation only for proven subsets; verify the example project opens/viewable with explicit coverage and warnings. Source originals remain byte-identical. An incomplete proof is a documented limitation, not a passing gate.

Quality gates include Rust format/lint/test checks, any retained CADCraft asset/layer checks, Windows build and execution, and file-level before/after checks for the example source project. This Linux session currently has no `cargo`/`rustc`; Windows toolchain and testing access must be resolved in the implementation plan rather than marked verified here.
