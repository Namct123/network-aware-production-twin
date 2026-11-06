# Rà mô hình xung: lấy mẫu, chuyển động và báo nhầm

## Kết quả mới

Đây là phân tích hậu kiểm trên dữ liệu đã xem, không phải phép kiểm chứng mới.
Không huấn luyện lại mô hình hoặc nới miền cảnh báo. Vị trí từ MuJoCo chỉ dùng
ở phía chấm để tìm giới hạn mô hình, không cấp cho bộ dự báo trực tuyến.

- 12 ca bình thường:6 ca thiếu đầu xung,6 ca đủ để kiểm tra.
- Trong 6 ca đủ, vận tốc trung bình sau xung cao hơn trong xung 5,9–7,9%.
- Miền sai số chỉ do lấy mẫu theo giả thiết lý tưởng chứa 2/6 ca.
- Miền bù hằng số cũ chứa 4/6 ca, phù hợp với 2 ca báo nhầm đã ghi.

## Vì sao công thức xung có thể sai?

Công thức dùng chiều dài phôi chia thời gian che cảm biến để suy vận tốc, rồi
dùng vận tốc đó dự đoán thời điểm tới cảm biến sau. Nếu vật vẫn thay đổi vận
tốc sau giai đoạn đo xung, cùng một vận tốc suy từ xung không mô tả toàn đoạn.

Kết quả từ vị trí chấm xác nhận sự khác nhau giữa hai vận tốc trung bình trong
sáu đoạn này. Nó hỗ trợ nhận định giả thiết vận tốc không đổi chưa phù hợp,
chưa loại trừ mọi ảnh hưởng hình học, tư thế phôi hoặc mô hình tiếp xúc.

## Tách riêng ảnh hưởng của lấy mẫu

GọiT là chu kỳ lấy mẫu,L là độ dài phôi,d là quãng còn lại sau khi hết xung.
Với vận tốc vật lý không đổi, biết đúngL, cảm biến điểm lý tưởng và mỗi cạnh
được ghi muộn không quáT, độ lệch thời điểm cạnh mẫu được chặn bởi:

`|thời điểm cạnh ghi được − dự báo từ xung| ≤ (1 + d/L) × T`

VớiL=60 mm,d=200 mm,T=20 ms, bán kính lý tưởng là86,7 ms. Đây là phép chặn
đại số dưới các giả thiết đã nêu, không phải khoảng tin cậy thống kê và không
được tự áp khi chuyển động đã vi phạm giả thiết. Bốn ca nằm ngoài chặn này là
dấu hiệu cần rà mô hình; không thể quy mọi sai lệch cho trễ mạng hoặc lấy mẫu.

## So sánh từng ca có xung đầy đủ

Sai lệch=thời điểm cạnh ghi được trừ thời điểm dự báo; số âm nghĩa cạnh ghi
sớm hơn dự báo. Cột vận tốc chỉ dùng dữ liệu chấm, không dùng để dự báo.

| Điều kiện | Sai lệch xung (ms) | Sau bù hằng (ms) | Vận tốc sau tăng so với trong xung |
|---|---:|---:|---:|
|condition_00_none|-180.0|-82.9|7.9%|
|condition_02_none|-106.7|-9.6|7.3%|
|condition_04_none|-73.3|23.8|7.2%|
|condition_06_none|-93.3|3.8|5.9%|
|condition_08_none|-113.3|-16.2|6.0%|
|condition_10_none|-6.7|90.4|5.9%|

Bù trung bình khoảng−97,1 ms không đủ mô tả mọi điều kiện: có ca còn lệch
sớm82,9 ms và có ca bị bù quá, lệch muộn90,4 ms. Không thay các giá trị này
bằng một kết quả đẹp sau khi dùng cùng dữ liệu để chỉnh ngưỡng.

## Sửa lỗi ranh giới dữ liệu học

Bộ đọc offline trước đây mặc định giá trị trước mẫu đầu làFalse. Khi mẫu đầu
đãTrue, nó có thể tạo đầu xung không thật sự được quan sát. Đã đổi trạng thái
đầu thành chưa biết và yêu cầu cạnhFalse→True thực sự. Bộ theo dõi online đã
từ chối dạng này; nay hai phía nhất quán.61 kết quả học/đánh giá gốc được tái
lập đúng sau sửa; trọng số và miền hiệu chuẩn đóng gói không đổi.

## Công việc tiếp theo

Rà mô hình đáp ứng khởi động và ý nghĩa hình học của cạnh quang. Chọn cấu trúc
mô hình có đầu vào nhân quả như lịch sử lệnh/thời gian bắt đầu, xác định phần
tham số cần hiệu chuẩn. Tạo tập hiệu chuẩn khác, khóa trước tập chưa xem và
so lại với bù hằng; không chỉ nới biên trên sáu ca này. Bộ nối sự kiện thứ hai
và đo vật lý vẫn cần được kiểm chứng riêng.

Mã:audit_pulse_model.py; dữ liệu:output/docker/pulse_model_audit_20261106_final.
19 kiểm tra trong Docker và174 kiểm tra lõi WSL đã đạt. Đây là candidate,
chưa được người dùng nghiệm thu; không có quyền ghi PLC.
