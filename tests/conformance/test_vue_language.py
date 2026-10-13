"""Focused conformance for the Vue SFC language adapter.

Oracle intent follows repo-test/rkg-fixture-nuxt4 README Vue SFC inventory
(language facts only). No Nuxt routing / Nitro / BullMQ. Pattern mirrors
TEST-RKG-ADAPTER-CONFORMANCE style of typescript/java language tests.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rkg.adapters import AdapterContext
from rkg.domain import EdgeType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_VUE_PATTERNS = ("*.vue", "**/*.vue")
_IGNORE = (
    "**/node_modules/**",
    "**/.nuxt/**",
    "**/.output/**",
    "**/dist/**",
    "**/coverage/**",
)
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _vue_adapter():
    from rkg.adapters.vue_language import VueLanguageAdapter

    return VueLanguageAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 65536, _VUE_PATTERNS, _IGNORE)
    manifest = build_manifest(
        resolve_local_source("repo-vue", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-vue", "snap-vue", "job-vue", config)
    adapter = _vue_adapter()
    assert adapter.detect(manifest).technologies
    parsed = adapter.parse(manifest, config)
    extracted = adapter.extract(context, parsed)
    resolved = adapter.resolve(context, parsed, extracted.facts)
    validate_fact_batch(resolved.facts)
    return adapter, manifest, config, context, parsed, resolved


def _names(resolved) -> set[str]:
    return {item.qualified_name for item in resolved.facts.entities}


def _edge_pairs(resolved, edge_type: EdgeType) -> set[tuple[str, str]]:
    by_id = {item.id: item for item in resolved.facts.entities}
    return {
        (by_id[edge.source_id].qualified_name, by_id[edge.target_id].qualified_name)
        for edge in resolved.facts.edges
        if edge.type == edge_type and edge.source_id in by_id
    }


def _rendered(resolved) -> str:
    payload = {
        "entities": [asdict(item) for item in resolved.facts.entities],
        "edges": [asdict(item) for item in resolved.facts.edges],
        "evidence": [asdict(item) for item in resolved.facts.evidence],
        "diagnostics": [asdict(item) for item in resolved.facts.diagnostics],
        "adapter_diagnostics": [asdict(item) for item in resolved.diagnostics],
    }
    return json.dumps(payload)


def test_descriptor_contract() -> None:
    adapter = _vue_adapter()
    assert adapter.descriptor.adapter_id == "rkg.vue"
    assert adapter.descriptor.kind.value == "language"
    assert adapter.descriptor.language == "vue"
    assert "structure" in adapter.descriptor.capabilities
    assert "imports" in adapter.descriptor.capabilities
    assert "calls" in adapter.descriptor.capabilities
    assert "classes" in adapter.descriptor.capabilities
    assert "metadata" in adapter.descriptor.capabilities


def test_sfc_source_unit_keeps_structured_sections(tmp_path: Path) -> None:
    """One .vue file → one SourceUnit; template/script/style stay on the unit."""
    _write(
        tmp_path,
        "app/components/OrderStatusBadge.vue",
        """
<script setup lang="ts">
import type { OrderStatus } from '#shared/types/order'
defineProps<{ status: OrderStatus }>()
</script>
<template>
  <span class="badge">{{ status }}</span>
</template>
<style scoped>
.badge { padding: 0.15rem 0.5rem; }
</style>
""".strip(),
    )
    _, _, _, _, parsed, resolved = _run(tmp_path)
    assert len(parsed.units) == 1
    unit = parsed.units[0]
    assert unit.language == "vue"
    sfc = unit.representation
    assert sfc.template is not None
    assert sfc.scripts and sfc.scripts[0].is_setup
    assert sfc.styles and sfc.styles[0].is_scoped
    names = _names(resolved)
    assert "app.components.OrderStatusBadge" in names
    # Must not fabricate sibling .ts / .css SourceUnits.
    assert not any(name.endswith(".ts") for name in names)
    source = next(
        item
        for item in resolved.facts.entities
        if item.qualified_name == "app.components.OrderStatusBadge"
    )
    attrs = dict(source.attributes)
    assert attrs.get("has_template") == "true"
    assert attrs.get("script_setup") == "true"
    assert attrs.get("has_style") == "true"


def test_define_component_type_callable_and_explicit_import(tmp_path: Path) -> None:
    """defineComponent + setup callable + explicit child .vue import."""
    _write(
        tmp_path,
        "app/components/OrderStatusBadge.vue",
        """
<script setup lang="ts">
defineProps<{ status: string }>()
</script>
<template><span>{{ status }}</span></template>
""".strip(),
    )
    _write(
        tmp_path,
        "app/components/OrderCard.vue",
        """
<script lang="ts">
import { defineComponent } from 'vue'
import OrderStatusBadge from './OrderStatusBadge.vue'

export default defineComponent({
  name: 'OrderCard',
  components: { OrderStatusBadge },
  setup(props, { emit }) {
    const requestCancellation = () => emit('cancel', 'id')
    return { requestCancellation }
  },
})
</script>
<template>
  <article>
    <OrderStatusBadge status="open" />
    <button type="button" @click="requestCancellation">Cancel</button>
  </article>
</template>
<style scoped>
article { padding: 1rem; }
</style>
""".strip(),
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    names = _names(resolved)
    assert "app.components.OrderCard" in names
    assert "app.components.OrderCard.OrderCard" in names
    assert "app.components.OrderCard.OrderCard.requestCancellation" in names
    imports = _edge_pairs(resolved, EdgeType.IMPORTS)
    assert any(
        src.endswith("OrderCard") and "OrderStatusBadge" in tgt for src, tgt in imports
    ), imports
    assert all(edge.evidence_ids for edge in resolved.facts.edges)


def test_script_setup_callable_and_internal_call(tmp_path: Path) -> None:
    """script setup emits Callables; unique internal calls resolve."""
    _write(
        tmp_path,
        "app/pages/orders/index.vue",
        """
<script setup lang="ts">
async function reload() {}
async function cancelOrder() {
  await reload()
}
await cancelOrder()
</script>
<template><section /></template>
""".strip(),
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    names = _names(resolved)
    assert "app.pages.orders.index" in names
    assert "app.pages.orders.index.reload" in names
    assert "app.pages.orders.index.cancelOrder" in names
    calls = _edge_pairs(resolved, EdgeType.CALLS)
    assert (
        "app.pages.orders.index.cancelOrder",
        "app.pages.orders.index.reload",
    ) in calls


def test_ignored_generated_trees_are_skipped(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/app.vue",
        "<template><div /></template>\n",
    )
    _write(
        tmp_path,
        ".nuxt/generated.vue",
        "<template><div>generated</div></template>\n",
    )
    _write(
        tmp_path,
        "node_modules/lib/Widget.vue",
        "<template><div /></template>\n",
    )
    _write(
        tmp_path,
        "dist/bundle.vue",
        "<template><div /></template>\n",
    )
    _, _, _, _, parsed, resolved = _run(tmp_path)
    paths = {unit.relative_path for unit in parsed.units}
    assert paths == {"app/app.vue"}
    names = _names(resolved)
    assert "app.app" in names
    assert not any(".nuxt" in name for name in names)


def test_syntax_error_is_isolated_with_relative_path(tmp_path: Path) -> None:
    """AC-RKG-035 — bad sibling diagnostic; valid SFC still extracts."""
    _write(
        tmp_path,
        "app/components/GoodBadge.vue",
        """
<script setup lang="ts">
const label = 'ok'
</script>
<template><span>{{ label }}</span></template>
""".strip(),
    )
    # Mirrors BrokenPanel.vue.fixture malformed script.
    _write(
        tmp_path,
        "app/components/BrokenPanel.vue",
        """
<script setup lang="ts">
const broken = {
</script>
<template><div>{{ broken }}</div></template>
""".strip(),
    )
    _, _, _, _, parsed, resolved = _run(tmp_path)
    assert any(
        unit.relative_path == "app/components/GoodBadge.vue" for unit in parsed.units
    )
    assert not any(
        unit.relative_path == "app/components/BrokenPanel.vue" for unit in parsed.units
    )
    diag = [
        (item.code, item.relative_path, item.line)
        for item in parsed.diagnostics
        if item.relative_path
    ]
    assert any(
        path == "app/components/BrokenPanel.vue" and line is not None
        for _, path, line in diag
    ), diag
    assert "app.components.GoodBadge" in _names(resolved)
    assert str(tmp_path) not in repr(resolved)
    assert str(tmp_path) not in _rendered(resolved)


def test_nuxt_hash_alias_is_not_guessed_as_es_import(tmp_path: Path) -> None:
    """AC-RKG-006 — `#shared/...` stays unresolved; no invented ES import edge."""
    _write(
        tmp_path,
        "app/components/OrderCard.vue",
        """
<script setup lang="ts">
import type { Order } from '#shared/types/order'
const label = 'x'
</script>
<template><div>{{ label }}</div></template>
""".strip(),
    )
    _write(
        tmp_path,
        "shared/types/order.ts",
        "export type Order = { id: string }\n",
    )
    _, _, _, _, parsed, resolved = _run(tmp_path)
    imports = _edge_pairs(resolved, EdgeType.IMPORTS)
    assert not any("order" in tgt.lower() for _, tgt in imports if "shared" in tgt)
    # type-only `#` import should not invent a SourceUnit import edge.
    assert not any("OrderCard" in src and "order" in tgt for src, tgt in imports)


def test_secret_sentinel_is_not_persisted(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/components/Note.vue",
        f"""
<script setup lang="ts">
const fixtureNote = '{_SECRET}'
</script>
<template><p>{{{{ fixtureNote }}}}</p></template>
""".strip(),
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    assert _SECRET not in _rendered(resolved)
    assert _SECRET not in repr(resolved)


def test_builtin_registration() -> None:
    from rkg.adapters.builtins import builtin_adapters

    ids = {adapter.descriptor.adapter_id for adapter in builtin_adapters()}
    assert "rkg.vue" in ids
