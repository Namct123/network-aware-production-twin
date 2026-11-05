# Hướng nghiên cứu hiện tại — 2026-11-05

## Material Passport

- Origin Skill: experiment-agent (tham khảo thiết kế và giới hạn bằng chứng)
- Origin Mode: plan; triển khai mã theo ủy quyền trực tiếp của người dùng
- Origin Date: 2026-11-05
- Verification Status: kế hoạch nghiên cứu; không phải kết quả kiểm chứng vật lý
- Version Label: predictive_residual_scope_v1

## Câu hỏi chính

Với cùng thông tin đầu vào, hệ có thể phát hiện sai lệch dự đoán–quan sát và chọn
cấu hình tốt hơn để tiếp tục làm việc trong điều kiện tín hiệu/mạng suy giảm không?
Không mặc định câu trả lời là có. ML chỉ được giữ nếu bổ sung lợi ích có đối chứng.

## Các mục phải làm theo thứ tự

1. Bộ so sánh độc lập: dự đoán trước khi nhận mốc cần kiểm tra, tính miền sai số,
   kiểm tra tín hiệu và thời gian; dữ liệu thật chỉ dùng để chấm ngoài lõi.
2. Hiệu chuẩn miền sai số trên tập bình thường riêng, kiểm tra mức bao phủ và báo
   nhầm trên tập chưa dùng để chọn tham số. Không gọi khoảng giả định là 95%.
3. So với timeout và quy tắc thích nghi có cùng dữ liệu. Kết quả ngoại tuyến không
   được chuyển thành kết luận tăng năng suất hoặc hồi phục chu trình.
4. Tạo chế độ suy giảm có giới hạn: tốc độ, thời gian, nguồn xác nhận và điều kiện
   chuyển bước. Thử kín trong mô phỏng; không tự bỏ qua liên động/feedback chưa có.
5. Thêm ML để học sai lệch hoặc đánh giá bất thường; tách train/validation/test
   theo phiên/điều kiện, không trộn các mẫu gần nhau hoặc lặp xác định để phóng đại
   độ chính xác. Giữ đối chứng quy tắc và DT không ML.
6. Hợp đồng PLC: yêu cầu chế độ/phiên bản, tham số giới hạn, hạn hiệu lực, ACK,
   trạng thái thực thi và chuyển HOLD khi không hợp lệ. Chưa có bộ ghi S7 thật.
7. Đo và kiểm chứng vật lý sau cùng theo yêu cầu người dùng; cập nhật tham số
   thay vì viết cứng số đo chưa có.

## Điều chưa thể suy ra

Không có mốc đầu vào thì không khẳng định đã biết vị trí. Hai lỗi cùng quan sát
thì chưa tách được nguyên nhân. Mất truyền động thật không có nghĩa phần mềm có
thể tạo đường cơ khí thay thế. Camera là khả năng bổ sung, chưa phải dữ liệu đo.

## Tiêu chí chấp nhận nghiên cứu

- Phát hiện: báo nhầm, bỏ sót trong cửa sổ quan sát đủ dài, thời gian từ dấu hiệu
  quan sát được tới báo; tách với thời gian từ lúc chèn lỗi.
- Mô hình: mức bao phủ khoảng theo điều kiện, độ rộng và sai số dự đoán.
- Vận hành: số sản phẩm đúng, thời gian dừng, vi phạm ràng buộc và chi phí tính.
- Mỗi phép so phải cùng thông tin, điều kiện và ngân sách tính; báo cả ca không
  có lợi, hết quan sát hoặc không đủ thông tin. Chưa cam kết % cải thiện.

## Tinh giản

Ưu tiên các mục trên. Không tiếp tục thêm giao diện, đổi engine, RL hoặc bản thảo
trùng nếu chưa phục vụ phép thử cụ thể. Giữ MuJoCo làm môi trường thử; giữ mô hình
1D nhẹ và nhánh tiếp xúc để đối chiếu, chưa cho mô hình nền quyền điều khiển.
