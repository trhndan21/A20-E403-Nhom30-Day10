# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User / agent thấy gì? (VD: trả lời "14 ngày" thay vì 7 ngày cho refund window, hoặc data stale từ effective_date cũ)

---

## Detection

> Metric nào báo? (freshness SLA >24h, expectation fail "no_stale_refund_window", eval `hits_forbidden` tăng)

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` (ví dụ: `manifest_sprint1.json`) | Xem `exported_at` > SLA 24h (so với current time), `freshness` fail. Nếu `measured_at: "publish"` thì check SLA. |
| 2 | Mở `artifacts/quarantine/*.csv` (ví dụ: `quarantine_sprint1.csv`) | Xem rows fail quality_rules: chunk_text duplicate, refund window "14 ngày" (severity halt), effective_date invalid. |
| 3 | Chạy `python eval_retrieval.py` với test_questions.json | Eval score giảm (accuracy < threshold), `hits_forbidden` tăng (trả lời sai policy). |

---

## Mitigation

> 1. Rerun pipeline: `python etl_pipeline.py run --run-id <new_id>` để clean lại data.  
> 2. Rollback embed: Nếu vector store Chroma bị corrupt, restore từ backup hoặc rerun embed stage.  
> 3. Tạm banner: Trong serving (Day 08/09), hiển thị "Data stale - please retry later" nếu freshness fail.

---

## Prevention

> 1. Thêm expectation mới trong `quality/expectations.py` cho stale data (ví dụ: check effective_date > cutoff).  
> 2. Alert trên freshness SLA: Integrate với monitoring để notify group-report-and-runbook nếu SLA >24h.  
> 3. Assign owner: A20-E403-Nhom30 (Ingestion Lead: Hien) chịu trách nhiệm rerun.  
> 4. Guardrail trong Day 11: Thêm validation trước embed để block stale chunks.
