# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Hồ Quang Hiển  
**Vai trò:** Ingestion / Raw Owner (Sprint 1 Lead)  
**Ngày nộp:** 2026-04-15

## 1. Tôi phụ trách phần nào?

Trong Day 10, tôi phụ trách phần Ingestion ở Sprint 1, tập trung vào ba việc: (1) bảo đảm dữ liệu thô đi vào pipeline đúng đường dẫn và có `run_id` để truy vết, (2) kiểm tra đầu ra log theo Definition of Done của Sprint 1, và (3) chốt tài liệu schema + source map để các vai trò Sprint sau dùng thống nhất. Tôi chạy pipeline bằng lệnh `python etl_pipeline.py run --run-id sprint1` và kiểm tra log tại `artifacts/logs/run_sprint1.log`, manifest tại `artifacts/manifests/manifest_sprint1.json`.

Tôi cũng cập nhật tài liệu contract ở hai file: `docs/data_contract.md` và `contracts/data_contract.yaml` để mô tả rõ nguồn ingest, failure mode, metric theo dõi và thông tin owner/alert channel. Phần này giúp nhóm có cùng ngôn ngữ giữa code và tài liệu trước khi mở rộng cleaning rules/expectations ở Sprint 2.

Kết nối với thành viên khác: tôi bàn giao các số liệu nền của run Sprint 1 (`raw=10`, `cleaned=6`, `quarantine=4`) cho Cleaning/Quality Owner để làm baseline đo impact khi thêm rule mới.

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật chính của tôi là giữ mô hình ingest có khả năng truy vết đầy đủ theo `run_id` thay vì chỉ quan tâm việc chạy xong. Cụ thể, tôi ưu tiên kiểm chứng bốn chỉ số bắt buộc xuất hiện trong log (`run_id`, `raw_records`, `cleaned_records`, `quarantine_records`) trước khi xem các phần nâng cao khác. Lý do là nếu thiếu chuẩn log ngay từ đầu, các sprint sau sẽ khó chứng minh tác động của rule mới hoặc khó phân tích lỗi khi có regression.

Tôi cũng chốt nguyên tắc tài liệu: schema cleaned và source map phải ghi rõ để không xảy ra lệch giữa code và contract. Trong `docs/data_contract.md`, tôi mô tả nguồn `data/raw/policy_export_dirty.csv` là batch ingest chính, còn `data/docs/*.txt` là canonical reference. Cách tách này giúp nhóm phân biệt dữ liệu vận hành và dữ liệu chuẩn đối chiếu chính sách.

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly nổi bật trong lần chạy Sprint 1 là freshness check trả về FAIL, với nội dung: `latest_exported_at=2026-04-10T08:00:00`, `age_hours=121.047`, `sla_hours=24.0`, reason `freshness_sla_exceeded`. Ban đầu nhìn vào trạng thái FAIL có thể hiểu nhầm là pipeline bị lỗi. Tôi xử lý bằng cách kiểm tra toàn bộ run log và xác nhận pipeline vẫn kết thúc `PIPELINE_OK`, expectation đều OK, embed vẫn upsert thành công (`embed_upsert count=6 collection=day10_kb`).

Kết luận của tôi: đây là cảnh báo observability đúng theo thiết kế, không phải lỗi kỹ thuật của ingest. Tôi ghi lại cách diễn giải này trong report nhóm để tránh nhầm khi review kết quả Sprint 1.

## 4. Bằng chứng trước / sau

Bằng chứng số liệu trước/sau ingest-clean ở run `sprint1`:

- Trước clean (raw): `raw_records=10`
- Sau clean: `cleaned_records=6`, `quarantine_records=4`

Bằng chứng file:

- Log: `artifacts/logs/run_sprint1.log`
- Cleaned CSV: `artifacts/cleaned/cleaned_sprint1.csv`
- Quarantine CSV: `artifacts/quarantine/quarantine_sprint1.csv`
- Manifest: `artifacts/manifests/manifest_sprint1.json`

Dựa trên số liệu này, tôi xác nhận pipeline đã thực hiện đúng mục tiêu Sprint 1: ingest được dữ liệu thô, tách quarantine có kiểm soát và lưu vết đầy đủ để các sprint sau tiếp tục.

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi muốn thêm một bảng tóm tắt metrics theo từng `run_id` (append vào CSV/JSONL) để so sánh nhanh `raw-cleaned-quarantine` và freshness qua nhiều lần chạy. Việc này giúp nhóm phát hiện drift sớm, đồng thời hỗ trợ phần báo cáo before/after ở Sprint 3 rõ ràng hơn.