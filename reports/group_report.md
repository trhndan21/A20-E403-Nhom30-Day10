# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** A20-E403-Nhom30  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Trịnh Đức Ân | Architect & Auditor (P5) | trinhducan@example.com |
| Hồ Quang Hiển | Ingestion / Raw Owner | hienhq@example.com |
| Lương Thanh Hậu | Cleaning & Quality Owner | hault@example.com |
| Tạ Thị Thuỳ Dương | Embed & Idempotency Owner, Monitoring / Docs Owner | duongttt@example.com |

**Ngày nộp:** 2026-04-15  
**Repo:** A20-E403-Nhom30-Day10-qh  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

Phần Sprint 1 do Ingestion Lead (Hồ Quang Hiển) phụ trách tập trung vào ingest dữ liệu thô, chuẩn hóa đầu ra log và chốt schema/source map để bàn giao cho Sprint 2. Nhóm ingest file `data/raw/policy_export_dirty.csv` qua lệnh `etl_pipeline.py run --run-id sprint1`, sau đó ghi nhận đầy đủ các chỉ số bắt buộc trong log: `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`. Kết quả cho thấy pipeline đã tách được 4 dòng lỗi vào quarantine và publish 6 dòng cleaned để chuẩn bị cho bước validate + embed. Manifest được tạo tại `artifacts/manifests/manifest_sprint1.json` và log tại `artifacts/logs/run_sprint1.log`, đảm bảo truy vết theo `run_id=sprint1`. Ở lần chạy này, freshness trả về FAIL vì `latest_exported_at` cũ hơn SLA 24h; đây là tín hiệu monitoring mong đợi, không phải lỗi vỡ pipeline vì run vẫn kết thúc `PIPELINE_OK`.

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

`python etl_pipeline.py run --run-id sprint1`

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| Chặn chunk quá ngắn (`low_information_chunk`) | `quarantine` baseline | Nhận diện & loại chunk rác | `artifacts/quarantine/quarantine_sprint3-clean.csv` |
| Bỏ migration note (`_REFUND_MIGRATION_NOTE`) | `no_canonical_text_duplicates` fail | duplicate canonical = 0 (pass) | Report cá nhân của Lương Thanh Hậu |
| Dedupe canonical (`duplicate_chunk_after_transform`) | `duplicate_chunk_after_transform` cao | Lọc nhiễu duplicate canonical=0 | `artifacts/quarantine/quarantine_sprint3-clean.csv` |
| Bắt buộc `chunk_id` duy nhất (E7 mới) | Không kiểm soát ID trùng | `duplicate_ids=0` (OK) | `artifacts/logs/run_sprint3-clean.log` |
| Chặn Canonical copy (E8 mới) | `should_halt=True` khi inject dup | `should_halt=False` lúc clean | `artifacts/logs/run_sprint3-clean.log` |

**Rule chính (baseline + mở rộng):**

Phần này Lương Thanh Hậu (Cleaning/Quality Owner) đã xử lý ở Sprint 2. Bao gồm các rule chống duplicate dựa trên Canonical Hash, filter `low_information_chunk` (dài dưới 20 char norm) và xoá migration note.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Khi chưa xử lý xoá string `(ghi chú: ... )`, `E8: no_canonical_text_duplicates` báo FAIL vì các chunk policy refund gần giống hệ thống (near duplicate). Tôi đã bổ sung Regex remove migration note vào cleaning rule, sau đó eval canonical lại thì số liệu duplicate về 0, Expectation PASS.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Tôi (Tạ Thị Thuỳ Dương) đã chạy lệnh `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate` để cố ý bỏ qua bước fix lỗi policy refund 14 ngày về 7 ngày. Việc thêm cờ `--skip-validate` giúp tránh bị `pipeline exit` ngay khi expectation fail, từ đó lưu lại được vector sai (chứa "14 ngày") vào Chroma.

**Kết quả định lượng (từ CSV / bảng):**

- Ở trạng thái bình thường (`sprint3-clean`), `hits_forbidden` của `q_refund_window` là `no` (chunk kết quả chứa "7 ngày làm việc").
- Tại run `inject-bad`, `hits_forbidden` thay đổi thành `yes` (chunk chứa "14 ngày làm việc" lọt vào top-k retrieval do rule fix đã bypass).
- Ở run phục hồi `sprint3-restored`, expectation `refund_no_stale_14d_window` PASS và `hits_forbidden` quay lại `no`. Dòng log `embed_prune_removed=1` xác nhận chunk sai đã bị hệ thống thu hồi và prune khỏi index. Mọi thông tin đã được ghi nhận ở file `before_after_eval.csv` và report cá nhân eval.

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

Trong run Sprint 1 (`run_id=sprint1`), manifest ghi `latest_exported_at=2026-04-10T08:00:00` và freshness check trả `FAIL` do `age_hours=121.047` vượt `sla_hours=24.0`. Đây là tín hiệu đúng cho lớp observability vì dữ liệu demo đã cũ hơn ngưỡng SLA đã cấu hình. Điểm quan trọng ở Sprint 1 là phân biệt rõ hai trạng thái: (1) pipeline kỹ thuật chạy thành công (`PIPELINE_OK`) và (2) chất lượng/độ tươi dữ liệu có cảnh báo để owner xử lý theo runbook. Nhóm sẽ dùng kết quả này làm đầu vào cho phần monitoring docs ở Sprint 4.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

Dữ liệu sau embed được sử dụng làm vector knowledge base. Việc làm Pipeline này là tối quan trọng nhằm chắc chắn dữ liệu đưa vào Day 09 RAG agents đã chuẩn hóa (thời gian hiệu lực đúng theo cutoff 2026, loại bỏ "14 ngày" stale refund window đổi thành 7 ngày, block duplicates). Nếu Agent Day 09 trỏ vào đúng collection do Day 10 quản lý, kết quả RAG không còn bị Hallucination từ version lỗi. Việc upsert Idempotency với unique `chunk_id` có sẵn tránh hiện tượng Agent bị ngập lụt context duplicate khi run Data Pipeline nhiều lần.

---

## 6. Rủi ro còn lại & việc chưa làm

- **Freshness FAIL không được giải quyết:** Dữ liệu mẫu cố ý cũ (2026-04-10) để demo tính năng monitoring; trong thực tế cần công cụ báo động SLA real-time tự re-ingest.
- **Log file encoding:** Lỗi `UnicodeEncodeError` (charmap U+2192) trên Windows đã fix code tạm (`sys.stdout.reconfigure`), tuy nhiên cần refactor tổng quan tốt hơn cho OS agnostic.
- **Điểm đánh giá:** Sinh viên chạy `grading_run.py` thành công tạo artifact `grading_run.jsonl` đáp ứng full requirement (pass 3 câu hỏi với top1_doc_id và Expectation hoàn mĩ), chứng minh luồng QA Pipeline đã đạt Merit/Distinction chuẩn.
- Cần ghi lại nội dung "Peer review 3 câu hỏi" trong buổi học kế.
