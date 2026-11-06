# Mô hình ML đầu tiên: sửa sai lệch thời điểm phôi tới PS3

## Đã xây gì?

Đã huấn luyện hồi quy Ridge bằng NumPy có sẵn để dự đoán phần sai lệch của công
thức thời gian đến PS3. Đây là mô hình ML có trọng số học từ dữ liệu, không chỉ
là kiểm thử hoặc gán quy tắc. Nó vẫn chỉ đưa khuyến nghị, chưa ghi lệnh PLC.

Từ xung PS2 đầy đủ, lấy ba đặc trưng: thời gian che cảm biến, tốc độ đã ra lệnh
và tích của hai đại lượng. Chốt đặc trưng khi kết thúc xung PS2, trước PS3.
Nhãn huấn luyện là thời điểm cạnh PS3 thực sự được ghi, không phải pose MuJoCo.
Mô hình học sai lệch giữa nhãn đó với ETA từ xung. Vì bản ghi lấy mẫu 20 ms,
đích đang dự báo là thời điểm mẫu báo cạnh, không phải thời điểm vật lý chính
xác nằm giữa hai mẫu.

## Tách dữ liệu

61 lượt mô phỏng đoạn băng bình thường: 32 train, 8 validation chọn lambda,
8 calibration để đặt miền sai số thực nghiệm, 9 test và 4 ca lệch miền. Bộ ba
speed/gain/friction không trùng giữa các tập. Mọi điều kiện là lưới thiết kế
xác định, không phải mẫu ngẫu nhiên đại diện nhà máy. Kiểm tra hash bản ghi cho
thấy chỉ có 16/4/4/9/4 cặp quan sát–lệnh khác nhau tương ứng: thay đổi ma sát ở
ba tập đầu cho bản ghi giống nhau. Không có cặp bản ghi trùng giữa các tập;
không coi các bản ghi lặp trong tập là lần đo độc lập.

Scaler và trọng số chỉ fit trên train. Chọn lambda trong 0,01/0,1/1/10 bằng
validation, khóa model trước calibration/test. Miền sai số là max residual
trên calibration riêng, khoảng 65 ms; không gọi là khoảng tin cậy 95%.

## Kết quả và đối chứng

| Phương án | MAE trên test 9 ca | MAE trên 4 ca lệch miền |
|---|---:|---:|
| Động học theo lệnh danh định | 105,7 ms | 330,0 ms |
| Công thức theo xung PS2 | 98,5 ms | 83,3 ms |
| Bù sai lệch trung bình từ train | 18,1 ms | 28,5 ms |
| Ridge học phần dư | 15,4 ms | 38,3 ms |

Bù hằng số được thêm sau pilot để kiểm tra phần cải thiện có chỉ là sửa bias
hay không; ghi rõ đây là đối chứng hậu kiểm. Nó chỉ dùng train để tính offset,
không thay các đặc trưng, lambda hoặc trọng số Ridge sau khi xem test.

So với công thức xung, mức giảm lớn; so với bù hằng số, ML chỉ tốt hơn khoảng
2,7 ms trên 9 ca. Ngoài miền, ML kém hơn bù hằng số. Cả 4 ca lệch miền có đặc
trưng nằm ngoài hộp đặc trưng train và chỉ được chấm để chẩn đoán, không tự cho
phép điều khiển. Miền sai số bao phủ 9/9 và 4/4 nhưng không suy thành xác suất
hoặc bảo đảm máy thật. Chưa có kiểm định thống kê hay kết quả tăng năng suất.

## Dùng mô hình đã huấn luyện

- Code: mujoco/eta_ml.py, study_eta_ml.py; kế hoạch: experiments/eta_ml_20261106.json.
- Trọng số: mujoco/models/eta_residual_v1.json; không sửa tay để làm đẹp kết quả.
- Miền sai số: mujoco/models/eta_error_envelope_v1.json; provenance kèm theo.
- predict_from_pulse nhận pulse_fit đã có, tốc độ và khoảng cách; không cần
  chờ PS3 hoặc đưa nhãn đích vào dự báo. Chỉ gọi với xung và lịch sử còn hợp lệ;
  cờ outside-training-domain và tuổi dữ liệu phải được xử lý trước khi dùng.

```python
import json
from pathlib import Path
from eta_ml import predict_from_pulse
model = json.loads(Path('mujoco/models/eta_residual_v1.json').read_text())
# pulse_fit lấy từ PulseObserver khi usable_for_monitoring là True.
# result = predict_from_pulse(model, pulse_fit, issued_speed, sensor_distance)
```

Bản candidate-20261106-eta-ml-v2 chứa trọng số thật và API chỉ dùng xung PS2;
không huấn luyện lại khi đóng gói. Dữ liệu/training origin ở
output/docker/eta_ml_20261106_final. Lượt đầu lỗi cấu hình trước train_00 giữ
ở output/eta_ml_20261106_pilot; bệ thử đã sửa cấu hình cục bộ, không sửa profile
vận hành. Bản WSL thành công giữ ở pilot_v2, Docker tái lập sai số tới 1e-8 ms.

## Bài báo và bước tiếp theo

Bổ sung phần phương pháp Ridge, tách tập, bảng đối chứng và giới hạn vào body.tex;
bảng tự sinh từ receipt, claim/evidence có hash và human_verification pending.
Title/abstract vẫn riêng và không đổi, phần kiểm chứng vật lý còn trống. Chưa
coi bản thảo là được tác giả duyệt hay sẵn sàng nộp.

Tiếp theo mới kết nối ETA và miền sai số vào mô đun đánh giá bất thường, với
fallback khi ngoài miền/dữ liệu không hợp lệ và đối chứng bù hằng số. Không
coi cải thiện ETA là giải quyết được cặp cảm biến hỏng/băng đứng cùng tín hiệu.
