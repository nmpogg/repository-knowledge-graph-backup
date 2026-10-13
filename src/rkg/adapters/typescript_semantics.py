"""Source-backed class heritage and local Map operation metadata."""

from dataclasses import replace

from rkg.adapters.typescript_parse import (
    child_named,
    identifier_name,
    named_children,
    text_of,
    walk_named,
)
from rkg.domain import EdgeType, Entity, EntityType, source_entity_id


def enrich_class_semantics(module, index, scope, facts, edges):
    for definition in module.definitions:
        entity = index.unique(
            definition.qualified_name, frozenset({EntityType.CALLABLE})
        )
        if entity is None:
            continue
        for node in walk_named(definition.node):
            if node.type == "return_statement":
                returned = next(
                    (
                        n
                        for n in named_children(node)
                        if n.type == "function_expression"
                    ),
                    None,
                )
                if returned is not None:
                    name = identifier_name(module.source, child_named(returned, "name"))
                    if name:
                        attrs = dict(facts.entities[entity.id].attributes)
                        attrs["returns_callable"] = name
                        facts.entities[entity.id] = replace(
                            facts.entities[entity.id], attributes=tuple(attrs.items())
                        )
    for definition in module.definitions:
        if definition.kind != "typescript_class":
            continue
        owner = index.unique(definition.qualified_name, frozenset({EntityType.TYPE}))
        if owner is None:
            continue
        for heritage in named_children(definition.node):
            if heritage.type != "class_heritage":
                continue
            for clause in named_children(heritage):
                relation = (
                    EdgeType.INHERITS_FROM
                    if clause.type == "extends_clause"
                    else EdgeType.IMPLEMENTS
                )
                for base_node in named_children(clause):
                    name = identifier_name(module.source, base_node)
                    if name is None:
                        continue
                    target = index.unique(
                        scope.names.get(name), frozenset({EntityType.TYPE})
                    )
                    if (
                        target is None
                        and name in {"Error", "Map", "Set"}
                        and name not in scope.names
                    ):
                        qn = "javascript." + name
                        key = source_entity_id(
                            facts.context.repository_id, "", EntityType.TYPE, qn
                        )
                        target = facts.ensure(
                            Entity(
                                key,
                                facts.context.repository_id,
                                facts.context.snapshot_id,
                                EntityType.TYPE,
                                name,
                                qn,
                                language_kind="javascript_builtin",
                            )
                        )
                    if target:
                        edges.add(
                            relation,
                            owner.id,
                            target.id,
                            module.path,
                            base_node.start_point[0] + 1,
                            "RKG.typescript.heritage.v1",
                        )
        if "Map" in scope.names:
            continue
        body = child_named(definition.node, "body")
        if body is None:
            continue
        map_fields = set()
        for member in named_children(body):
            value = child_named(member, "value")
            if (
                value is not None
                and value.type == "new_expression"
                and any(
                    text_of(module.source, c) == "readonly" for c in member.children
                )
            ):
                ctor = child_named(value, "constructor")
                if identifier_name(module.source, ctor) == "Map":
                    name = identifier_name(module.source, child_named(member, "name"))
                    if name:
                        map_fields.add(name)
        for method in module.definitions:
            if method.owner != definition.qualified_name:
                continue
            entity = index.unique(
                method.qualified_name, frozenset({EntityType.CALLABLE})
            )
            if entity is None:
                continue
            operations, other_calls = [], False
            for node in walk_named(method.node):
                if node.type not in {"call_expression", "new_expression"}:
                    continue
                callee = child_named(node, "function")
                if callee is None or callee.type != "member_expression":
                    other_calls = True
                    continue
                receiver = child_named(callee, "object")
                operation = identifier_name(
                    module.source, child_named(callee, "property")
                )
                field = (
                    identifier_name(module.source, child_named(receiver, "property"))
                    if receiver is not None
                    else None
                )
                obj = child_named(receiver, "object") if receiver is not None else None
                if (
                    field in map_fields
                    and text_of(module.source, obj) == "this"
                    and operation in {"get", "set", "delete", "has", "values", "clear"}
                ):
                    operations.append(f"{field}.{operation}")
                else:
                    other_calls = True
            if operations:
                attrs = dict(facts.entities[entity.id].attributes)
                attrs.update(
                    storage_kind="memory_map",
                    storage_operations=tuple(dict.fromkeys(operations)),
                    storage_operations_only=not other_calls,
                )
                facts.entities[entity.id] = replace(
                    facts.entities[entity.id], attributes=tuple(attrs.items())
                )
