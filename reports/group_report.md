# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** A20-E403-Nhom30  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Hồ Quang Hiển | Ingestion / Raw Owner | ___ |
| ___ | Cleaning & Quality Owner | ___ |
| ___ | Embed & Idempotency Owner | ___ |
| ___ | Monitoring / Docs Owner | ___ |

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
| … | … | … | … |

**Rule chính (baseline + mở rộng):**

- Phần này do Cleaning/Quality Owner bổ sung ở Sprint 2.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Phần này do Cleaning/Quality Owner cập nhật sau khi chạy kịch bản inject ở Sprint 3.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Phần này do Embed Owner phụ trách ở Sprint 3.

**Kết quả định lượng (từ CSV / bảng):**

Phần này do Embed Owner cập nhật bằng `artifacts/eval/*.csv`.

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

Trong run Sprint 1 (`run_id=sprint1`), manifest ghi `latest_exported_at=2026-04-10T08:00:00` và freshness check trả `FAIL` do `age_hours=121.047` vượt `sla_hours=24.0`. Đây là tín hiệu đúng cho lớp observability vì dữ liệu demo đã cũ hơn ngưỡng SLA đã cấu hình. Điểm quan trọng ở Sprint 1 là phân biệt rõ hai trạng thái: (1) pipeline kỹ thuật chạy thành công (`PIPELINE_OK`) và (2) chất lượng/độ tươi dữ liệu có cảnh báo để owner xử lý theo runbook. Nhóm sẽ dùng kết quả này làm đầu vào cho phần monitoring docs ở Sprint 4.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

Phần này do Embed Owner và Monitoring/Docs Owner cập nhật sau khi hoàn tất Sprint 3-4.

---

## 6. Rủi ro còn lại & việc chưa làm

- Chưa có kịch bản inject + before/after retrieval trong phần report này (đợi Sprint 3).
- Chưa ghi đầy đủ peer review 3 câu hỏi của phần E (đợi Sprint 4).
