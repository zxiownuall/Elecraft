"""Import an attributed, allowlisted CADCraft source snapshot."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

DIRS = ('crates', 'apps', 'xtask', '.cargo', 'packaging/windows')
FILES = ('Cargo.toml', 'Cargo.lock', '.gitignore', 'rustfmt.toml',
         'clippy.toml', 'LICENSE-MIT', 'LICENSE-APACHE', 'NOTICE',
         'ATTRIBUTION.md', 'docs/control-protocol.md')


def _preflight_destination(dest: Path, relative: Path) -> None:
    target = dest / relative
    for path in (dest, *(dest / Path(*relative.parts[:i])
                         for i in range(1, len(relative.parts) + 1))):
        if path.is_symlink() or (path == target and path.exists()):
            raise FileExistsError(relative.as_posix())
        if path != target and path.exists() and not path.is_dir():
            raise FileExistsError(relative.as_posix())


def import_snapshot(source: Path, dest: Path) -> dict:
    source, dest = source.resolve(), dest.resolve()
    if not source.is_dir() or source == dest or source in dest.parents or dest in source.parents:
        raise ValueError('source and destination must be distinct directories')
    selected = []
    for name in DIRS:
        root = source / name
        if not root.is_dir():
            raise FileExistsError(name)
        if any(source.joinpath(*Path(name).parts[:i]).is_symlink()
               for i in range(1, len(Path(name).parts) + 1)):
            raise ValueError(f'symlink in source: {name}')
        _preflight_destination(dest, Path(name))
        for p in root.rglob('*'):
            if '.git' in p.relative_to(source).parts:
                continue
            if p.is_symlink():
                raise ValueError(f'symlink in source: {p.relative_to(source)}')
            if p.is_file():
                selected.append(p)
    for name in FILES:
        p = source / name
        if not p.is_file():
            raise FileExistsError(name)
        _preflight_destination(dest, Path(name))
        selected.append(p)
    for p in selected:  # Preflight before writing any destination file.
        rel = p.relative_to(source)
        parts = [source.joinpath(*rel.parts[:i]) for i in range(1, len(rel.parts) + 1)]
        if any(x.is_symlink() for x in parts):
            raise ValueError(f'symlink in source: {rel}')
        _preflight_destination(dest, rel)
    _preflight_destination(dest, Path('docs/provenance/cadcraft-snapshot.json'))
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--dest', type=Path, required=True)
    args = parser.parse_args()
    manifest = import_snapshot(args.source, args.dest)
    print(f"Imported {len(manifest['files'])} files; manifest: "
          f"{args.dest / 'docs/provenance/cadcraft-snapshot.json'}")


if __name__ == '__main__':
    main()
