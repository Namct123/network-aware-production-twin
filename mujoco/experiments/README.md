# Kế hoạch thí nghiệm mô phỏng

Các JSON trong thư mục này là **experiment plan**, không phải machine profile.
Không truyền chúng vào `--config`. Dùng `check_robustness.py --plan ...` hoặc
`scripts/docker_dt.ps1 -Mode robustness-check -Plan ten_ke_hoach.json`.

- `robustness_20261031.json`: 13 kịch bản × 3 seed × 2 chế độ chính sách = 78 lượt.
- `robustness_smoke.json`: 3 kịch bản × 1 seed × 2 chế độ = 6 lượt kiểm tra nhanh/CI.

Kế hoạch ghi rõ budget tính predictor (mặc định 1 s cho kiểm tra chức năng).
Mỗi scenario có tên riêng, patch tham số, fault và thời điểm bắt đầu fault.
Các patch chỉ cho phép delay/jitter/loss mạng, hệ số tốc độ băng dài, khối lượng
phôi và lực hút hữu hiệu. Seed và bật/tắt chính sách được ghép theo cặp tự động.
Các giá trị biến thiên là fixture tổng hợp, không được ghi thành số đo máy thật.

Toàn bộ cấu hình được kiểm tra trước khi chạy. Ma trận có giới hạn 200 lượt;
tên thư mục do chương trình sinh không cho phép đường dẫn tùy ý. Mỗi lượt lưu
profile hiệu lực và ground truth riêng; có lỗi vẫn giữ báo cáo và dữ liệu.

Các bảng nhóm không tính chu kỳ từ ca HOLD và không gọi mọi HOLD không có fault
cảm biến là báo nhầm. Nhiều seed của mạng tất định cũng không tạo thử nghiệm độc lập.
Xem `docs/robustness.md` ở thư mục gốc dự án để diễn giải kết quả và giới hạn.
