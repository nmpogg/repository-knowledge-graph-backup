from dataclasses import replace

import pytest

from rkg.conversations.narrative import render_narrative, validate_narrative
from rkg.domain.models import (
    ContextPackage,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
)
from rkg.llm import LLMError


def fixture():
    nodes = tuple(
        Entity(i, "repo", "snap", EntityType.CALLABLE, i, "app." + i)
        for i in ("a", "b", "c")
    )
    ev = Evidence("ev", "snap", "app/calls.py", 1, 2, "calls")
    edges = (
        Edge("ab", "snap", EdgeType.CALLS, "a", "b", "calls", ("ev",)),
        Edge("bc", "snap", EdgeType.CALLS, "b", "c", "calls", ("ev",)),
        Edge("ca", "snap", EdgeType.CALLS, "c", "a", "calls", ("ev",)),
    )
    return ContextPackage("v1", "repo", "snap", "a", nodes, edges, (ev,))


def response(edge_ids=("ab",), root="a", anchor="a", direction="outgoing"):
    return {
        "status": "answered",
        "root_id": root,
        "sections": [
            {
                "relation": "calls",
                "direction": direction,
                "paths": [{"anchor_id": anchor, "edge_ids": list(edge_ids)}],
            }
        ],
    }


@pytest.mark.parametrize(
    "value",
    [
        response(root="foreign"),
        response(anchor="b"),
        response(("foreign",)),
        response(("bc",)),
        response(("ab", "bc", "ca")),
        response(direction="incoming"),
        {**response(), "answer": "invented fact"},
    ],
)
def test_complete_narrative_fails_closed(value):
    with pytest.raises(LLMError) as error:
        validate_narrative(value, fixture(), ("calls",), "outgoing")
    assert error.value.code == "llm_malformed_response"


def test_direct_indirect_and_exact_bindings():
    context = fixture()
    value = response(("ab", "bc"))
    value["sections"][0]["paths"].insert(0, {"anchor_id": "a", "edge_ids": ["ab"]})
    selected = validate_narrative(value, context, ("calls",), "outgoing")
    answer, claims, citations = render_narrative(selected, context, "en")
    assert "directly" in answer and "indirectly" in answer
    assert len(claims) == 2
    for claim in claims:
        assert citations[claim["citation_indexes"][0]]["edge_id"] == claim["edge_id"]
        assert citations[claim["citation_indexes"][0]]["evidence_id"] == "ev"


def test_missing_and_foreign_snapshot_evidence_rejected():
    context = fixture()
    for evidence in [
        (),
        (replace(context.evidence[0], snapshot_id="other"),),
        (replace(context.evidence[0], file_path="/private/source.py"),),
    ]:
        with pytest.raises(LLMError):
            validate_narrative(
                response(), replace(context, evidence=evidence), ("calls",), "outgoing"
            )


def test_incoming_preserves_caller_roles():
    context = fixture()
    selected = validate_narrative(
        response(("ca",), direction="incoming"), context, ("calls",), "incoming"
    )
    answer, claims, _ = render_narrative(selected, context, "en")
    assert "c calls a" in claims[0]["text"]
    assert "a calls c" not in answer


def test_aggregate_edge_limit_and_status_consistency():
    context = fixture()
    targets = tuple(
        replace(context.nodes[1], id="t" + str(i), name="t" + str(i)) for i in range(9)
    )
    edges = tuple(
        replace(context.edges[0], id="e" + str(i), target_id=targets[i].id)
        for i in range(9)
    )
    context = replace(context, nodes=(context.nodes[0], *targets), edges=edges)
    sections = [
        {
            "relation": "calls",
            "direction": "outgoing",
            "paths": [{"anchor_id": "a", "edge_ids": [e.id]} for e in edges[:8]],
        },
        {
            "relation": "calls",
            "direction": "outgoing",
            "paths": [{"anchor_id": "a", "edge_ids": [edges[8].id]}],
        },
    ]
    with pytest.raises(LLMError):
        validate_narrative(
            {"status": "answered", "root_id": "a", "sections": sections},
            context,
            ("calls",),
            "outgoing",
        )
    for value in [
        {"status": "answered", "root_id": "a", "sections": []},
        {**response(), "status": "insufficient_evidence"},
    ]:
        with pytest.raises(LLMError):
            validate_narrative(value, fixture(), ("calls",), "outgoing")


def test_foreign_node_and_unrequested_relation_rejected():
    context = fixture()
    other = replace(context.nodes[1], snapshot_id="other")
    with pytest.raises(LLMError):
        validate_narrative(
            response(),
            replace(context, nodes=(context.nodes[0], other, context.nodes[2])),
            ("calls",),
            "outgoing",
        )
    with pytest.raises(LLMError):
        validate_narrative(response(), context, ("reads",), "outgoing")


@pytest.mark.parametrize(
    ("question", "relation"),
    [
        ("what does a call", "calls"),
        ("a doc gi", "reads"),
        ("a ghi gi", "writes"),
        ("a phat len dau", "publishes"),
        ("a nhan tu dau", "consumes"),
        ("a trien khai gi", "implements"),
        ("a ke thua gi", "inherits_from"),
        ("what does a contain", "contains"),
        ("what does a expose", "exposes"),
        ("what is a handled by", "handled_by"),
        ("a phu thuoc gi", "depends_on"),
        ("a maps to what", "maps_to"),
        ("a imports what", "imports"),
    ],
)
def test_explicit_relation_is_bound_before_narrative(question, relation):
    from rkg.conversations.grounded import _relation_types

    assert relation in _relation_types(question)


def test_indirect_write_primary_answer_names_actual_relation():
    context = fixture()
    terminal = replace(context.edges[1], type=EdgeType.WRITES)
    context = replace(context, edges=(context.edges[0], terminal))
    value = response(("ab", "bc"))
    value["sections"][0]["relation"] = "writes"
    paths = validate_narrative(value, context, ("writes",), "outgoing")
    answer, _, _ = render_narrative(paths, context, "en")
    assert "writes to" in answer
    assert "calls" in answer


def test_colliding_qualified_names_remain_distinguishable_in_both_languages():
    context = fixture()
    one = replace(
        context.nodes[0],
        name="login",
        qualified_name="app.login",
        file_path="a/auth.py",
        start_line=1,
    )
    two = replace(
        context.nodes[1],
        name="login",
        qualified_name="app.login",
        file_path="b/auth.py",
        start_line=3,
    )
    context = replace(context, nodes=(one, two, context.nodes[2]))
    paths = validate_narrative(response(), context, ("calls",), "outgoing")
    for language in ("vi", "en"):
        answer, claims, _ = render_narrative(paths, context, language)
        assert "a/auth.py" in answer and "b/auth.py" in answer
        assert "app.login calls app.login." not in claims[0]["text"]


def test_identifier_relation_words_cannot_widen_explicit_intent():
    from rkg.conversations.grounded import _relation_types

    assert _relation_types("What does \x60app.calls\x60 write?") == ("writes",)
    assert _relation_types("Which interface does app.Child inherit from?") == (
        "inherits_from",
    )


@pytest.mark.parametrize(("language", "name"), [("en", "repository"), ("vi", "kho mã")])
def test_repository_pseudo_node_participates_in_collision_counts(language, name):
    context = fixture()
    dependency = replace(
        context.nodes[0],
        type=EntityType.EXTERNAL_DEPENDENCY,
        name=name,
        qualified_name=name,
        file_path="requirements.txt",
    )
    edge = replace(
        context.edges[0],
        id="dependency-edge",
        type=EdgeType.DEPENDS_ON,
        source_id="repo",
        target_id="a",
    )
    context = replace(context, nodes=(dependency,), edges=(edge,))
    value = response(("dependency-edge",), direction="incoming")
    value["sections"][0]["relation"] = "depends_on"
    selected = validate_narrative(value, context, ("depends_on",), "incoming")
    answer, claims, _ = render_narrative(selected, context, language)
    assert "requirements.txt" in answer
    assert f"{name} depends on {name}." not in claims[0]["text"]
    assert f"{name} phụ thuộc vào {name}." not in claims[0]["text"]


@pytest.mark.parametrize("language", ["vi", "en"])
def test_checkout_tables_are_explained_in_sentences_with_shared_steps(language):
    from rkg.conversations.narrative import NarrativePath

    context = fixture()
    names = {"a": "checkout", "b": "validate_quantities", "c": "product_context"}
    nodes = tuple(replace(n, name=names[n.id]) for n in context.nodes)
    tables = tuple(
        Entity(
            name,
            "repo",
            "snap",
            EntityType.DATA_RESOURCE,
            name,
            name,
            attributes=(("resource_kind", "table"),),
        )
        for name in ("orders", "products", "categories")
    )
    context = replace(
        context,
        nodes=nodes + tables,
        edges=context.edges
        + (
            Edge("write", "snap", EdgeType.WRITES, "a", "orders", "writes", ("ev",)),
            Edge("products", "snap", EdgeType.READS, "c", "products", "reads", ("ev",)),
            Edge(
                "categories",
                "snap",
                EdgeType.READS,
                "c",
                "categories",
                "reads",
                ("ev",),
            ),
        ),
    )
    paths = (
        NarrativePath("writes", "outgoing", "a", ("write",)),
        NarrativePath("reads", "outgoing", "a", ("ab", "bc", "products")),
        NarrativePath("reads", "outgoing", "a", ("ab", "bc", "categories")),
    )
    answer, claims, citations = render_narrative(paths, context, language)
    assert "→" not in answer and "—" not in answer
    assert "- " not in answer
    assert len(answer.split("\n\n")) == 2
    assert len(claims) == 5 and len(citations) == 5
    if language == "vi":
        assert "checkout ghi trực tiếp dữ liệu vào bảng orders." in answer
        assert (
            "checkout đọc gián tiếp dữ liệu từ các bảng products và categories."
            in answer
        )
        assert "checkout gọi validate_quantities." in answer
        assert "validate_quantities gọi product_context." in answer
        assert (
            "product_context đọc dữ liệu từ các bảng products và categories." in answer
        )
    else:
        assert "checkout writes to table orders directly." in answer
        assert "checkout reads tables products and categories indirectly." in answer
        assert "checkout calls validate_quantities." in answer
        assert "validate_quantities calls product_context." in answer
    for claim in claims:
        assert claim["citation_indexes"]
        assert all(
            citations[i]["edge_id"] == claim["edge_id"]
            for i in claim["citation_indexes"]
        )


def test_incoming_indirect_calls_are_sentences_in_actual_call_order():
    from rkg.conversations.narrative import NarrativePath

    context = fixture()
    path = NarrativePath("calls", "incoming", "a", ("ca", "bc"))
    answer, claims, _ = render_narrative((path,), context, "vi")
    assert "a được gọi trực tiếp bởi c" in answer
    assert "c được gọi trực tiếp bởi b" in answer
    assert "b gọi gián tiếp a" in answer
    assert "a gọi b" not in answer and "→" not in answer
    assert {c["edge_id"] for c in claims} == {"ca", "bc"}
