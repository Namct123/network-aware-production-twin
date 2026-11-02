# Báo cáo đợt đánh giá — 02/11/2026

Đã hoàn thiện ba mục: đo thời gian dự báo, chạy lỗi có đối chứng và đưa kết quả lên trang tổng quan.
Viết đủ các mục trước khi chạy. Không điều chỉnh tốc độ, ngưỡng hoặc thông số vật lý theo kết quả.

## Thời gian quan sát

Mỗi ô là 15 lượt đo sau làm nóng, trên 3 trạng thái ước lượng giả lập. Hai nhánh có mức chi tiết khác nhau.
p95 là số đo theo thứ hạng chứa 95% mẫu; chưa phải thời gian lớn nhất bảo đảm. Hạn chức năng dùng riêng 1 giây.

| Môi trường | Nhánh | Loại hạn | Trung vị (ms) | p95 (ms) | Quá hạn / mẫu | Tính đủ / mẫu |
|---|---|---|---:|---:|---:|---:|
| WSL | Tính 1 chiều | Đang cấu hình: 20 ms | 1.928 | 3.053 | 0/15 | 15/15 |
| WSL | Tính 1 chiều | Chức năng: 1 giây | 2.121 | 3.137 | 0/15 | 15/15 |
| WSL | MuJoCo băng/phôi | Đang cấu hình: 20 ms | 20.322 | 20.833 | 15/15 | 0/15 |
| WSL | MuJoCo băng/phôi | Chức năng: 1 giây | 436.826 | 468.342 | 0/15 | 15/15 |
| Docker | Tính 1 chiều | Đang cấu hình: 20 ms | 2.760 | 3.537 | 0/15 | 15/15 |
| Docker | Tính 1 chiều | Chức năng: 1 giây | 2.297 | 3.016 | 0/15 | 15/15 |
| Docker | MuJoCo băng/phôi | Đang cấu hình: 20 ms | 20.482 | 21.094 | 15/15 | 0/15 |
| Docker | MuJoCo băng/phôi | Chức năng: 1 giây | 460.372 | 596.286 | 0/15 | 15/15 |

Nhánh MuJoCo vẫn chưa phù hợp quyết định theo hạn 20 ms. Không tăng hạn mặc định để biến kết quả thành đạt.
Báo cáo thời gian này không đo độ chính xác cơ học hoặc chứng nhận thời gian thực; môi trường lúc ổ đĩa gần đầy không đại diện mọi điều kiện vận hành.

## Kết quả có đối chứng

Bật/tắt giới hạn tốc độ tái cấu hình cố định; cả hai vẫn dùng bộ ước lượng và dự báo. Không gọi đây là so PLC tuần tự với DT.
Mỗi tình huống dùng 2 seed (mã tạo nhiễu); tình huống tất định không thành độc lập chỉ vì đổi seed.

| Tình huống | Tắt: hoàn tất / dừng | Bật: hoàn tất / dừng |
|---|---:|---:|
| Bình thường | 2 / 0 | 2 / 0 |
| Cảm biến điểm gắp không báo | 0 / 2 | 0 / 2 |
| Trễ dữ liệu 20 ms | 0 / 2 | 2 / 0 |
| Mất 5% bản tin | 2 / 0 | 2 / 0 |
| Băng mô phỏng chậm hơn lệnh 15% | 2 / 0 | 2 / 0 |
| Băng mô phỏng nhanh hơn lệnh 15% | 2 / 0 | 2 / 0 |

24/24 lượt đạt tiêu chí hỗ trợ phôi khi dừng hoặc đặt phôi khi hoàn tất. Có 18 lượt hoàn tất và 6 lượt dừng, không gọi cả 24 là sản xuất thành công.
Hai lượt trễ 20 ms chỉ là hai tình huống mô phỏng cụ thể; chưa suy ra phần trăm tăng năng suất hoặc độ chính xác phát hiện lỗi máy thật.
Dữ liệu lượt không đạt nếu có sẽ vẫn được giữ; trong ma trận lần này không có vi phạm tiêu chí.

## Các việc đã kiểm tra

- Docker: 97 kiểm tra logic, 24 lượt đối chứng và kiểm tra tích hợp đều đạt.
- Bên ngoài ảnh: 8 kiểm tra web, 2 kiểm tra đóng gói và cú pháp JavaScript đạt.
- Mã trong ảnh khớp tệp nguồn; ảnh cũ giữ nguyên. Ảnh mới candidate-20261102-qualification chờ người dùng nghiệm thu.
- Chi tiết và cách mở: [hướng dẫn đánh giá](danh_gia_co_doi_chung.md); [nhật ký](nhat_ky_cong_viec.md).

## Việc tiếp theo

Tối ưu nhánh dự báo MuJoCo dựa trên thời gian vừa đo, rồi kiểm tra lại độ tương đương và việc dừng khi quá hạn.
Chưa ghép PLC thật, chưa hiệu chuẩn khí nén/ma sát hoặc đồng bộ đầy đủ CAD V5. Chưa huấn luyện học máy.
Ổ C gần đầy đã gây lỗi khởi động WSL trong đợt này. Đã nén tại chỗ dữ liệu sinh ra, không xóa bằng chứng hay ảnh cũ; cần thêm dung lượng cho các đợt lớn.
