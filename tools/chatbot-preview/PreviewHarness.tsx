import { useLocation, useNavigate } from 'react-router-dom'
import { previewCases } from './previewClient'

export function PreviewHarness() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  return <aside className="preview-harness" aria-label="Điều khiển bản xem trước">
    <details>
    <summary>Bản xem trước · dữ liệu mẫu · chọn tình huống</summary>
    <p>Dùng màn hình Ask hiện có. Không gọi API/LLM. Nội dung bạn nhập chỉ ở bộ nhớ; tải lại sẽ trở về dữ liệu mẫu.</p>
    <label htmlFor="preview-case">Tình huống cần xem</label>
    <select id="preview-case" value={pathname.split('/').at(-1)?.replace('preview-', '') ?? 'answer'} onChange={(e) => navigate(`/conversations/preview-${e.target.value}`)}>
      {previewCases.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
    </select>
    <p className="hint">Đổi sáng/tối và Việt/Anh bằng nút có sẵn. Chọn “LLM chưa cấu hình”, “Quá thời gian” hoặc “Xung đột” rồi nhập câu hỏi và bấm Gửi để thử giữ bản nháp.</p>
    </details>
  </aside>
}
