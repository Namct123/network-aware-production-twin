# Nghiên cứu cảm biến không báo và băng tải đứng — 04/11/2026

Đã chạy 7 tình huống, mỗi tình huống lặp 3 lần trên cùng cấu hình MuJoCo. Không thay ngưỡng, tham số vật lý hoặc lõi điều khiển. Đây là bộ phản ví dụ được chọn để kiểm tra giới hạn phân biệt nguyên nhân, không phải mẫu lỗi ngẫu nhiên ngoài nhà máy.

## Kết quả thời gian

| Tình huống | Từ lúc chèn đến dừng (ms) | Từ bất đồng cảm biến đầu tiên đến dừng (ms, chỉ bộ chấm biết) | Lý do dừng |
|---|---:|---:|---|
| Đối chứng bình thường | Không áp dụng | Không áp dụng | Chưa có xác nhận trục XY/đầu hút |
| PS1 trên đầu đẩy không báo | 2220 | 200 | Hết thời hạn chờ tín hiệu cấp phôi |
| Băng cấp phôi đứng | 2220 | Không áp dụng | Hết thời hạn chờ tín hiệu cấp phôi |
| PS3 tại điểm gắp không báo | 1560 | 320 | Không thấy mốc cảm biến như mô hình dự kiến |
| Băng dọc đứng | 1560 | Không áp dụng | Không thấy mốc cảm biến như mô hình dự kiến |
| PS3 luôn báo có phôi | 0 | 0 | Thời gian qua hai cảm biến không hợp lý |
| PS2 trước điểm gắp không báo | 1800 | 1640 | Có tín hiệu điểm gắp nhưng thiếu mốc cảm biến trước |

Mốc chèn là lúc bộ thử bắt đầu ép tín hiệu hoặc băng tải, có thể trước khi phôi tới cảm biến. Bởi vậy 2.220 ms từ lúc chèn không đồng nghĩa CPU mất 2.220 ms để xử lý. Ở ca PS1 không báo, bộ chấm thấy tia quang đáng lẽ đổi trạng thái tại 2,04 s; hệ dừng ở 2,24 s, chênh 200 ms. Bộ chấm biết điều này từ mô phỏng; lõi DT không được biết tia quang lý tưởng hoặc vị trí phôi thật.

Giá trị 0 ms ở PS3 luôn báo chỉ có nghĩa phản ứng trong cùng nhịp lấy mẫu 20 ms, không phải thời gian CPU bằng 0. Ca bình thường không có lỗi được chèn và dừng trước chuyển động XY/đầu hút chưa có xác nhận. Không tính ca đó như một lỗi mạng hay lỗi cảm biến.

## Hai nguyên nhân khác nhau có cùng dấu vết

Cả 6 cặp đều có cùng toàn bộ khung tín hiệu và quyết định được ghi tới lần dừng đầu:

- PS1 không báo và băng cấp phôi đứng: vị trí phôi tại mốc dừng lệch khoảng 35,4 cm.
- PS3 không báo và băng dọc đứng sau mốc PS2: vị trí phôi tại mốc dừng lệch khoảng 24,8 cm.

Vị trí chỉ được ghi trong truth_evaluator_only.jsonl. Bộ điều khiển nhận các trạng thái số và trạng thái chưa có dữ liệu, không nhận nhãn lỗi, lệnh băng tải đã bị ép ở plant hoặc tọa độ phôi. Lệnh DT phát ra và lệnh áp vào mô phỏng được tách riêng; bộ thử không sửa lệnh trong lịch sử của DT.

Kết luận phù hợp là hệ phát hiện triệu chứng không khớp và dừng chờ. Với riêng lịch sử tín hiệu đã ghi trong các cặp này, chưa thể khẳng định cảm biến hỏng hay chuyển động bị mất. Chạy dự báo nhanh hơn không tự tạo thêm bằng chứng để tách hai nguyên nhân. Không biến 6/6 cặp giống hoặc 21 ca thực thi thành độ chính xác chẩn đoán.

## Kiểm tra và giới hạn

143 kiểm tra lõi, 8 kiểm tra web, kiểm tra tích hợp và 2 kiểm tra giao hàng đạt. Bộ đọc độc lập tính lại 6 cặp và kiểm tra các hàng tín hiệu/trạng thái mô phỏng khớp dấu thời gian. Bộ chấm vị trí ghi nhận phôi còn trong vùng đỡ sau dừng ở 21/21 ca. Đây là tiêu chí vị trí trong mô phỏng, không phải chứng nhận an toàn, tiếp xúc hay độ chính xác trên máy thật.

Cờ passed trong sensor_drive_study.json xác nhận các ca được thực thi đủ và đạt trạng thái cuối quy định; không có nghĩa đã phân loại đúng 21 lỗi. Ba lần lặp dùng cùng mô hình và lịch chèn, không phải ba máy độc lập. Mô hình ma sát, truyền động, hình học và vị trí đầu vào vẫn có tham số chưa kiểm chứng vật lý. CAD V5 chưa được coi là đồng bộ đầy đủ với mô hình này.

Bảy tình huống được chạy riêng; không có nghĩa DT đang nhận dạng bảy loại lỗi đồng thời. 54 kịch bản dự báo 1D là biến thiên của mô hình dừng, không phải 54 loại hỏng cảm biến.

## Mã nguồn và cách chạy

- mujoco/study_sensor_drive.py: plant vòng kín và các tình huống cảm biến/truyền động.
- mujoco/experiments/sensor_drive_20261104.json: số lần lặp và danh mục tình huống.
- scripts/analyze_sensor_drive.py: chấm độc lập, tính lại cặp và tách các mốc thời gian.

Trong môi trường Python đã cài MuJoCo:

```text
python mujoco/study_sensor_drive.py --output output/thu_cam_bien_moi
python scripts/analyze_sensor_drive.py --input output/thu_cam_bien_moi --output output/cham_cam_bien_moi.json
```

Thư mục/tệp đầu ra phải mới; tham số máy vẫn sửa qua profile và --config. Bộ thử này truyền khung cảm biến trực tiếp, không đưa thêm nhiễu mạng; các nghiên cứu mạng trước vẫn được giữ riêng.

Dữ liệu đã chạy: output/docker/sensor_drive_20261104_v2. Kiểm tra và bộ chấm: output/docker/sensor_drive_validation_20261104_v2. Docker mới là candidate-20261104-sensor-drive-v2; chờ kiểm nghiệm, giữ nguyên ảnh accepted cũ.

## Tách thông tin phiên khỏi nhãn lỗi

Lượt pilot dùng tên phiên có chứa tên tình huống; lõi hiện tại không đọc tên đó
để chẩn đoán. Bản cuối vẫn đổi sang 21 mã UUID (định danh ngẫu nhiên), khác nhau và không chứa
nhãn loại lỗi, rồi chạy lại đủ 21 ca. Cả 21 chuỗi quan sát và 21 chuỗi quyết định
logic giữ nguyên so với pilot; chỉ bỏ thời gian CPU khỏi phép so. Nhãn lỗi vẫn
được lưu trong hồ sơ của bộ thử, tách khỏi đầu vào và thông tin phiên của lõi RuntimeCore.

Ca băng đứng được tạo bằng việc ép lệnh áp vào bề mặt băng về 0 trong mô phỏng,
trong khi lịch sử lệnh của DT vẫn ghi lệnh chạy. Phôi tiếp tục tuân theo quán tính
và ma sát của MuJoCo. Đây là giả lập mất tác động truyền động; mô hình lỗi điện,
mômen động cơ hoặc kẹt cơ khí chi tiết chưa được kiểm chứng.

Dữ liệu pilot giữ ở sensor_drive_20261104; dữ liệu bản cuối ở
sensor_drive_20261104_v2. Không cộng hai bản thành 42 phép thử độc lập.
