"""Keep historical CADCraft contributor credits available to the About build."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_contributor_metadata import check_metadata


ROOT = Path(__file__).resolve().parents[1]
HASHES = {
    'contributors/contributors.json': '42b551b5225e7fdb6ee1ab0880d34cbe435b0f92cb065d31c2d3b7e5deef6ce1',
    'contributors/people.toml': '81daea0ebd2a59e06632dc72210fe17b8e33eef8a4b639971d028bf2f2f9bb87',
}
PROVENANCE = 'docs/provenance/cadcraft-contributors-supplement.json'


class ContributorMetadataTests(unittest.TestCase):
    def test_imported_bytes_and_supplement_are_intact(self):
        self.assertEqual(check_metadata(ROOT), [])
        supplement = json.loads((ROOT / PROVENANCE).read_text(encoding='utf-8'))
        self.assertEqual(supplement['files'], HASHES)
        self.assertEqual(supplement['source_head'], '86f3199b400c271a1166103519b3785e4ac88e72')
        self.assertEqual(supplement['scope'], 'historical CADCraft contributor metadata, not Elecraft fork history')
        self.assertFalse(set(HASHES) & set(json.loads(
            (ROOT / 'docs/provenance/cadcraft-snapshot.json').read_text(encoding='utf-8')
        )['files']))

    def test_missing_or_changed_source_or_provenance_fails(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (*HASHES, PROVENANCE):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertEqual(check_metadata(root), [])
            for name in (*HASHES, PROVENANCE):
                target = root / name
                original = target.read_bytes()
                target.write_bytes(original + b'altered')
                self.assertNotEqual(check_metadata(root), [], name)
                target.unlink()
                self.assertNotEqual(check_metadata(root), [], name)
                target.write_bytes(original)
            self.assertEqual(check_metadata(root), [])
            record = json.loads((root / PROVENANCE).read_text(encoding='utf-8'))
            record['source_reported_commits'] = 27
            (root / PROVENANCE).write_text(json.dumps(record), encoding='utf-8')
            self.assertNotEqual(check_metadata(root), [], 'valid but altered provenance must fail')


if __name__ == '__main__':
    unittest.main()
