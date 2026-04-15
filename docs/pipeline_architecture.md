# Kiến trúc pipeline — Lab Day 10

**Nhóm:** A20-E403-Nhom30  
**Cập nhật:** 2026-04-15

---

## 1. Sơ đồ luồng (bắt buộc có 1 diagram: Mermaid / ASCII)

```
raw export (CSV/API/…)  →  [run_id log] clean  →  validate (expectations)  →  embed (Chroma)  →  serving (Day 08/09)
                              ↓
                         quarantine (fail rows)
                              ↓
                         [freshness check on manifests]
```

> Vẽ thêm: điểm đo **freshness** (sau validate, trên manifests), chỗ ghi **run_id** (trong logs và manifests), và file **quarantine** (output từ clean stage).

---

## 2. Ranh giới trách nhiệm

| Thành phần | Input | Output | Owner nhóm |
|------------|-------|--------|--------------|
| Ingest | Raw CSV (data/raw/policy_export_dirty.csv) | Raw rows (dicts) | A20-E403-Nhom30 |
| Transform | Raw rows | Cleaned CSV (artifacts/cleaned/) + Quarantine CSV (artifacts/quarantine/) | A20-E403-Nhom30 |
| Quality | Cleaned rows | Expectations pass/fail (logs) | A20-E403-Nhom30 |
| Embed | Cleaned rows | Vector embeddings in Chroma | A20-E403-Nhom30 |
| Monitor | Manifests (artifacts/manifests/) | Freshness alerts (group-report-and-runbook) | A20-E403-Nhom30 |

---

## 3. Idempotency & rerun

> Mô tả: Upsert theo `chunk_id` (stable hash từ doc_id + chunk_text + seq). Rerun 2 lần không tạo duplicate vector vì chunk_id ổn định và idempotent.

---

## 4. Liên hệ Day 09

> Pipeline này cung cấp / làm mới corpus từ `data/docs/` (cùng thư mục với day09/lab) cho retrieval, thông qua export cleaned chunks vào vector store Chroma.

---

## 5. Rủi ro đã biết

- Duplicate chunk_text (severity: warn).
- Stale refund window (14 ngày thay vì 7, severity: halt).
- Invalid effective_date (không parse được ISO hoặc DMY).
- Doc_id không trong allowlist (quarantine).
