# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/raw/policy_export_dirty.csv` | Batch CSV mỗi lần chạy `etl_pipeline.py run` | Duplicate chunk, thiếu `effective_date`, `doc_id` ngoài allowlist, timestamp không chuẩn | `raw_records`, `cleaned_records`, `quarantine_records`, `quarantine_rate = quarantine/raw` |
| `data/docs/*.txt` (canonical docs) | Canonical reference để đối chiếu nội dung policy trước publish | Nội dung stale (refund 14 ngày thay vì 7), xung đột version HR (10 vs 12 ngày phép) | expectation `no_stale_refund_window`, expectation `hr_leave_no_stale_10d_annual`, cảnh báo freshness |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | ID ổn định cho upsert idempotent vào Chroma |
| doc_id | string | Có | Khóa định danh tài liệu nguồn, phải thuộc allowlist |
| chunk_text | string | Có | Nội dung chunk để embed, không rỗng, độ dài tối thiểu theo rule |
| effective_date | date | Có | Định dạng ISO `YYYY-MM-DD` sau cleaning |
| exported_at | datetime | Có | Thời điểm export dùng cho freshness SLA |

---

## 3. Quy tắc quarantine vs drop

- Record vi phạm chất lượng nhưng vẫn cần truy vết sẽ chuyển vào `artifacts/quarantine/quarantine_<run_id>.csv`.
- Không drop im lặng trong ingest; mọi record không được publish phải được đếm vào `quarantine_records` và có lý do trong rule cleaning.
- Quyền approve merge lại dữ liệu quarantine: Ingestion Lead (P1) phối hợp Cleaning/Quality Owner sau khi xác nhận fix nguồn hoặc fix rule.

---

## 4. Phiên bản & canonical

- Source of truth cho refund window: `data/docs/policy_refund_v4.txt` (cửa sổ hoàn tiền 7 ngày).
- Source of truth cho HR leave policy: `data/docs/hr_leave_policy.txt` với cutoff hiệu lực từ `2026-01-01`.
- Mọi nội dung lệch canonical phải bị chặn ở expectation halt trước bước publish/embed.
