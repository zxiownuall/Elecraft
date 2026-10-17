"""Fail CI when the supplemental historical CADCraft credits are missing or changed."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'contributors/contributors.json': '42b551b5225e7fdb6ee1ab0880d34cbe435b0f92cb065d31c2d3b7e5deef6ce1',
    'contributors/people.toml': '81daea0ebd2a59e06632dc72210fe17b8e33eef8a4b639971d028bf2f2f9bb87',
}
SUPPLEMENT = 'docs/provenance/cadcraft-contributors-supplement.json'
SUPPLEMENT_SHA256 = 'c2e7187c88d5b250d9272a5914b66035179f93a68da38aeeffc8f7a2e48fa6db'
SCOPE = 'historical CADCraft contributor metadata, not Elecraft fork history'
SOURCE_HEAD = '86f3199b400c271a1166103519b3785e4ac88e72'


def check_metadata(root: Path = ROOT) -> list[str]:
    issues = []
    for name, expected in FILES.items():
        try:
            actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        except OSError as exc:
            issues.append(f'{name}: {exc}')
            continue
        if actual != expected:
            issues.append(f'{name}: SHA-256 {actual}, expected {expected}')
    try:
        raw = (root / SUPPLEMENT).read_bytes()
        if hashlib.sha256(raw).hexdigest() != SUPPLEMENT_SHA256:
            issues.append(f'{SUPPLEMENT}: SHA-256 differs from pinned supplemental record')
        record = json.loads(raw.decode('utf-8'))
        if (record.get('files') != FILES or record.get('scope') != SCOPE
                or record.get('source_head') != SOURCE_HEAD
                or record.get('source_repo') != 'storytold/cadcraft'):
            issues.append(f'{SUPPLEMENT}: provenance differs from pinned source')
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(f'{SUPPLEMENT}: {exc}')
    return issues


if __name__ == '__main__':
    import sys
    problems = check_metadata()
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        sys.exit(1)
    print('contributor metadata: pinned historical source and provenance intact')
