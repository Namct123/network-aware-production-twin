# Công bố dự án trên GitHub — 01/11/2026

Kho công khai: https://github.com/Namct123/network-aware-production-twin

Gói tải xuống: https://github.com/Namct123/network-aware-production-twin/releases/tag/candidate-20261101-focused-handoff

## Cách lấy dự án

Nhấn Code → Download ZIP hoặc dùng:

```text
git clone https://github.com/Namct123/network-aware-production-twin.git
```

Đọc README.md, sau đó docs/ban_tich_hop_phan_mem.md. Các báo cáo PDF và bản thảo
ở reports. Bản tải nguồn hiện tại là `ProductionTwin_Focused_Source_20261101.zip`
trong Releases, đi kèm SHA256SUMS.txt để đối chiếu. Bản này đã gỡ cầu nối và scene
Factory I/O; bản nguồn đầy đủ cũ được thay khỏi mục tải xuống để tránh lấy nhầm.
Các gói cũ có cấu hình và hình học riêng, không được gọi là đã đồng bộ với bản mới.

Mã Docker và cấu hình dựng ảnh có trong kho, không tải ảnh nhị phân lên dịch vụ
khác. Thư viện cài đặt, tệp bí mật, bộ nhớ đệm và toàn bộ nhật ký chạy thô không
đưa vào Git. Bằng chứng kiểm tra chọn lọc có trong docker/evidence.

Kho được xác minh xem được không cần đăng nhập. Cấu hình Git ghi tác giả
Namct123 <namface561@gmail.com>. Trạng thái kiểm tra tự động xem ở mục Actions;
công khai dự án không thay thế việc kiểm chứng và nghiệm thu máy thật.
