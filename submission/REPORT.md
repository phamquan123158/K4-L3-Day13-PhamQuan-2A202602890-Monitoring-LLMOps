# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Phạm Quân
- **MSSV:** 2A202602890
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/phamquan123158/K4-L3-Day13-PhamQuan-2A202602890-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-<MSSV>`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | | 100/100 | 0 trường bắt buộc/enrichment thiếu; 0 PII leak |
| `validate_dashboard.py` | | 6/6 panel | Contract hợp lệ và dashboard runtime đã render đủ panel |
| `pytest` | | 22 passed | Chạy trong `.venv` |
| Số traces hợp lệ | | 14 | Langfuse v2 xác nhận 14 trace, mỗi trace có root/retriever/generation |
| Số PII leak | | 0 | Log validator trên 50 record gần nhất |
| Latency P95 / TTFT P95 | | 1194 ms / 50 ms | 24 request hoàn tất trong cửa sổ 60 phút |
| Retrieval success rate | | 100% | 24/24 request có tool result thành công trong cửa sổ đo |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** middleware chấp nhận `x-request-id` hợp lệ dạng `req-<8-hex>`, nếu thiếu/sai format thì tự sinh; ID được bind vào structlog contextvars, response header và trace metadata.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- **Cách bảo đảm PII được scrub trước khi ghi:** processor scrub đệ quy event trước JSON renderer và file writer; không bật capture input/output thô cho observations.
- **Cách kiểm chứng kết quả:** `validate_logs.py` đạt 100/100, không có PII phát hiện trong 50 log gần nhất.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** dùng key trong `.env` của project đã cấu hình; Langfuse v2 trả 14 trace trong workload vừa chạy.
- **Cấu trúc root/retrieval/generation observations:** root `lab-agent-run` (`AGENT`) có hai child `rag-retrieve` (`RETRIEVER`) và `llm-generate` (`GENERATION`).
- **Cách nối trace với log:** cùng `correlation_id` trong metadata trace và JSONL; ví dụ `req-24a4af97`.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** version 1, label `baseline`.
- **Version/label candidate:** version 2, label `candidate`.
- **Trace ID của mỗi version:** baseline v1 `da83975537b21709b9a639954ffe7a49`; candidate v2 `bf7c40d30d813e9ed84914bf0c1d3434`; production v2 trước rollback `5ffa3847347ef03d41d0850602635b76`; production v1 sau rollback `adf01943995b07d8af837cfa2460e30e`.
- **Cách promote và rollback `production`:** production được gán v2, cùng input sinh trace trên, sau đó label được trả về v1; Langfuse v2 xác nhận production hiện là version 1 (`baseline`, `production`).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Streamlit đọc `data/logs.jsonl`, cửa sổ 60 phút, refresh 30 giây; latency/TTFT, traffic, errors/retrieval success, cost, tokens, quality. Contract validator đạt 6/6.
- **SLO và lý do chọn:** `fast_successful_requests` mục tiêu 99.5% trong 28 ngày; request thành công khi có `response_sent` và latency không quá 3000 ms. Ngưỡng bắt suy giảm trước khi request trở nên quá chậm với người dùng.
- **Cách tính error budget:** 100% - 99.5% = 0.5% tổng request trong cửa sổ 28 ngày; số request lỗi cho phép = tổng request × 0.005 (ví dụ 10,000 request tương ứng 50 request).
- **Ba alert và runbook tương ứng:** `p95_latency_budget_breach` → [Alert 1](../docs/alerts.md#alert-1); `retrieval_failure_spike` → [Alert 2](../docs/alerts.md#alert-2); `quality_and_cost_regression` → [Alert 3](../docs/alerts.md#alert-3). Cả ba gửi Slack và có severity, duration, owner.

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
