import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.import_cadcraft_snapshot import import_snapshot


class ImportSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source'
        self.dest = Path(self.temp.name) / 'dest'
        self.source.mkdir()
        self.dest.mkdir()
        self.sample = {
            'Cargo.toml': b'[workspace]\n',
            'crates/geom/src/lib.rs': b'pub fn geom() {}\n',
            'docs/brand/mark.svg': b'<svg/>',
            'assets/app-icon/cadcraft.ico': b'old icon',
            'LICENSE-MIT': b'MIT license\n',
            '.git/config': b'[core]\n',
        }
        for name, data in self.sample.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name in ('apps', 'xtask', '.cargo', 'packaging/windows'):
            (self.source / name).mkdir(parents=True)
        for name in ('Cargo.lock', '.gitignore', 'rustfmt.toml', 'clippy.toml',
                     'LICENSE-APACHE', 'NOTICE', 'ATTRIBUTION.md',
                     'docs/control-protocol.md'):
            self.sample[name] = b''
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')

    def test_allowlist_hashes_and_manifest(self):
        manifest = import_snapshot(self.source, self.dest)
        allowed = set(self.sample) - {'docs/brand/mark.svg',
                                      'assets/app-icon/cadcraft.ico', '.git/config'}
        self.assertEqual(list(manifest['files']), sorted(allowed))
        for name in allowed:
            self.assertEqual((self.dest / name).read_bytes(), self.sample[name])
            self.assertEqual(manifest['files'][name], hashlib.sha256(self.sample[name]).hexdigest())
        for name in set(self.sample) - allowed:
            self.assertNotIn(name, manifest['files'])
            self.assertFalse((self.dest / name).exists())
        saved = json.loads((self.dest / 'docs/provenance/cadcraft-snapshot.json').read_text())
        self.assertEqual(saved, manifest)
        self.assertEqual(manifest['source'], str(self.source.resolve()))
        self.assertEqual(manifest['url'], 'https://github.com/storytold/cadcraft')
        self.assertIn('captured_utc', manifest)

    def test_refuses_second_import_before_changing_files(self):
        import_snapshot(self.source, self.dest)
        original = (self.dest / 'Cargo.toml').read_bytes()
        with self.assertRaises(FileExistsError):
            import_snapshot(self.source, self.dest)
        self.assertEqual((self.dest / 'Cargo.toml').read_bytes(), original)

    def test_symlink_is_rejected_before_any_copy(self):
        (self.source / 'crates/geom/src/lib.rs').unlink()
        (self.source / 'crates/geom/src/lib.rs').symlink_to(self.source / 'Cargo.toml')
        with self.assertRaisesRegex(ValueError, 'symlink in source'):
            import_snapshot(self.source, self.dest)
        self.assertFalse((self.dest / 'Cargo.toml').exists())

    def test_refuses_nested_source_and_destination(self):
        with self.assertRaises(ValueError):
            import_snapshot(self.source, self.source / 'nested')
