# Quy ước tích hợp

## Nguồn chuẩn hiện tại

- Hình học CAD hiện tại: `fusion/ProductionTwin_V5/ProductionTwin_V5.py` và bản tham chiếu `cad_reference/production_twin_v5.step`. Một số kích thước đã có số đo sơ bộ; hình học CAD V5 chưa đồng bộ đầy đủ với cảnh MuJoCo. V0/V4 chỉ giữ làm lịch sử.
- Giao diện tín hiệu MuJoCo hiện tại: `mujoco/signals.py`, `mujoco/sensor_model.py` và bảng trong `docs/dt_core_progress.md`. Tín hiệu chưa có nguồn dùng `null/unavailable`; không thay bằng `false`. Dữ liệu chuẩn của bộ mô phỏng chỉ đi vào log đánh giá riêng.
- Thông số vận hành: profile JSON trong `mujoco/configs/`; sửa giá trị bằng profile mới/CSV số đo, không rải hằng số vào thuật toán. Đơn vị SI, trạng thái nguồn gốc và cách nghiệm thu ở `docs/modular_twin.md`. Đổi schema phải cập nhật loader, các nơi sử dụng và kiểm tra cùng lúc.
- Đơn vị: CAD/CSV dùng mm; MuJoCo dùng m, kg, s; Z hướng lên.

## Quy trình đóng góp

**Docker:** hạng mục chỉ trở thành bản được chấp thuận sau khi người dùng trực tiếp
kiểm nghiệm và xác nhận đạt. Sau xác nhận, cập nhật Docker ngay, chạy kiểm tra và
ghi image ID/hash/nguồn xác nhận trong `docker/RELEASES.md`. Bản chờ kiểm nghiệm
mang tag candidate; không tự gắn stable/latest. Xem [hướng dẫn](docs/docker.md).

1. Tạo nhánh riêng cho phần CAD, MuJoCo, PLC hoặc digital twin.
2. Khi đổi tên một tín hiệu, trục, đơn vị hoặc giới hạn chuyển động, cập nhật tài liệu và phần nhận dữ liệu cùng lúc trong pull request.
3. Ghi cách kiểm tra thay đổi. Với MuJoCo, chạy kiểm tra logic và chu trình; với PLC, đính kèm bảng I/O và kết quả mô phỏng; với CAD, nêu kích thước đo thực nào đã thay thế ước lượng.
4. Không đưa mật khẩu, token, IP nội bộ, dữ liệu cá nhân, bộ nhớ đệm hay tệp xuất tạm vào kho.

## Điều kiện trước khi ghép với PLC thật

Xác nhận pin I/O, mức điện, hành trình, chiều trục, trạng thái dừng khẩn và liên động an toàn trên máy. Chưa có trình đọc S7 hoặc lệnh ghi PLC thật; cổng mẫu chỉ ghi lệnh tệp.
