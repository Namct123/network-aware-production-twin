# Dự án hiện làm được gì? — bản giải thích dễ hiểu

Cập nhật ngày 31/10/2026.

## Mục tiêu của hệ thống

Chúng ta đang xây một **bản sao số của trạm gắp thả**: mô hình trên máy tính
nhận dữ liệu, ước lượng phôi đang ở đâu, thử tính điều có thể xảy ra và giúp
chọn cách vận hành. Tên tiếng Anh của ý tưởng này là *Digital Twin*.

Hiện phần lớn việc kiểm tra vẫn thực hiện trong MuJoCo, tức phần mềm mô phỏng
chuyển động và tiếp xúc. Kết quả trên máy tính chưa thay cho kiểm chứng trên
hệ thống thật.

## Những phần đã làm

| Phần đã có | Hiểu đơn giản là gì? | Có ích ở đâu? |
|---|---|---|
| Mô hình trạm | Có băng tải, xi lanh, robot XY, giác hút, cảm biến và phôi | Thử được quá trình vận chuyển, gắp và thả mà chưa cần chạy máy thật |
| Bộ thông số tách riêng | Kích thước, tốc độ, ma sát, thời gian chờ nằm trong tệp | Khi có số đo thật có thể nhập lại, không phải sửa nhiều chỗ trong chương trình |
| Bộ nhận tín hiệu | Phân biệt có phôi, chưa thấy phôi, thiếu dữ liệu và dữ liệu cũ | Tránh hiểu nhầm dữ liệu mất là cảm biến đang báo không có vật |
| Bộ ước lượng | Tính gần đúng vị trí phôi từ cảm biến và các lệnh tốc độ đã gửi | Theo dõi phôi khi không có cảm biến đo liên tục |
| Bộ điều khiển trình tự | Quy định khi nào cấp phôi, đẩy, chạy băng, gắp và thả | Không để các thao tác xảy ra sai thứ tự |
| Bộ dự báo | Tính một số trường hợp chạy thêm hoặc dừng | Cân nhắc việc tiếp tục chạy có còn phù hợp với giới hạn mô hình không |
| Bộ giới hạn tốc độ | Có thể giảm tốc khi dữ liệu chậm hoặc thiếu | Thử giữ khả năng gắp đúng khi đường truyền xấu đi |
| Bộ đánh giá sau dừng | Ghi lý do dừng và những gì còn phải kiểm tra | Không cho rằng mạng trở lại là máy đã sẵn sàng chạy |
| Quy trình đặt lại thử nghiệm | Gửi yêu cầu, nhận xác nhận, rồi có lệnh bắt đầu riêng | Chặn lệnh cũ, lệnh nhầm hoặc lệnh gửi lặp khi tạo một lượt mô phỏng mới |

## Dừng chờ không có nghĩa máy đã hỏng

**HOLD nghĩa là dừng chờ.** Hệ thống dừng vì chưa đủ thông tin hoặc chưa đủ
điều kiện để tiếp tục. Ví dụ: tín hiệu quá cũ, thiếu một cạnh cảm biến, hoặc vị
trí phôi chưa được biết đủ chính xác.

Hệ thống có thể đang quá thận trọng vì thông số chưa được đo thật. Do đó cần
đếm riêng hai việc: **bao nhiêu lượt hoàn tất gắp thả** và **bao nhiêu lượt dừng**.
Một lượt dừng đúng giới hạn kiểm tra không được gọi là một sản phẩm hoàn tất.

## Kết quả đã biết về việc giảm tốc

Trong cùng bộ tình huống mô phỏng đã chọn, mỗi cách có 39 lượt:

| Cách vận hành | Hoàn tất | Dừng chờ |
|---|---:|---:|
| Không bật phần tự giới hạn tốc độ | 16 | 23 |
| Dùng một mức giới hạn cố định | 19 | 20 |
| Tính lại giới hạn theo tuổi dữ liệu và sai số | 15 | 24 |

Cách tính lại giới hạn có ca nhanh hơn, nhưng cũng dừng nhiều hơn khi thời gian
nhận dữ liệu thay đổi. Vì vậy hiện **chưa chọn nó làm cách chạy mặc định**.
Các số trên mô tả những tình huống đã thử, chưa phải tỷ lệ thành công của máy thật.

## Bước mới nhất: đặt lại một chu trình mô phỏng mới

Trước đây chương trình chỉ cho biết sau dừng còn thiếu điều kiện gì. Nay đã bổ
sung được phần gửi yêu cầu đặt lại và kiểm tra xác nhận.

Ví dụ dễ hình dung:

1. Lượt A mất dữ liệu và dừng chờ.
2. Dữ liệu trở lại; chương trình cho phép người kiểm tra xem xét.
3. Trong phép thử, người kiểm tra được giả lập là đã chuẩn bị lại máy/phôi.
4. Một cảnh mô phỏng B được tạo mới và trả xác nhận đúng yêu cầu.
5. Chưa có lệnh bắt đầu riêng thì cảnh B vẫn chưa chạy.
6. Có đúng lệnh bắt đầu thì B chạy một lần và đặt phôi vào hộp.
7. Cảnh A vẫn giữ nguyên; không giả vờ rằng phôi cũ đã tự phục hồi.

Phép thử mới tách **15 tình huống kiểm tra bản tin** khỏi **2 lượt mô phỏng
chuyển động**. Xác nhận của người kiểm tra trong đó vẫn là giả lập.

Bản đóng gói cuối đã chạy lại và đạt 88 phép kiểm tra chương trình cùng phép
thử đặt lại này. Các bộ kiểm tra cũ cũng đạt yêu cầu. Nhật ký điều khiển của 78
ca cũ không đổi so với bản trước. Chi tiết của phép thử mới có trong
[báo cáo được tạo tự động](../output/docker/reset-check_20261031T105102Z_8fce769a/report.md).

## Các báo cáo nên đọc theo thứ tự

1. Bản giải thích này để biết toàn cảnh.
2. [Hướng dẫn đặt lại chu trình mới](dat_lai_chu_trinh_moi.md) để hiểu phần vừa làm.
3. [Đánh giá sau dừng](hold_recovery.md) nếu muốn biết vì sao vẫn chưa được chạy.
4. [Bảng tiến độ chi tiết](dt_core_progress.md) nếu cần tên tệp và các bước trước.

Sau khi chạy phép thử, mở `report.md` trong thư mục kết quả. Những tệp dữ liệu
khác chủ yếu phục vụ kiểm tra chi tiết và chạy lại thí nghiệm.

## Những việc còn thiếu trước khi nói hệ thống hoàn thiện

- Chưa kiểm chứng nối lõi này với PLC, tức bộ điều khiển của máy thật.
- Chưa có đầy đủ xác nhận vị trí trục, chân không, vị trí phôi và liên động thật.
- Chưa tiếp tục được mọi công đoạn của phôi đang dang dở sau khi dừng.
- Chưa chứng minh thời gian phản hồi hoặc độ chính xác trên máy thật.
- Mô hình CAD và mô hình dùng để tính chuyển động chưa khớp toàn bộ chi tiết.

Mỗi phần mới được đóng thành một bản thử Docker, tức một gói có sẵn môi trường
chạy. Chỉ kiểm tra tự động đạt chưa có nghĩa bạn đã nghiệm thu. Các bản trước
được giữ lại để so sánh và quay về khi cần.


## Bản tích hợp phần mềm số 1 — 31/10/2026

Đã ghép sáu mục trước khi kiểm tra chung. Xem [hướng dẫn](ban_tich_hop_phan_mem.md) và [nhật ký từng mục](nhat_ky_cong_viec.md). Trang theo dõi: `/tong_quan.html`. Chưa nghiệm thu máy thật.
