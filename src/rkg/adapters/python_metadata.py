"""Static Python dependency inventory from immutable manifest bytes.

Only declared metadata is trusted. Import ownership is an explicit adapter profile;
an arbitrary distribution name is never converted into an import name.
"""

from __future__ import annotations

import ast
import re
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath

from rkg.adapters.contracts import AdapterContext, AdapterDiagnostic, ParseResult
from rkg.adapters.python_language import _module_name, _unique_definitions
from rkg.adapters.python_resolution import _bindings, _frames, _Module, _qualified
from rkg.domain import (
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.ingestion import SourceManifest

DECLARED_RULE = "RKG.python_metadata.declared.v1"
USED_RULE = "RKG.python_metadata.used.v1"
LOCK_RULE = "RKG.python_metadata.lock.v1"
_REQUIREMENT = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^]]+\])?\s*(.*)$")
_NORMALIZE = re.compile(r"[-_.]+")
# Reviewed import ownership for the MVP profile. No fallback based on similar names.
IMPORT_OWNERS: dict[str, tuple[str, ...]] = {
    "fastapi": ("fastapi",),
    "sqlalchemy": ("sqlalchemy",),
    "aiokafka": ("aiokafka",),
    "httpx": ("httpx",),
    "requests": ("requests",),
    "pydantic": ("pydantic",),
    "pyyaml": ("yaml",),
    "beautifulsoup4": ("bs4",),
    "pillow": ("PIL",),
    "python-dateutil": ("dateutil",),
    "uvicorn": ("uvicorn",),
    "numpy": ("numpy",),
}


@dataclass(frozen=True, slots=True)
class Dependency:
    name: str
    version: str | None
    source: str
    path: str
    line: int
    group: str = "main"
    marker: str | None = None
    lock_only: bool = False


@dataclass(frozen=True, slots=True)
class Inventory:
    dependencies: tuple[Dependency, ...]
    diagnostics: tuple[AdapterDiagnostic, ...]


def _norm(value: str) -> str:
    return _NORMALIZE.sub("-", value).lower()


def _body_nodes(function: ast.FunctionDef | ast.AsyncFunctionDef):
    """Walk a callable's body without attributing nested callables to its owner."""
    pending = list(reversed(function.body))
    while pending:
        node = pending.pop()
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        yield node
        pending.extend(reversed(list(ast.iter_child_nodes(node))))


def _line(content: bytes, needle: str) -> int:
    for number, row in enumerate(
        content.decode("utf-8", errors="replace").splitlines(), 1
    ):
        if needle in row:
            return number
    name = _REQUIREMENT.match(needle)
    if name:
        for number, row in enumerate(
            content.decode("utf-8", errors="replace").splitlines(), 1
        ):
            if re.search(rf"\b{re.escape(name.group(1))}\b", row):
                return number
    return 1


def _requirement(value: str, path: str, line: int, group: str) -> Dependency | None:
    main, _, marker = value.partition(";")
    match = _REQUIREMENT.match(main)
    if not match or main.lstrip().startswith(("-", "#")):
        return None
    spec = match.group(2).strip()
    # URLs and editable sources can contain credentials; reject the entire entry.
    if spec and not re.fullmatch(r"[<>=!~^.*,0-9\s]+", spec):
        return None
    version = spec or None
    return Dependency(
        _norm(match.group(1)),
        version,
        "declared",
        path,
        line,
        group,
        marker.strip() or None,
    )


def read_inventory(manifest: SourceManifest) -> Inventory:
    files = {item.relative_path: item.content for item in manifest.files}
    dependencies: list[Dependency] = []
    diagnostics: list[AdapterDiagnostic] = []

    def add(value: str, path: str, group: str) -> None:
        item = _requirement(value, path, _line(files[path], value), group)
        if item:
            dependencies.append(item)
        else:
            diagnostics.append(
                AdapterDiagnostic("python_metadata_unsupported", path, 1)
            )

    for path in sorted(files):
        if PurePosixPath(path).name != "pyproject.toml":
            continue
        try:
            document = tomllib.loads(files[path].decode("utf-8"))
        except (UnicodeError, tomllib.TOMLDecodeError):
            diagnostics.append(AdapterDiagnostic("python_metadata_invalid", path, 1))
            continue
        project = document.get("project", {})
        if isinstance(project, dict):
            if "dependencies" in project.get("dynamic", ()):
                diagnostics.append(
                    AdapterDiagnostic("python_metadata_dynamic", path, 1)
                )
            for value in project.get("dependencies", ()):
                if isinstance(value, str):
                    add(value, path, "main")
            for group, values in project.get("optional-dependencies", {}).items():
                for value in values:
                    if isinstance(value, str):
                        add(value, path, str(group))
        groups = document.get("dependency-groups", {})

        def expand_group(group: str, current: str, stack: frozenset[str]) -> None:
            if current in stack:
                diagnostics.append(
                    AdapterDiagnostic("python_metadata_include_cycle", path, 1)
                )
                return
            for value in groups.get(current, ()):
                if isinstance(value, str):
                    add(value, path, group)
                elif isinstance(value, dict) and isinstance(
                    value.get("include-group"), str
                ):
                    expand_group(group, value["include-group"], stack | {current})

        for group in sorted(groups):
            expand_group(str(group), str(group), frozenset())
        poetry = document.get("tool", {}).get("poetry", {})
        for group, values in [("main", poetry.get("dependencies", {}))] + [
            (name, body.get("dependencies", {}))
            for name, body in poetry.get("group", {}).items()
        ]:
            for name, constraint in values.items():
                if name.lower() == "python":
                    continue
                spec = (
                    constraint
                    if isinstance(constraint, str)
                    else constraint.get("version", "")
                )
                add(f"{name}{spec if isinstance(spec, str) else ''}", path, str(group))

    def requirements(path: str, stack: frozenset[str]) -> None:
        if path in stack:
            diagnostics.append(
                AdapterDiagnostic("python_metadata_include_cycle", path, 1)
            )
            return
        for number, raw in enumerate(
            files[path].decode("utf-8", errors="replace").splitlines(), 1
        ):
            value = raw.strip()
            if not value or value.startswith("#"):
                continue
            if value.startswith(("-r ", "--requirement ", "-c ", "--constraint ")):
                child = value.split(maxsplit=1)[1].strip()
                target = str(PurePosixPath(path).parent / child)
                if (
                    child.startswith("/")
                    or ".." in PurePosixPath(child).parts
                    or target not in files
                ):
                    diagnostics.append(
                        AdapterDiagnostic(
                            "python_metadata_include_missing", path, number
                        )
                    )
                else:
                    requirements(target, stack | {path})
                continue
            item = _requirement(value, path, number, "main")
            if item:
                dependencies.append(item)
            else:
                diagnostics.append(
                    AdapterDiagnostic("python_metadata_unsupported", path, number)
                )

    for path in sorted(files):
        name = PurePosixPath(path).name
        if name.startswith("requirements") and name.endswith(".txt"):
            requirements(path, frozenset())

    for path in sorted(files):
        if PurePosixPath(path).name not in {"uv.lock", "poetry.lock"}:
            continue
        try:
            document = tomllib.loads(files[path].decode("utf-8"))
        except (UnicodeError, tomllib.TOMLDecodeError):
            diagnostics.append(AdapterDiagnostic("python_metadata_invalid", path, 1))
            continue
        declared = {item.name for item in dependencies if not item.lock_only}
        for package in document.get("package", ()):
            name = package.get("name")
            version = package.get("version")
            if isinstance(name, str) and isinstance(version, str):
                normalized = _norm(name)
                dependencies.append(
                    Dependency(
                        normalized,
                        version,
                        "lock",
                        path,
                        _line(files[path], f'name = "{name}"'),
                        lock_only=normalized not in declared,
                    )
                )
    return Inventory(
        tuple(
            sorted(
                set(dependencies),
                key=lambda item: (
                    item.name,
                    item.path,
                    item.line,
                    item.group,
                    item.source,
                ),
            )
        ),
        tuple(diagnostics),
    )


def add_inventory_facts(
    context: AdapterContext, parsed: ParseResult, candidate: FactBatch
) -> FactBatch:
    inventories = [
        unit.representation
        for unit in parsed.units
        if unit.representation_kind == "python-metadata/v1"
    ]
    if not inventories:
        return candidate
    inventory = inventories[0]
    assert isinstance(inventory, Inventory)
    entities = {item.id: item for item in candidate.entities}
    edges = {item.id: item for item in candidate.edges}
    evidence = {item.id: item for item in candidate.evidence}
    by_name: dict[str, list[Dependency]] = defaultdict(list)
    for item in inventory.dependencies:
        by_name[item.name].append(item)
    module_names = {
        item.qualified_name.split(".")[0]
        for item in candidate.entities
        if item.type == EntityType.SOURCE_UNIT
    }
    module_names.update(
        PurePosixPath(item.file_path).stem
        for item in candidate.entities
        if item.type == EntityType.SOURCE_UNIT and item.file_path
    )
    import_owner = {
        root: name for name in by_name for root in IMPORT_OWNERS.get(name, ())
    }
    observed: set[str] = set()
    use_sites: list[tuple[str, str, int]] = []
    for unit in parsed.units:
        if not isinstance(unit.representation, ast.Module):
            continue
        path = unit.relative_path
        module = _Module(path, _module_name(path), unit.representation)
        module_frame = _bindings(module, module.tree.body, module.name)
        definitions_list, _ = _unique_definitions(module.tree, module.name, path)
        definitions = {name: (owner, node) for owner, name, node in definitions_list}
        for node in ast.walk(module.tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)) and not getattr(
                node, "level", 0
            ):
                roots = (
                    [alias.name.split(".")[0] for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module.split(".")[0]]
                    if node.module
                    else []
                )
                for root in roots:
                    if root not in module_names and root in import_owner:
                        observed.add(import_owner[root])
        for _, name, node in definitions_list:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                source = next(
                    (
                        item
                        for item in entities.values()
                        if item.type == EntityType.CALLABLE
                        and item.qualified_name == name
                        and item.file_path == path
                    ),
                    None,
                )
                if source is None:
                    continue
                frames = _frames(name, module, definitions, module_frame)
                for child in _body_nodes(node):
                    if not isinstance(child, (ast.Call, ast.Name, ast.Attribute)):
                        continue
                    expression = child.func if isinstance(child, ast.Call) else child
                    qualified = _qualified(expression, frames)
                    if (
                        qualified
                        and qualified.split(".")[0] in import_owner
                        and qualified.split(".")[0] not in module_names
                    ):
                        use_sites.append(
                            (
                                source.id,
                                import_owner[qualified.split(".")[0]],
                                child.lineno,
                            )
                        )
    for name, declarations in sorted(by_name.items()):
        primary = next(
            (item for item in declarations if item.source == "declared"),
            declarations[0],
        )
        lock = next((item for item in declarations if item.source == "lock"), None)
        entity_id = source_entity_id(
            context.repository_id, "", EntityType.EXTERNAL_DEPENDENCY, name
        )
        attrs = (
            (
                "status",
                "lock_only"
                if all(item.lock_only for item in declarations)
                else "declared"
                if name in observed
                else "declared_no_observed_import",
            ),
            ("version", lock.version if lock else primary.version),
            ("version_provenance", "lock" if lock else "declared"),
            (
                "groups",
                tuple(
                    sorted(
                        {
                            item.group
                            for item in declarations
                            if item.source == "declared"
                        }
                    )
                ),
            ),
            (
                "markers",
                tuple(sorted({item.marker for item in declarations if item.marker})),
            ),
        )
        entities[entity_id] = Entity(
            entity_id,
            context.repository_id,
            context.snapshot_id,
            EntityType.EXTERNAL_DEPENDENCY,
            name,
            name,
            attributes=attrs,
        )
        for item in declarations:
            rule = LOCK_RULE if item.source == "lock" else DECLARED_RULE
            ev_id = evidence_id(
                context.snapshot_id, item.path, item.line, item.line, rule
            )
            evidence[ev_id] = Evidence(
                ev_id, context.snapshot_id, item.path, item.line, item.line, rule
            )
            key = edge_id(
                context.snapshot_id,
                EdgeType.DEPENDS_ON,
                context.repository_id,
                entity_id,
            )
            prior = edges.get(key)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                EdgeType.DEPENDS_ON,
                context.repository_id,
                entity_id,
                DECLARED_RULE
                if not all(d.lock_only for d in declarations)
                else LOCK_RULE,
                tuple(sorted(set(prior.evidence_ids if prior else ()) | {ev_id})),
            )
        for source, used_name, line in use_sites:
            if used_name != name:
                continue
            ev_id = evidence_id(
                context.snapshot_id,
                next(item.file_path for item in entities.values() if item.id == source),
                line,
                line,
                USED_RULE,
            )
            path = next(
                item.file_path for item in entities.values() if item.id == source
            )
            evidence[ev_id] = Evidence(
                ev_id, context.snapshot_id, path, line, line, USED_RULE
            )
            key = edge_id(context.snapshot_id, EdgeType.DEPENDS_ON, source, entity_id)
            prior = edges.get(key)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                EdgeType.DEPENDS_ON,
                source,
                entity_id,
                USED_RULE,
                tuple(sorted(set(prior.evidence_ids if prior else ()) | {ev_id})),
            )
    return FactBatch(
        context.repository_id,
        context.snapshot_id,
        tuple(entities[key] for key in sorted(entities)),
        tuple(edges[key] for key in sorted(edges)),
        tuple(evidence[key] for key in sorted(evidence)),
        candidate.diagnostics,
    )
