---
key: TEST-RKG-UI-STRUCTURE
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-026
captured_at: 2026-09-29
captured_against:
  artifacts:
    - { key: TASK-RKG-026, revision: 2 }
    - { key: FR-RKG-003, revision: 8 }
    - { key: UIS-RKG-001, revision: 7 }
    - { key: NFR-RKG-UX-001, revision: 7 }
  code_tree: 516f17e+uncommitted-structure-view
  pins:
    node: "24.20.0"
    npm: "11.19.0"
command: cd frontend && npm run lint && npx tsc -b --pretty false && npm test
result: pass
---

# TEST-RKG-UI-STRUCTURE

Kiểm `AC-RKG-073` trên cây làm việc (mock client), HEAD `516f17e` cộng phần
Structure chưa commit:

- `npm run lint` — oxlint exit 0, chỉ warning. File mới có warning
  `set-state-in-effect` cùng kiểu với các trang đang fetch.
- `npx tsc -b --pretty false` — exit 0.
- `npm test` — 8 file, 35 test pass. Trong đó
  `structureTree.test.ts` chứng minh hai entity cùng `name` nhưng khác
  `qualified_name` không gộp nhánh, qualified name rỗng dùng `name`, và paging
  đi hết `total`. `ExplorerPage.test.tsx` chứng minh nhóm Graph / List /
  Structure chỉ một nút `aria-pressed`, ArrowRight bung nhánh, chọn lá mở
  heading detail đang có, rồi Graph và List trả canvas về chế độ cũ.

Không chạy live backend. Không kiểm click trên trình duyệt.
