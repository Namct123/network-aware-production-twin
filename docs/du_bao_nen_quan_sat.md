# Dự báo nền: chạy quan sát trước khi dùng để điều khiển

MuJoCo trước đây tính đủ khoảng 50 ms ở phép đo 8 luồng, lâu hơn hạn 20 ms.
Bộ mới đưa việc này sang tiến trình riêng; nhánh dự báo 1 chiều vẫn quyết định.
Đây là bước tách đường tính chậm và kiểm chứng giao tiếp, chưa giải xong việc
áp một dự báo cũ vào trạng thái mới. Kết quả nền không được cho chạy, dừng hay reset.

## Cách chạy

```text
python mujoco/check_background.py --output output/docker/background-check_local
```

Hoặc Docker thử nghiệm:

```text
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode build
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode background-check
```

Bộ thử chạy 3 chu trình: không chạy nền; chạy MuJoCo nền; nền bị đặt hạn tính rất
ngắn để luôn trả kết quả thiếu. Có đối chứng dấu vết lệnh và kiểm tra tiến trình
nền bị dừng vẫn không làm hỏng bước gọi lõi. Thư mục đầu ra phải chưa tồn tại.

Muốn mở một lượt riêng, trong môi trường MuJoCo đã cài:

```text
python mujoco/run_twin.py --config mujoco/configs/background_observer_20261103.json --assume-open-loop --pace-wall-time --output output/docker/background_demo
```

--assume-open-loop chỉ là giả định mô phỏng cho trục/chân không chưa có phản hồi;
không dùng để tuyên bố máy thật đã kiểm chứng. --pace-wall-time làm nhịp mô phỏng
chờ theo thời gian trên máy để có cơ hội nhận kết quả nền; không phải đồng bộ PLC.
Nếu chạy tua nhanh thì kết quả nền thường bị loại do thời gian mô phỏng đã tiến xa.

## Vì sao chưa cho phép áp lời khuyên nền?

Một dự báo hoàn tất sau 50 ms có thể tính từ vị trí trước đó và từ phương án
chỉ chạy thêm 20 ms rồi dừng. Không thể tự hiểu CONTINUE cũ là được tiếp tục từ
vị trí hiện tại. Do đó tất cả kết quả hiện chỉ ghi tệp, dù qua các kiểm tra sau:

- Đúng phiên, lượt khởi tạo, mã hồ sơ và ảnh chụp đầu vào.
- Đúng yêu cầu đang đợi; bản tin sai không được giải phóng chỗ của yêu cầu thật.
- Tuổi quyết định/nguồn trong đồng hồ mô phỏng, tuổi yêu cầu trong đồng hồ cha,
  số mẫu trễ và chân trời dự báo còn đủ. Không trừ lẫn hai loại đồng hồ.
- Pha và lần đổi lệnh chưa thay; ước lượng hiện tại còn phù hợp khoảng truyền
  động sơ bộ. Đây là điều kiện đọc quan sát, chưa phải chứng minh an toàn.
- Đủ kịch bản, kết quả hữu hạn. Thiếu, sai hoặc quá cũ đều bị loại.

Tối đa một yêu cầu được xử lý. Khi bận sẽ bỏ qua lần gửi mới, không tích hàng
vô hạn. Kẹt, lỗi hoặc chết tiến trình được ghi nhận; không tự khởi động lại
hoặc đổi nhánh điều khiển. Tiến trình được đóng trong nhánh finally khi kết thúc.

## Các tham số chỉnh được

Hồ sơ giữ prediction.backend=numeric_1d và prediction.wall_budget_s=0.02.
Nhóm prediction.background có enabled, mode=observe_only, compute_budget_s,
max_sim_age_s, max_wall_age_s, max_lag_sequences, worker_timeout_s,
startup_timeout_s và close_timeout_s. native_threads chọn số luồng của worker.
Đó là thiết lập phần mềm, không phải số đo đã hiệu chuẩn. Đổi hồ sơ bằng phiên
RuntimeCore mới, không sửa tham số ngay trong một phiên đang chạy.

## Đọc kết quả

background.jsonl ghi gửi, bận, nhận/loại và lý do; prediction.jsonl vẫn ghi quyết
định nhánh nhanh. control_timing.jsonl đo bước RuntimeCore và phần giao tiếp nền,
không gồm cơ học, ghi tệp, nhịp chờ hoặc khởi tạo. summary.json ghi worker đã đóng.
Bộ thử có report.md và background_check.json. Kết quả không đạt không được xóa.
Không suy p95/lớn nhất quan sát thành bảo đảm thời gian thực hoặc độ chính xác máy thật.
