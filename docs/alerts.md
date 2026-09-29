# Alert và runbook cho dashboard / SLO

Mỗi alert đều dựa trên triệu chứng người dùng hoặc SLO, không dựa vào tên implementation nội bộ.

## Alert 1

- Tên: p95_latency_budget_breach
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack
- SLI/SLO liên quan: SLO fast_successful_requests, error budget 0.5% trong 28 ngày
- Điều kiện và thời gian duy trì: p95 latency vượt 3000ms liên tục 5 phút
- Ảnh hưởng tới người dùng: người dùng thấy phản hồi chậm, độ tin cậy cảm nhận giảm, đặc biệt trên query dài hoặc trong giờ cao điểm
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra dashboard panel latency để thấy liệu P95/P99 có vượt ngưỡng và khoảng thời gian nào bắt đầu.
  2. Lọc log `response_sent` theo `correlation_id` và xác định request nào chậm nhất trong khoảng đó.
  3. Mở trace Langfuse của các request đó để xác định có phải retrieval hoặc LLM generation bị kéo dài.
- Mitigation tạm thời: giảm concurrency, bật cơ chế timeout hoặc giảm độ dài context truy xuất để tránh xếp hàng.
- Owner: platform-oncall

## Alert 2

- Tên: retrieval_failure_spike
- Severity: critical
- Duration: 10m
- Kênh thông báo: Slack
- SLI/SLO liên quan: retrieval success rate >= 90% và error budget của các lỗi tool
- Điều kiện và thời gian duy trì: tỷ lệ retrieval success thấp hơn 90% trong 10 phút hoặc tool_fail xuất hiện liên tiếp
- Ảnh hưởng tới người dùng: nhiều request không trả lời đúng hoặc bị lỗi hoàn toàn; chất lượng service giảm mạnh
- Ba bước kiểm tra đầu tiên:
  1. Xem panel errors để xác định tool_success_rate_pct và error_type.
  2. Kiểm tra `request_failed` và `tool_name` trong log để xác nhận có phải lỗi retrieval hay LLM.
  3. So sánh trace của request lỗi với span retrieval/LLM để kiểm tra xem có timeout hoặc dependency xuống cấp không.
- Mitigation tạm thời: vô hiệu hóa hoặc chuyển sang fallback document set, kiểm tra backend retrieval và retry cơ bản.
- Owner: llm-ops

## Alert 3

- Tên: quality_and_cost_regression
- Severity: warning
- Duration: 15m
- Kênh thông báo: Slack
- SLI/SLO liên quan: quality score trung bình >= 0.75, chi phí <= 2.5 USD/ngày
- Điều kiện và thời gian duy trì: average quality < 0.75 hoặc tổng chi phí ngày vượt 2.5 USD liên tục 15 phút
- Ảnh hưởng tới người dùng: chất lượng trả lời giảm, câu trả lời quá ngắn hoặc thiếu tính nhất quán; còn làm tăng chi phí vận hành
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel quality và cost trong dashboard để xác nhận xu hướng đi xuống hay tăng đột ngột.
  2. Lọc log từ `response_sent` để xem tokens_in/tokens_out, quality_score và latency của request gần thời điểm alert.
  3. Mở trace của request thấp chất lượng để xác định liệu prompt, retrieval hoặc model config đang lệch từ baseline.
- Mitigation tạm thời: rollback prompt về version ổn định và giảm độ dài prompt/context để giảm cost.
- Owner: product-analytics
