# Quality report — Lab Day 10 (nhóm)

**run_id:** `sprint3-clean` / `inject-bad` / `sprint3-restored`  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (inject-bad) | Sau (sprint3-restored) | Ghi chú |
|--------|-------------------|------------------------|---------|
| raw_records | 10 | 10 | Nhất quán qua các run |
| cleaned_records | 6 | 6 | Nhất quán qua các run |
| quarantine_records | 4 | 4 | Nhất quán qua các run |
| Expectation halt? | **CÓ** — `refund_no_stale_14d_window` FAIL (bypass bởi `--skip-validate`) | **Không** (8/8 pass) | sprint3-clean cũng 8/8 pass |

**Quarantine 4 records (nhất quán qua các run):**

| Lý do | Số lượng |
|-------|----------|
| `duplicate_chunk_text` (row 2 trùng row 1) | 1 |
| `missing_effective_date` (row 5 thiếu ngày) | 1 |
| `stale_hr_policy_effective_date` (row 7, date < 2026-01-01) | 1 |
| `unknown_doc_id` (row 9, `legacy_catalog_xyz_zzz` ngoài allowlist) | 1 |

---

## 2. Before / after retrieval (bắt buộc)

> Đính kèm hoặc dẫn link tới [`artifacts/eval/before_after_eval.csv`](../artifacts/eval/before_after_eval.csv) (hoặc 2 file before/after):
> [`artifacts/eval/after_inject_bad.csv`](../artifacts/eval/after_inject_bad.csv),
> [`artifacts/eval/restored_eval.csv`](../artifacts/eval/restored_eval.csv)

**Câu hỏi then chốt:** refund window (`q_refund_window`)

| Scenario | run_id | top1_preview (tóm tắt) | contains_expected | hits_forbidden |
|----------|--------|------------------------|-------------------|----------------|
| **Good state** | sprint3-clean | "...trong vòng **7 ngày làm việc** kể từ xác nhận đơn..." | yes | no |
| **Trước** (inject-bad) | inject-bad | "...trong vòng **14 ngày làm việc** kể từ xác nhận đơn..." | yes | **yes** |
| **Sau** (restored) | sprint3-restored | "...trong vòng **7 ngày làm việc** kể từ xác nhận đơn..." | yes | no |

**Trước:** `inject-bad` — `q_refund_window`: `hits_forbidden=yes`, chunk chứa "14 ngày làm việc" được upsert do `--no-refund-fix` bỏ qua rule fix  
**Sau:** `sprint3-restored` — `q_refund_window`: `hits_forbidden=no`, `embed_prune_removed=1` xác nhận chunk stale bị xóa và thay bằng bản đã fix

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, cột `top1_doc_expected`)

| Scenario | run_id | top1_doc_id | contains_expected | hits_forbidden | top1_doc_expected |
|----------|--------|-------------|-------------------|----------------|-------------------|
| **Good state** | sprint3-clean | hr_leave_policy | yes ("12 ngày phép năm") | no | yes |
| **Trước** (inject-bad) | inject-bad | hr_leave_policy | yes | no | yes |
| **Sau** (restored) | sprint3-restored | hr_leave_policy | yes | no | yes |

**Trước:** `inject-bad` — `q_leave_version` không bị ảnh hưởng vì inject chỉ tác động refund chunk, không tác động HR chunk  
**Sau:** `sprint3-restored` — `q_leave_version` pass nhất quán; pipeline quarantine row 7 (`effective_date < 2026-01-01`) → chỉ bản 2026 với "12 ngày phép năm" còn trong index

---

## 3. Freshness & monitor

> Kết quả `freshness_check` (PASS/WARN/FAIL) và giải thích SLA bạn chọn.

**Kết quả:** `FAIL` ở tất cả các run  
**Chi tiết:** `latest_exported_at = 2026-04-10T08:00:00`, `age_hours ≈ 121.8`, `sla_hours = 24`

**SLA đã chọn:** 24 giờ (mặc định, cấu hình qua env `FRESHNESS_SLA_HOURS`)

| Status | Điều kiện | Hành động cần làm |
|--------|-----------|-------------------|
| PASS | `age_hours ≤ sla_hours` | Không cần can thiệp |
| WARN | `sla_hours < age_hours ≤ 2 × sla_hours` (nếu có cấu hình warn threshold) | Alert, theo dõi |
| FAIL | `age_hours > sla_hours` | Trigger reingestion, notify owner |

**Giải thích:** FAIL là có chủ đích — dữ liệu mẫu có `exported_at = 2026-04-10`, cố tình đặt cũ ~5 ngày để chứng minh freshness check hoạt động và phát hiện được data stale. Đây không phải lỗi pipeline mà là bằng chứng observability hoạt động đúng.

---

## 4. Corruption inject (Sprint 3)

> Mô tả cố ý làm hỏng dữ liệu kiểu gì (duplicate / stale / sai format) và cách phát hiện.

**Loại corruption:** Stale policy chunk — giữ nguyên "14 ngày làm việc" thay vì fix thành "7 ngày làm việc"  
**Cách inject:** Chạy `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`

**Cơ chế chi tiết:**

1. `--no-refund-fix`: Rule 6 (`fix_refund_window`) trong `cleaning_rules.py` bị bỏ qua → chunk `policy_refund_v4` chứa "14 ngày làm việc" đi thẳng vào cleaned output
2. Expectation `refund_no_stale_14d_window` **FAIL** (halt) — hệ thống phát hiện đúng corruption
3. `--skip-validate`: Bypass expectation halt → pipeline tiếp tục embed chunk sai lên Chroma
4. `embed_prune_removed=1`: Chunk đúng (SHA256 của text "7 ngày") bị xóa khỏi index, thay bằng chunk sai (SHA256 khác của text "14 ngày")

**Cách phát hiện:**

| Cơ chế | Kết quả |
|--------|---------|
| Expectation `refund_no_stale_14d_window` | FAIL, `violations=1` — phát hiện tại bước validate |
| `manifest_inject-bad.json`: `skipped_validate: true` | Audit trail ghi lại hành động bypass |
| `eval_retrieval.py` → `after_inject_bad.csv` | `q_refund_window`: `hits_forbidden=yes` — phát hiện tại bước retrieval |

**Recovery:** Chạy lại `python etl_pipeline.py run --run-id sprint3-restored` (không có flag inject) → `embed_prune_removed=1`, chunk "14 ngày" bị prune, chunk "7 ngày" được upsert lại, `expectation[refund_no_stale_14d_window] OK`.

---

## 5. Hạn chế & việc chưa làm

- **Freshness FAIL không được giải quyết:** Dữ liệu mẫu cố ý cũ để demo monitoring. Trong thực tế cần trigger reingestion từ source.
- **Log file encoding:** Pipeline gặp lỗi `UnicodeEncodeError` trên Windows console (cp1252 không nhận ký tự `→`) khi chạy `--skip-validate`. Workaround: `PYTHONIOENCODING=utf-8`. Cần fix vĩnh viễn trong `etl_pipeline.py` (ví dụ dùng ASCII arrow `->` hoặc set stdout encoding).
- **Điểm đánh giá Grading:** Sinh viên Trịnh Đức Ân chạy thành công `grading_run.py`, ghi nhận kết quả đánh giá 3/3 câu đạt chuẩn đánh giá JSONL với tiêu chí `hits_forbidden=false` thành công, lưu log vào `artifacts/eval/grading_run.jsonl`.
- **Inject chỉ test một loại corruption:** Chỉ kiểm tra stale refund window. Các loại khác (duplicate inject, BOM, sai format date) chưa được test tự động trong eval.
- **Merit `q_leave_version` pass nhất quán:** Vì inject không ảnh hưởng HR chunk. Để test version conflict HR một cách có chủ đích, cần thêm kịch bản inject stale HR date riêng.
