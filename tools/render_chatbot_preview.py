#!/usr/bin/env python3
"""Materialize existing Ask into an isolated fixture-only UX preview.

Never modifies product source or reads .env. Normative baseline hashes are verified
before generation. Test/build commands are run separately against the fresh stage.
"""

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "tools/chatbot-preview"
BASELINE = (
    ROOT
    / ".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline"
    / "BL-CHG-RKG-2026-002-r5.yaml"
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(
            "Preview source anchor changed; inspect source before regenerating"
        )
    return text.replace(old, new, 1)


def materialize():
    baseline = json.loads(BASELINE.read_text())
    for pin in baseline["artifacts"]:
        if digest(ROOT / ".aide" / pin["path"]) != pin["hash"]:
            raise ValueError(f"Baseline mismatch: {pin['key']}")
    stage = Path(tempfile.mkdtemp(prefix="rkg-chatbot-preview-"))
    frontend = ROOT / "frontend"
    inputs = [
        p
        for p in frontend.rglob("*")
        if p.is_file()
        and not set(p.relative_to(frontend).parts) & {"node_modules", "dist", ".git"}
        and not p.name.startswith(".env")
        and not p.name.endswith((".local", ".tsbuildinfo"))
    ]
    for path in inputs:
        dest = stage / path.relative_to(frontend)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    (stage / "node_modules").symlink_to(
        frontend / "node_modules", target_is_directory=True
    )
    for asset in ASSETS.glob("*"):
        if asset.suffix not in {".tsx", ".ts", ".css"}:
            continue
        dest = stage / "src/preview" / asset.name
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(asset, dest)
    (
        stage / "src/client/index.ts"
    ).write_text("""import { createPreviewClient } from '../preview/previewClient'
import type { RkgClient } from './mock/mockClient'
export type { RkgClient } from './mock/mockClient'
let client: RkgClient | null = null
export function getRkgClient(): RkgClient { return client ??= createPreviewClient() }
export function getClientMode(): 'mock' | 'live' { return 'mock' }
""")
    (stage / "vite.config.ts").write_text("""import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
export default defineConfig({ plugins: [react()], base: './',
  envDir: './isolated-preview-env',
  server: { host: '127.0.0.1', port: 5174, strictPort: true },
  preview: { host: '127.0.0.1', port: 5174, strictPort: true } })
""")
    app = stage / "src/App.tsx"
    text = app.read_text().replace("BrowserRouter", "HashRouter")
    text = (
        "import { useParams } from 'react-router-dom'\n"
        "import './preview/preview.css'\n" + text
    )
    text += (
        "\nfunction PreviewConversation() {\n"
        "  const { conversationId } = useParams();\n"
        "  return <ConversationPage key={conversationId} />\n}\n"
    )
    text = replace_once(
        text,
        'path="conversations/:conversationId" element={<ConversationPage />}',
        'path="conversations/:conversationId" element={<PreviewConversation />}',
    )
    text = replace_once(
        text,
        '<Route index element={<Navigate to="/repositories" replace />} />',
        "<Route index element={<Navigate "
        'to="/conversations/preview-answer" replace />} />',
    )
    app.write_text(text)
    shell = stage / "src/components/shell/AppShell.tsx"
    shell_text = (
        "import { PreviewHarness } from '../../preview/PreviewHarness'\n"
        + shell.read_text()
    )
    shell_text = replace_once(
        shell_text,
        '<div className="app-main">',
        '<div className="app-main">\n        <PreviewHarness />',
    )
    shell_text = replace_once(
        shell_text,
        '<a className="skip-link" href="#main">',
        '<a className="skip-link" href="#main" '
        "onClick={(e) => { e.preventDefault(); "
        "document.getElementById('main')?.focus() }}>",
    )
    shell.write_text(shell_text)
    page = stage / "src/pages/conversations/ConversationPage.tsx"
    text = page.read_text()
    text = (
        "import { PreviewReply } from '../../preview/PreviewReply'\n"
        "import { candidateLabel, exactEvidence, focusLabel }\n"
        "  from '../../preview/previewClient'\n" + text
    )
    start = text.index("interface TurnFlags {")
    end = text.index("export function ConversationPage()", start)
    text = text[:start] + text[end:]
    text = replace_once(
        text,
        "  const [flags, setFlags] = useState<Record<string, TurnFlags>>({})\n",
        "",
    )
    start = text.index("    setFlags((current) => ({")
    end = text.index("    setQuestion('')", start)
    text = text[:start] + text[end:]
    start = text.index("              {turn.answer ||")
    end = text.index("\n            </li>", start)
    text = (
        text[:start]
        + "              <PreviewReply turn={turn} unavailable={unavailable} "
        "openCitation={(item) => void openCitation(item)} />" + text[end:]
    )
    text = replace_once(
        text, "setEvidence(detail)", "setEvidence(exactEvidence(detail, item))"
    )
    text = replace_once(text, "shortId(focusId, 18)", "focusLabel(focusId)")
    # Keep successful transcript visible for an unavailable snapshot in this prototype.
    text = replace_once(
        text,
        "setUnavailable(false)",
        "setUnavailable(conversationId === 'preview-unavailable')",
    )
    text = replace_once(
        text,
        "      const message = messageFor(err, t, locale)",
        "      if (err instanceof RkgApiError && "
        "[502, 503, 504].includes(err.status)) await load()\n"
        "      const message = messageFor(err, t, locale)",
    )
    text = replace_once(
        text,
        "      if (err instanceof RkgApiError && "
        "[502, 503, 504].includes(err.status)) {\n"
        "        await load()\n      }\n",
        "",
    )
    text = re.sub(
        r"t\('ask.chooseCandidate', \{\s*n: index \+ 1,\s*type: item.type,"
        r"\s*name: item.qualified_name,\s*\}\)",
        "candidateLabel(item.id, index + 1, locale)",
        text,
    )
    text = replace_once(
        text,
        "{t('ask.clarification')}",
        "{locale === 'vi' ? 'Bạn đang hỏi mục nào?' : 'Which item do you mean?'}",
    )
    text = replace_once(
        text,
        "<p>{t('ask.questionPlaceholder')}</p>",
        "<p>{locale === 'vi' ? 'Bạn có thể hỏi endpoint gọi hàm nào, "
        "hàm đọc/ghi bảng nào hoặc phát sự kiện nào. Ví dụ: "
        "GET /orders/{id} gọi những hàm nào?' : "
        "'Ask which functions an endpoint calls, which tables a function "
        "reads or writes, or which events it emits. Try: "
        "Which functions does GET /orders/{id} call?'}</p>",
    )
    text = replace_once(
        text,
        "        {evidenceError ? <p>{evidenceError}</p> : null}",
        "        <p>{t('ask.pinned', { id: shortId(pinnedSnapshot, 14) })}</p>\n"
        "        {!evidence && !evidenceError ? "
        "<p role=\"status\">{t('common.loading')}</p> : null}\n"
        "        {evidenceError ? <p>{evidenceError}</p> : null}",
    )
    text = replace_once(
        text,
        '      {unavailable ? (\n        <p className="ask-note">',
        '      {unavailable ? (\n        <p className="ask-note">\n'
        "          {t('ask.snapshotUnavailable')} {' '}",
    )
    page.write_text(text)
    manifest = {
        "key": "UIM-RKG-002",
        "baseline": baseline["key"],
        "non_normative": True,
        "fixture_only": True,
        "implementation_ready": False,
        "baseline_sha256": digest(BASELINE),
        "inputs": {str(p.relative_to(ROOT)): digest(p) for p in sorted(inputs)},
        "generator": {
            "path": "tools/render_chatbot_preview.py",
            "sha256": digest(Path(__file__)),
        },
        "assets": {
            str(p.relative_to(ROOT)): digest(p)
            for p in sorted(ASSETS.glob("*"))
            if p.is_file()
        },
        "derived_from": [
            pin
            for pin in baseline["artifacts"]
            if pin["key"]
            in {"UXF-RKG-002", "SCR-RKG-001", "UID-RKG-001", "TOK-RKG-001"}
        ],
        "token_file": {
            "path": ".aide/design/ui/tokens/tokens.json",
            "sha256": digest(ROOT / ".aide/design/ui/tokens/tokens.json"),
        },
        "materialized_inputs": {
            str(p.relative_to(stage)): digest(p)
            for p in sorted(
                list((stage / "src").rglob("*"))
                + [
                    stage / "vite.config.ts",
                    stage / "package.json",
                    stage / "package-lock.json",
                    stage / "index.html",
                ]
            )
            if p.is_file()
        },
        "checks": {
            "real_browser": "not_run",
            "device_walkthrough": "not_run",
            "live_provider": "not_run",
            "backend_grounding": "not_run",
        },
        "limits": [
            "Private synthetic evidence/coverage annotations; no public wire binding.",
            "No server persistence; reload resets fixtures.",
            "Author component checks are not independent review.",
        ],
    }
    (stage / "preview-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    return stage


def publish(stage):
    manifest = json.loads((stage / "preview-manifest.json").read_text())
    if digest(BASELINE) != manifest["baseline_sha256"]:
        raise ValueError("Preview baseline changed")
    for pin in json.loads(BASELINE.read_text())["artifacts"]:
        if digest(ROOT / ".aide" / pin["path"]) != pin["hash"]:
            raise ValueError(f"Baseline mismatch: {pin['key']}")
    # Fail rather than publish a bundle from inputs edited since materialization.
    pins = dict(manifest["inputs"]) | dict(manifest["assets"])
    pins[manifest["generator"]["path"]] = manifest["generator"]["sha256"]
    for path, expected in pins.items():
        if digest(ROOT / path) != expected:
            raise ValueError(f"Preview input changed: {path}")
    for path, expected in manifest["materialized_inputs"].items():
        if digest(stage / path) != expected:
            raise ValueError(f"Materialized source changed: {path}")
    out = ROOT / ".aide/generated/ui-mocks/chatbot-002"
    if out.exists():
        raise ValueError(
            "Existing generated preview preserved; choose a new output revision"
        )
    out.mkdir(parents=True)
    shutil.copytree(stage / "dist", out / "app")
    manifest["bundle"] = {
        str(p.relative_to(out)): digest(p)
        for p in sorted((out / "app").rglob("*"))
        if p.is_file()
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    (out / "UIM-RKG-002.md").write_text("""---
key: UIM-RKG-002
type: ui-mock
group: derived
revision: 1
non_normative: true
change_set: CHG-RKG-2026-002
derived_from: [UXF-RKG-002, SCR-RKG-001, UID-RKG-001, TOK-RKG-001]
classification: internal
ai_assisted: true
---
# UIM-RKG-002 — Preview trên Ask hiện có

Khi preview và UXF/SCR/UID bất đồng, UXF/SCR/UID thắng.

Sinh bằng `tools/render_chatbot_preview.py`; không chỉnh generated bằng tay.
Revision, byte hashes của nguồn, generator, token và bundle nằm trong `manifest.json`.
Tái sử dụng AppShell/ConversationPage/Button/dialog/locale/theme/font/token thật.
Fixture client và presentation là prototype trong staging; product source không đổi.

Chạy static preview trên loopback bằng lệnh ở README của tool. Mở
`http://127.0.0.1:5174/#/conversations/preview-answer`.

Walkthrough: đọc answer direct/indirect; mở/đóng nguồn bằng keyboard; chọn entity
để tiếp tục ý định ban đầu; xem insufficient/partial/legacy/greeting/empty;
thử Gửi trong disabled/timeout/conflict để kiểm tra draft/pending; xem unavailable.
Đổi sáng/tối, Việt/Anh và kiểm tra chuỗi dài trên thiết bị chính thật.

Các flag/evidence ở đây dùng private synthetic catalog, không chứng minh public API
binding, server persistence, resolver hay LLM đã được triển khai. Reload seed lại
fixture; các câu nhập thêm chỉ ở memory. Không có model/API call.
Real browser, device, live-provider và independent UI review chưa chạy.
UI/UX Gate vẫn pending; chỉ ký UXF r5, SCR r9, UID r8 sau đủ walkthrough/evidence.
""")
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-stage", type=Path)
    args = parser.parse_args()
    if args.publish_stage:
        publish(args.publish_stage)
    else:
        print(materialize())
