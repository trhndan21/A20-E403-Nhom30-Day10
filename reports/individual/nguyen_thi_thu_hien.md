# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Thị Thu Hiền  
**Vai trò:** Ops Lead (Sprint 4 — P4)  
**Ngày nộp:** 2026-04-15  

---

## 1. Tôi phụ trách phần nào?

**File / module:**

- `monitoring/freshness_check.py` — Chịu trách nhiệm xây dựng logic kiểm tra độ tươi của dữ liệu (Data Freshness) dựa trên thời gian thực tế so với SLA trong Data Contract.
- `docs/runbook.md` — Soạn thảo cẩm nang vận hành, hướng dẫn các bước xử lý sự cố (Recovery) khi pipeline gặp lỗi hoặc dữ liệu bị quá hạn.
- `docs/pipeline_architecture.md` — Vẽ và mô tả sơ đồ kiến trúc hệ thống, luồng di chuyển của dữ liệu từ Raw -> Clean -> Embed.
- `docs/data_contract.md` — Hoàn thiện tài liệu hợp đồng dữ liệu, quy định về SLA và các nguồn dữ liệu chuẩn (Canonical sources).

**Kết nối với thành viên khác:**

Tôi đóng vai trò là "người gác cổng" cuối cùng để đảm bảo hệ thống vận hành ổn định. Tôi sử dụng các file `manifest.json` được tạo ra từ công việc của **Hiển (P1)** và **Hậu (P2)** để đo lường hiệu suất. Khi **Dương (P3)** thực hiện kịch bản "Inject corruption", tôi phối hợp để ghi nhận các cảnh báo trong báo cáo chất lượng và cập nhật vào Runbook các bước để khôi phục trạng thái sạch (Restore).

**Bằng chứng:**

- `artifacts/manifests/manifest_sprint4-fresh.json` — Manifest xác nhận dữ liệu đạt chuẩn SLA.
- `artifacts/logs/freshness_check.log` — Nhật ký quét và kiểm tra SLA của hệ thống.
- `docs/data_contract.yaml` — File cấu hình đã được cập nhật thông tin về Owner và SLA 24h.

---

## 2. Một quyết định kỹ thuật

Tôi chọn **sử dụng file Manifest làm "Single Source of Truth" (Nguồn tin cậy duy nhất)** cho việc kiểm tra Freshness thay vì truy vấn trực tiếp vào cơ sở dữ liệu Vector (ChromaDB).

**Lý do:** Trong một hệ thống quan sát (Observability) chuẩn, chúng ta cần tách biệt giữa dữ liệu lưu trữ và siêu dữ liệu (Metadata) về phiên bản chạy. Việc đọc trực tiếp từ Manifest giúp tôi biết chính xác bản ghi đó thuộc về `run_id` nào, được sinh ra lúc nào mà không cần kết nối vào database, giúp tăng tốc độ kiểm tra và giảm thiểu rủi ro làm treo database khi hệ thống mở rộng.

Quyết định thứ hai là **thiết lập cơ chế cảnh báo 3 tầng (PASS/WARN/FAIL)** trong Runbook:
- **PASS (< 12h):** Dữ liệu hoàn toàn mới.
- **WARN (12h - 24h):** Dữ liệu sắp hết hạn, nhắc nhở team chạy lại pipeline.
- **FAIL (> 24h):** Vi phạm SLA, hệ thống cần được kiểm tra ngay lập tức.

---

## 3. Một lỗi hoặc anomaly đã xử lý

**Triệu chứng:** Khi chạy module freshness check, hệ thống báo lỗi xung đột định dạng thời gian:
```text
ValueError: time data '2026-04-15 14:30:00' does not match format '%Y-%m-%dT%H:%M:%S'