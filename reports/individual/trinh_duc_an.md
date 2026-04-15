# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trịnh Đức An  
**Vai trò:** Architect & Auditor (P5)  
**Ngày nộp:** 2026-04-15  

---

## 1. Tôi phụ trách phần nào?

Trong Lab Day 10 này, tôi đảm nhận vai trò **Architect & Auditor (P5)** nhằm đảm bảo chuẩn hóa môi trường làm việc nhóm, hệ thống hóa quá trình báo cáo và kiểm tra chấm điểm cuối cùng. Cụ thể:
- **Ngữ cảnh:** Giữ nhiệm vụ thiết lập repo, setup môi trường, và quản lý luồng Git qua các Sprint. Đóng vai trò tổng hợp ở chốt chặng cuối.
- **Tập trung:**
  - **`grading_run.py` & `data/grading_questions.json`**: Thiết lập môi trường ảo, xử lý các dependencies và chạy script grading sau khi các bạn hoàn tất.
  - **`reports/group_report.md`**: Thiết kế lại khung báo cáo nhóm, tổng hợp chỉ số `metric_impact` và gán phân rã công việc chi tiết.  
- **Tương tác nhóm:** Tôi quản lý kho repository, phân giải xung đột Git khi các bạn gộp (merge) code từ các nhánh Ingest (Hiển), Clean (Hậu), hay Embed (Dương) khác nhau. Việc setup chuẩn tạo tiền đề vững chắc cho các thành viên hoàn tất phần code mà không bận tâm lặp lại về thiết lập local env.

## 2. Một quyết định kỹ thuật

**Quyết định kỹ thuật của tôi:** Chuẩn hóa việc sử dụng môi trường độc lập kèm `pip install` đồng bộ phiên bản `sentence-transformers` trên các máy macOS (Apple Silicon)/Windows. Ban đầu, kịch bản chạy grading dễ phát sinh crash ở module embedding vector. Thay vì yêu cầu từng bạn tự gỡ lỗi, tôi cấu trúc hóa quyết định thiết lập `bash` pipeline kiểm tra phụ trợ. 

Đồng thời, đối với `group_report.md`, để tối ưu hóa thay vì chờ đợi các thành viên khác nộp bài viết nháp lộn xộn, tôi tổ chức form báo cáo nhóm theo cách "template - slot": phân luồng công việc rõ ràng lấy số liệu của từng người đập vào ô trống chỉ định (VD: `metric_impact` từ Hậu, `inject_bad` từ Dương). Nhờ Audit kỹ, tài liệu thể hiện nhất quán 100% dữ kiện log vào bảng.

## 3. Một lỗi hoặc anomaly đã xử lý

**Anomaly/Lỗi đã đối mặt:** Thiếu hệ thống dependency khi chạy `grading_run.py` (sau 17h, khi GV cập nhật file `grading_questions.json`).
- Triệu chứng: Chạy `python3 grading_run.py --out artifacts/eval/grading_run.jsonl` văng lỗi `ModuleNotFoundError: No module named 'chromadb'`.
- Chẩn đoán: Pip environment mặc định văng lỗi missing module do không có file setup phù hợp ở bản thân file đánh giá (độc lập với ETL ban đầu).
- Hướng giải quyết: Ngay lập tức cài đặt `pip install chromadb sentence-transformers` đồng bộ cho toàn luồng, đảm bảo hệ thống đã setup đủ package phục vụ Retrieval vector store ở model mặc định `all-MiniLM-L6-v2`. Bằng chứng là script đánh giá ngay sau đó chạy xuất `JSONL` thành công.

## 4. Bằng chứng trước / sau

- **Trạng thái Before (Lỗi cấu hình Pipeline Grading):** Môi trường thiếu package sinh ra Terminal output `exit_code: 1` lúc audit. 
- **Trạng thái After (Auditing Thành công):** Chạy lệnh eval thông suốt, khởi tạo tệp `artifacts/eval/grading_run.jsonl`.
  - Check câu `gq_d10_01`: Data ghi nhận `"hits_forbidden": false` và `"contains_expected": true`. Cho thấy pipeline đã nhận rule Clean chuẩn Refund Window từ 14 xuống 7 ngày.
  - Check câu `gq_d10_03`: Khẳng định rule versioning chạy ổn thỏa, `hit_forbidden` báo false chứng nhận HR policy lỗi thời `10 ngày` không lọt vào top vector kết quả. Khẳng định Quality pipeline của nhóm thành công ấn tượng. (Được phản ánh trên JSONL run của Artifacts).

## 5. Cải tiến tiếp theo

Nếu có thêm thời hạn mở rộng (tầm 2 tiếng), tôi sẽ dựng script `Makefile` kết hợp gộp 3 công đoạn trong 1 lệnh duy nhất: Re-run ETL -> Clean Eval -> Grading run. Điều đó sẽ giúp đội ngũ thẩm định nhàn gọn cực độ để tracking toàn luồng trạng thái Data Quality. Thêm nữa, tôi cũng sẽ tích hợp Github Actions CI để tự build lint file format Markdown, đảm bảo độ thẩm mỹ của Repository luôn hoàn hảo nhất khi merge.
