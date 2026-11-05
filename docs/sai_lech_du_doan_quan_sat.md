# So sánh dự đoán với quan sát — kết quả bước đầu

## Material Passport

- Origin Skill: experiment-agent (nguyên tắc phạm vi và tái lập)
- Origin Mode: run, thực hiện mã theo yêu cầu tiếp tục của người dùng
- Origin Date: 2026-11-05
- Verification Status: kết quả JSON và từng hàng tái lập chính xác giữa host và Docker; chưa kiểm chứng vật lý
- Version Label: event_residual_replay_v1

## Mục đích và chức năng

`mujoco/innovation.py` dự đoán miền vị trí tâm phôi từ cạnh xuống của PS2 vật lý (tên logic ps1), lịch sử lệnh băng dọc và miền sai số. Bộ này kiểm tra cạnh lên ở PS3 vật lý (logic ps2) có phù hợp miền dự đoán không; nếu miền đã qua mốc mà vẫn không thấy cạnh, ghi dấu hiệu bất thường.

Dự đoán không lấy vị trí thật, tốc độ áp dụng, loại lỗi hoặc ước lượng đã được PS3 sửa lại. Lệnh tại cùng nhịp chỉ được ghi SAU khi kiểm tra quan sát; không dùng lệnh tương lai. Bộ chấm ngoài mới đọc vị trí thật để đếm mẫu nằm trong khoảng.

## Thiết kế đã khóa trước khi phát lại

- Nguồn: 21 phiên sensor_drive_20261104_v2, bảy ca × ba lượt. Đây là phát lại dữ liệu đã có, không chạy mới 21 máy MuJoCo. Các lượt lặp xác định, không phải 21 quan sát độc lập để suy ra độ chính xác ngoài thực tế.
- Hai cấu hình sửa được trong mujoco/experiments/residual_20261105.json: miền hẹp giả định (gain 0,95–1,05, drift 0,005 m/s); miền engineering của profile (0,8–1,2, drift 0,02 m/s). Không thay các ngưỡng sau khi xem kết quả.
- Bổ sung sai số mốc, quãng di chuyển trong một nhịp lấy mẫu, biến thiên lệnh và sai số dừng. Xác nhận thiếu cạnh qua hai mẫu liên tiếp; cạnh đến sai thời điểm được ghi ngay tại mẫu cạnh.
- Tham chiếu đơn giản: deadline theo khoảng đường/tốc độ danh định + 0,2 s. Đây chỉ là timeout một sự kiện, chưa phải bộ điều khiển thích nghi mạnh và chưa công bằng để kết luận DT vượt điều khiển truyền thống.
- Dừng phân tích ở HOLD đầu tiên của bộ điều khiển đã tạo dữ liệu. Không báo trước mốc đó có thể là cửa sổ bị cắt, không kết luận chắc chắn bỏ sót vĩnh viễn.
- Không nối bộ mới vào quyền điều khiển, không huấn luyện ML, không bypass cảm biến và chưa có cấu hình PLC chạy máy thật.

## Kết quả (lượt 01; hai lượt còn lại trùng kết quả)

| Ca | Miền hẹp: báo đầu (s) | Miền profile: báo đầu (s) | Timeout tham chiếu (s) |
|---|---:|---:|---:|
| feed_drive_stall | chưa báo/không áp dụng | chưa báo/không áp dụng | chưa báo/không áp dụng |
| feed_sensor_missing | chưa báo/không áp dụng | chưa báo/không áp dụng | chưa báo/không áp dụng |
| long_drive_stall | 6.84 | chưa báo/không áp dụng | 6.86 |
| nominal | chưa báo/không áp dụng | chưa báo/không áp dụng | chưa báo/không áp dụng |
| pickup_sensor_high | 5.40 | 5.40 | chưa báo/không áp dụng |
| pickup_sensor_missing | 6.84 | chưa báo/không áp dụng | 6.86 |
| upstream_sensor_missing | chưa báo/không áp dụng | chưa báo/không áp dụng | chưa báo/không áp dụng |

Ở cặp PS3 không báo/băng dọc đứng, miền hẹp báo lúc 6,84 s; timeout tham chiếu báo 6,86 s. Chênh đúng một nhịp 20 ms, phụ thuộc giả định và slack đã chọn; không coi là lợi thế thực tiễn đã chứng minh. Miền rộng chưa đủ cơ sở báo trước HOLD cũ ở 6,96 s. PS3 luôn báo bị chỉ ra ngay ở 5,40 s do trái miền dự đoán; bộ điều khiển cũ cũng đã chặn ca này ngay nhịp đó.

Ca bình thường không có cảnh báo ở cả hai miền; mỗi lượt có 63/63 mẫu sau mốc nằm trong khoảng. Khi PS3 không báo nhưng băng vẫn chạy, 79/79 mẫu nằm trong khoảng ở cả hai miền. Khi băng dọc đứng, chỉ 4/79 (hẹp) và 5/79 (rộng) mẫu nằm trong khoảng. Đây là số mẫu của một quỹ đạo mô phỏng, không phải khoảng tin cậy 95% hoặc độ chính xác chẩn đoán.

Ba ca không có mốc đầu vào hợp lệ cho bộ này (hai ca cấp phôi và PS2 không báo) được ghi no_anchor; không biến thành kết luận hệ khỏe. Dữ liệu cũ/thiếu/chất lượng không dùng được được tách riêng, không tự đổi thành bit false.

## Kết luận và việc tiếp theo

Đã có bộ so sánh độc lập, nhân quả và đo được ảnh hưởng của giả định sai số. Chưa có bằng chứng duy trì sản xuất tốt hơn, ML tốt hơn quy tắc, hoặc tách được lỗi cảm biến với mất chuyển động: hai ca cùng quan sát vẫn cùng kết quả báo.

Ưu tiên tiếp theo: tạo tập điều kiện bình thường biến thiên riêng để hiệu chuẩn khoảng, giữ tập kiểm tra chưa dùng để chọn ngưỡng; sau đó thử kín ba bộ điều khiển cùng thông tin. Nếu muốn tiếp tục khi mất một mốc, phải chứng minh còn đủ quan sát độc lập hoặc giới hạn bất định; không dùng việc thu nhỏ khoảng để giả tạo điều kiện tiếp tục.

## Chạy lại

```powershell
# Trên host Python (không cần MuJoCo vì chỉ phát lại)
python mujoco/study_residual.py --source output/docker/sensor_drive_20261104_v2 --output output/residual_new_run
python -m unittest discover -s mujoco -p test_innovation.py -v
```

Chọn thư mục mới, bộ thử từ chối ghi đè. Kết quả cuối: output/docker/residual_20261105_final; pilot giữ riêng. Manifest ghi SHA-256 của kế hoạch, mã và từng tệp đầu vào. Kiểm tra byte ban đầu khác do Windows CRLF/Linux LF; JSON và từng hàng có giá trị trùng chính xác, không sửa dữ liệu để khớp.

Docker: candidate-20261105-residual-focus; chưa có nghiệm thu người dùng. Bản accepted và quyền điều khiển hiện tại giữ nguyên.
