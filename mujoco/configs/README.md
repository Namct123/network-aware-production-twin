# Hồ sơ thông số máy

- `simulation.json`: baseline chưa có số đo thực, dùng để đối chiếu.
- `slow_a2_demo.json`: bản thử tổng hợp dùng A2 0,06 m/s; không phải hiệu chuẩn thật.
- `physical_measurements.csv`: bảng trống để ghi số đo SI, ngày/phương pháp/người đo.
- `predictive_demo.json`: bật giám sát dự báo 1D, tham số tổng hợp chưa hiệu chuẩn.

Sao chép bảng đo cho mỗi phiên; không ghi số 0 thay cho mục chưa đo.
Nhập qua `calibrate.py` để tạo JSON mới có nguồn gốc và kiểm tra tính nhất quán.
Không sửa profile đang được dùng giữa một chu trình.

Hướng dẫn, hợp đồng mô-đun và lệnh chạy: [docs/modular_twin.md](../../docs/modular_twin.md).
