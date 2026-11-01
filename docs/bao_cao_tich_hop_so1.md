# Báo cáo dễ hiểu — bản tích hợp số 1

Hoàn thiện sáu mục trước, sau đó mới chạy kiểm tra, đúng trình tự đã thống nhất.
Phạm vi là một phôi trong mỗi chu trình. Chưa có chương trình ghi lệnh ra PLC thật.

| Mục | Kết quả triển khai và chức năng |
|---|---|
| M01 | Loại tín hiệu/lệnh nhầm phiên, lượt cũ, lặp số thứ tự; chặn lệnh ngoài giới hạn. |
| M02 | Đọc cảm biến theo bảng tên và quy tắc đổi thời gian; chưa rõ giữ trạng thái chưa biết. |
| M03 | Mô phỏng và đọc lại tệp dùng cùng lõi; ghi được dấu vết tín hiệu và lệnh. |
| M04 | Tính trước chuyển động băng/phôi trên một mô hình MuJoCo riêng. |
| M05 | Xem nhật ký, trạng thái và kết quả trên trang tiếng Việt, chỉ đọc. |
| M06 | Có kiểm tra ghép toàn bộ, hướng dẫn mở, gói nguồn và Docker thử nghiệm. |

## Kết quả đã kiểm tra

93 kiểm tra logic đạt. Chạy mở giả định hoàn tất và đặt đúng phôi trong mô phỏng.
Chạy chặt chẽ dừng chờ khi chưa có phản hồi trục/chân không. Đọc lại dữ liệu và
xử lý dự báo quá hạn đạt. Trong Docker: 15 tình huống bản tin đặt lại và 2 cảnh
mô phỏng đạt; 15 tình huống tái cấu hình đạt. Mã trong ảnh khớp mã nguồn đã kiểm tra.
Trang tổng quan tải được API, HTML và JavaScript trong WSL; chưa xem xét bố cục bằng mắt.

## Phần cần điều chỉnh tiếp theo

Nhánh dự báo MuJoCo mới tính 54 trường hợp trong khoảng 306 ms ở một phép thử;
không thể suy thành tốc độ bảo đảm. Hạn cấu hình đang là 20 ms, vì vậy chưa đủ
bằng chứng dùng nhánh này để quyết định theo hạn đó. Nhánh tính cũ vẫn mặc định.
MuJoCo mới chỉ dự báo băng và phôi, chưa dự báo toàn bộ robot và khí nén.
Không có phần trăm tăng tốc hoặc độ chính xác phát hiện lỗi máy thật đã xác nhận.

Sau đợt này mới lần lượt thử: lỗi cảm biến, trễ/mất mạng, thay tốc độ, sai số đo.
Mỗi lần lưu hồ sơ riêng, so với bản hiện tại rồi mới đổi một nhóm tham số.
Chưa thực hiện tìm tham số tối ưu trong đợt tích hợp này.

Bản CAD V5 và cảnh MuJoCo chưa đồng bộ đầy đủ. Cần đo ma sát, khí nén, thời gian
đáp ứng, phản hồi trục và chân không trên máy thật. Chưa xử lý nhiều phôi cùng lúc.
Đặt lại hiện tạo chu trình mới, không tự tiếp tục phôi cũ sau lỗi.

Xem `ban_tich_hop_phan_mem.md` để mở và chạy; `nhat_ky_cong_viec.md` để biết
đã làm từng mục; `../docker/RELEASES.md` để tra ảnh thử nghiệm và bằng chứng.
