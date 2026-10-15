#!/usr/bin/env python3
"""Check source pins and fixture inventory without importing/executing C# source."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {'bin', 'obj', 'TestResults', '.git', '__pycache__'}


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative_file(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name,
            'Inventory path must be repository-relative')
    target = ROOT / name
    require(not target.is_symlink() and target.resolve().is_relative_to(ROOT),
            'Inventory path escapes fixture')
    require(target.is_file(), 'Missing inventory source')
    return target


def verify_evidence(value):
    if isinstance(value, dict):
        if 'evidence' in value:
            evidence = value['evidence']
            evidence_items = evidence if isinstance(evidence, list) else [evidence]
            for source in evidence_items:
                lines = relative_file(source['path']).read_text(encoding='utf-8').splitlines()
                number = source['line']
                require(isinstance(number, int) and 1 <= number <= len(lines), 'Invalid evidence line')
                if 'line_sha256' in source:
                    require(hashlib.sha256(lines[number - 1].encode()).hexdigest() == source['line_sha256'],
                            'Evidence line changed; review inventory')
        for item in value.values():
            verify_evidence(item)
    elif isinstance(value, list):
        for item in value:
            verify_evidence(item)


def main():
    entities = read_json('expected/entities.json')['exact']
    edges = read_json('expected/edges.json')
    questions = read_json('expected/questions.json')['cases']
    keys = {item['key'] for item in entities}
    require(len(keys) == len(entities), 'Duplicate entity semantic key')
    allowed_types = {'Type', 'Callable', 'Endpoint', 'DataResource', 'ExternalDependency'}
    allowed_relations = {'handled_by', 'calls', 'implements', 'depends_on', 'maps_to', 'reads', 'writes'}
    for item in entities:
        require(item['type'] in allowed_types, 'Unknown canonical entity type')
        require(item['stage'] in {'language', 'framework', 'data_access'}, 'Unknown demo stage')
    seen_edges = set()
    for item in edges['exact'] + edges['optional']:
        require(item['source'] in keys and item['target'] in keys, 'Dangling edge key')
        require(item['relation'] in allowed_relations, 'Unknown canonical relation')
        identity = (item['source'], item['relation'], item['target'])
        require(identity not in seen_edges, 'Duplicate edge identity')
        seen_edges.add(identity)
    endpoints = [(item['method'], item['path']) for item in entities if item['type'] == 'Endpoint']
    require(len(endpoints) == len(set(endpoints)) == 6, 'Expected six distinct method/path endpoints')
    require(len({case['key'] for case in questions}) == len(questions) == 10, 'Expected ten demo questions')
    for case in questions:
        require(set(case['required_entities']) <= keys, 'Dangling question entity key')
    for path in sorted((ROOT / 'expected').glob('*.json')):
        verify_evidence(read_json(path.relative_to(ROOT).as_posix()))
    manifest = read_json('expected/source-manifest.json')
    actual = sorted(path.relative_to(ROOT).as_posix() for path in ROOT.rglob('*')
                    if path.is_file() and not (set(path.relative_to(ROOT).parts) & IGNORED)
                    and (path.suffix in {'.cs', '.csproj', '.props', '.slnx'}
                         or path.name in {'packages.lock.json', 'global.json', 'NuGet.Config'}
                         or 'analysis-cases' in path.relative_to(ROOT).parts))
    require(actual == sorted(manifest['files']), 'Source manifest file inventory changed')
    for name, digest in manifest['files'].items():
        require(hashlib.sha256(relative_file(name).read_bytes()).hexdigest() == digest,
                'Source digest changed; review inventory before updating pins')
    for project in ROOT.rglob('*.csproj'):
        lock = json.loads(project.with_name('packages.lock.json').read_text())
        dependencies = lock['dependencies']['net10.0']
        for ref in ET.parse(project).getroot().iter('PackageReference'):
            name, version = ref.attrib['Include'], ref.attrib['Version']
            require(dependencies[name]['resolved'] == version, 'Direct dependency lock/version mismatch')
    print(f'PASS: {len(entities)} entities, {len(edges["exact"])} exact edges, '
          f'{len(edges["optional"])} optional edges, {len(questions)} questions; '
          f'{len(actual)} source/build files pinned. C# source was not executed.')


if __name__ == '__main__':
    main()
