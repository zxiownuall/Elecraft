"""Distributable identity, resources and original icon contract (stdlib only)."""
import importlib.util
from pathlib import Path
import struct
import unittest
import zlib
from tempfile import TemporaryDirectory
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def audit(root):
    spec = importlib.util.spec_from_file_location("audit_brand", ROOT / "scripts/audit_brand.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_brand(root)


def png_pixels(png):
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    chunks = []
    offset = 8
    while offset < len(png):
        length = struct.unpack_from(">I", png, offset)[0]
        tag = png[offset + 4:offset + 8]
        data = png[offset + 8:offset + 8 + length]
        crc = struct.unpack_from(">I", png, offset + 8 + length)[0]
        assert zlib.crc32(tag + data) == crc
        chunks.append((tag, data))
        offset += length + 12
    assert offset == len(png)
    assert chunks[-1] == (b"IEND", b"")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    assert (width, height, depth, color, compression, filtering, interlace) == (256, 256, 8, 2, 0, 0, 0)
    pixels = zlib.decompress(b"".join(data for tag, data in chunks if tag == b"IDAT"))
    assert len(pixels) == height * (1 + 3 * width)
    assert all(pixels[row * (1 + 3 * width)] == 0 for row in range(height))
    return pixels


class BrandTests(unittest.TestCase):
    def test_binary_targets_and_runtime_identity(self):
        app = (ROOT / "apps/cadcraft/Cargo.toml").read_text()
        cli = (ROOT / "apps/cadcraft-cli/Cargo.toml").read_text()
        self.assertIn('default-run = "elecraft"', app)
        self.assertIn('name = "elecraft"\npath = "src/main.rs"', app)
        self.assertIn('name = "elecraft-cli"\npath = "src/main.rs"', cli)
        main = (ROOT / "apps/cadcraft/src/main.rs").read_text()
        workspace = (ROOT / "apps/cadcraft/src/workspace.rs").read_text()
        for source in (main, workspace):
            self.assertIn('"ELECRAFT_CONFIG_DIR"', source)
            self.assertIn('join("Elecraft")', source)
            self.assertNotIn('"CADCRAFT_CONFIG_DIR"', source)
        self.assertIn('.with_title("Elecraft")', main)
        self.assertIn('"Elecraft",\n', main)
        self.assertIn('format!("elecraft {}', main)
        self.assertIn('"elecraft.log"', (ROOT / "apps/cadcraft/src/logging.rs").read_text())
        self.assertIn('outln!("elecraft-cli {}', (ROOT / "apps/cadcraft-cli/src/main.rs").read_text())

    def test_packaging_identity_and_original_resource(self):
        for package, binary in (('cadcraft', 'elecraft'), ('cadcraft-cli', 'elecraft-cli')):
            manifest = tomllib.loads((ROOT / f'apps/{package}/Cargo.toml').read_text())
            self.assertEqual(manifest['package']['name'], package)
            self.assertEqual(manifest['bin'], [{'name': binary, 'path': 'src/main.rs'}])
        build = (ROOT / "apps/cadcraft/build.rs").read_text()
        self.assertIn('set_icon("../../assets/app-icon/elecraft.ico")', build)
        for field, value in (("ProductName", "Elecraft"), ("OriginalFilename", "elecraft.exe"), ("InternalName", "elecraft")):
            self.assertIn(f'.set("{field}", "{value}")', build)
        self.assertIn('ArtCraft Team and the CADCraft contributors', build)
        ps = (ROOT / "packaging/windows/package.ps1").read_text()
        wxs = (ROOT / "packaging/windows/cadcraft.wxs").read_text()
        self.assertIn("'elecraft.exe'", ps)
        self.assertIn("'elecraft-cli.exe'", ps)
        self.assertIn('Name="Elecraft"', wxs)
        self.assertIn('BinDir)\\elecraft.exe', wxs)
        self.assertNotIn('cadcraft.exe', wxs.lower())
        tree = ET.fromstring(wxs)
        namespace = {'w': 'http://wixtoolset.org/schemas/v4/wxs'}
        package = tree.find('w:Package', namespace)
        assert package is not None
        self.assertEqual(package.get('Name'), 'Elecraft')
        sources = [node.get('Source', '') for node in tree.findall('.//w:File', namespace)]
        self.assertTrue(any(source.endswith('\\elecraft.exe') for source in sources), sources)
        self.assertTrue(any(source.endswith('\\elecraft-cli.exe') for source in sources), sources)

    def test_cli_integration_tests_resolve_declared_binary(self):
        manifest = tomllib.loads((ROOT / 'apps/cadcraft-cli/Cargo.toml').read_text())
        binary = manifest['bin'][0]['name']
        for name in ('cli.rs', 'mcp_connect.rs', 'drafting_spacing.rs', 'skipped_records.rs'):
            with self.subTest(name=name):
                source = (ROOT / 'apps/cadcraft-cli/tests' / name).read_text()
                self.assertIn(f'env!("CARGO_BIN_EXE_{binary}")', source)
                self.assertNotIn('CARGO_BIN_EXE_cadcraft-cli', source)

    def test_msi_and_portable_include_legal_documents(self):
        root_files = {name for name in ('README.md', 'NOTICE', 'ATTRIBUTION.md', 'LICENSE',
                                         'LICENSE-MIT', 'LICENSE-APACHE') if (ROOT / name).is_file()}
        ps = (ROOT / 'packaging/windows/package.ps1').read_text()
        self.assertIn("foreach ($f in 'README.md', 'NOTICE', 'ATTRIBUTION.md', 'LICENSE', 'LICENSE-MIT', 'LICENSE-APACHE')", ps)
        tree = ET.parse(ROOT / 'packaging/windows/cadcraft.wxs')
        ns = {'w': 'http://wixtoolset.org/schemas/v4/wxs'}
        sources = {node.get('Source', '').split('\\')[-1] for node in tree.findall('.//w:File', ns)}
        self.assertTrue(root_files <= sources, root_files - sources)
        self.assertIn('Copy-Item $p $Stage', ps)
        self.assertIn('Copy-Item (Join-Path $Stage $f) $Portable', ps)
        # Optional embedded font licenses must follow the same staging path into both artifacts.
        self.assertIn('Copy-Item $ofl.FullName (Join-Path $Stage', ps)
        self.assertIn("Get-ChildItem -Path (Join-Path $Stage 'OFL-*.txt')", ps)
        self.assertIn('HasFontLicenses=', ps)
        self.assertIn('$(var.HasFontLicenses)', (ROOT / 'packaging/windows/cadcraft.wxs').read_text())
        self.assertIn('OFL-*.txt', (ROOT / 'packaging/windows/cadcraft.wxs').read_text())

    def test_generated_png_and_ico_embed_same_decodable_original_pixels(self):
        png = (ROOT / "assets/app-icon/elecraft-256.png").read_bytes()
        pixels = png_pixels(png)
        ico = (ROOT / "assets/app-icon/elecraft.ico").read_bytes()
        self.assertEqual(ico[:6], struct.pack('<HHH', 0, 1, 1))
        w, h, palette, reserved, planes, bpp, size, offset = struct.unpack_from('<BBBBHHII', ico, 6)
        self.assertEqual((w, h, palette, reserved, planes, bpp, size, offset), (0, 0, 0, 0, 1, 32, len(png), 22))
        self.assertEqual(ico[offset:offset + size], png)
        self.assertEqual(len(ico), offset + size)
        self.assertEqual(pixels[1:4], bytes((16, 36, 65)))
        self.assertIn(bytes((230, 245, 255)), pixels)
        spec = importlib.util.spec_from_file_location('icon', ROOT / 'scripts/make_elecraft_icon.py')
        assert spec is not None and spec.loader is not None
        icon = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(icon)
        self.assertEqual(icon.make_png(), png, 'checked-in bytes must match the stdlib generator')
        self.assertIn('elecraft-256.png', (ROOT / 'apps/cadcraft/src/main.rs').read_text())

    def test_audit_detects_product_identity_but_exempts_legal_and_internal_crates(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for directory in ('apps/cadcraft/src', 'packaging/windows', 'crates/ui-egui/src/i18n', 'docs/provenance'):
                (root / directory).mkdir(parents=True)
            (root / 'NOTICE').write_text('Copyright ArtCraft Team and CADCraft contributors')
            (root / 'docs/provenance/origin.md').write_text('CADCraft')
            (root / 'apps/cadcraft/src/internal.rs').write_text('use cadcraft_engine::Session;')
            self.assertEqual(audit(root), [])
            (root / 'apps/cadcraft/src/main.rs').write_text('include_bytes!("cadcraft-256.png");\n.with_title("CADCraft")')
            (root / 'packaging/windows/installer.wxs').write_text('Name="CADCraft"')
            (root / 'crates/ui-egui/src/i18n/de.tsv').write_text('\tAbout CADCraft\tÜber CADCraft\n')
            violations = audit(root)
            self.assertEqual(len(violations), 4, violations)
            self.assertTrue(any('main.rs' in item for item in violations))
            self.assertTrue(any('installer.wxs' in item for item in violations))
            self.assertTrue(any('de.tsv' in item for item in violations))
            (root / 'crates/mcp/src').mkdir(parents=True)
            (root / 'crates/mcp/src/server.rs').write_text('"cadcraft://drawing"')
            self.assertTrue(any('server.rs' in item for item in audit(root)))

    def test_repository_audit_and_attribution(self):
        self.assertEqual(audit(ROOT), [])
        self.assertIn('ArtCraft Team and the CADCraft contributors', (ROOT / 'NOTICE').read_text())

    def test_localized_about_key_is_present_without_old_marketing(self):
        catalogs = sorted((ROOT / 'crates/ui-egui/src/i18n').glob('*.tsv'))
        self.assertEqual(len(catalogs), 12)
        for catalog in catalogs:
            records = [line.split('\t') for line in catalog.read_text().splitlines() if not line.startswith('#') and line.strip()]
            self.assertTrue(all(len(parts) == 3 for parts in records), catalog.name)
            self.assertEqual(len({(parts[0], parts[1]) for parts in records}), len(records), catalog.name)
            self.assertTrue(any(parts[1] == 'About Elecraft' and parts[2] for parts in records), catalog.name)
            self.assertFalse(any('ArtCraft' in part for parts in records for part in parts), catalog.name)

    def test_backend_and_exporters_show_current_identity(self):
        backend = (ROOT / 'crates/mcp/src/backend.rs').read_text()
        self.assertIn('connected to Elecraft at', backend)
        self.assertIn('"-a", "Elecraft"', backend)
        self.assertIn('elecraft://drawing', (ROOT / 'crates/mcp/src/server.rs').read_text())
        plotters = (ROOT / 'crates/engine/src/cmd/plotters.rs').read_text()
        self.assertIn('"ELECRAFT_CONFIG_DIR"', plotters)
        self.assertIn('"Elecraft PDF"', plotters)
        self.assertIn('/Producer (Elecraft)', (ROOT / 'crates/io/src/pdf.rs').read_text())
        self.assertIn('BUILTIN_FONT: &str = "Elecraft Stroke"', (ROOT / 'crates/fonts/src/lib.rs').read_text())


if __name__ == '__main__':
    unittest.main()
