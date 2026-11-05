# Hiệu chuẩn miền dự đoán trên đoạn băng PS2 → PS3

## Material Passport

- Origin Skill: experiment-agent (nguyên tắc thiết kế và tái lập)
- Origin Mode: run theo yêu cầu tiếp tục nghiên cứu
- Origin Date: 2026-11-05
- Verification Status: 37 điều kiện và phân tích tái lập chính xác trong Docker; chưa kiểm chứng vật lý
- Version Label: optical_interval_calibration_v1

## Đã làm gì?

Tách đoạn theo dõi phôi trên băng dọc để hiệu chuẩn mà không bị HOLD của chu trình cũ cắt ngắn. Phôi bắt đầu trước PS2 vật lý, băng chạy theo lệnh cố định trong một cửa sổ đã đặt. Đây là bệ thử riêng, không phải 37 chu trình gắp–thả hoàn chỉnh.

Chín điều kiện bình thường dùng tốc độ đặt 0,12/0,16/0,20 m/s và hệ số đáp ứng băng 0,88/1,00/1,12. Bộ hiệu chuẩn chỉ nhận thời điểm cạnh xuống PS2, cạnh lên PS3, khoảng cách hình học và tích phân lệnh. Nhãn hệ số thật và vị trí phôi không được dùng để fit.

Sau chín ca, lưu sealed_calibration.json và SHA-256 trước khi tạo tập kiểm tra. Miền hệ số suy ra là **0,830508–1,202830**. Độ trôi 0,005 m/s và sai số mốc vẫn là các giả định đặt trước, chưa học hết từ dữ liệu. Không gọi đây là khoảng tin cậy thống kê.

## Tách dữ liệu và đối chứng

- 9 ca hiệu chuẩn bình thường.
- 8 ca bình thường chưa dùng để fit: tốc độ 0,14/0,18 m/s, hệ số 0,92/1,08 và ma sát trượt phôi 0,8/1,2. Đây là lưới điều kiện thiết kế xác định; các giá trị đều nằm trong miền để thử nội suy, không phải mẫu đại diện cho nhà máy.
- 16 ca lỗi trên tám điều kiện kiểm tra: PS3 luôn không báo hoặc mất chuyển động băng dọc sau cạnh xuống PS2. Nhãn chèn lỗi chỉ ở bộ thử.
- 4 ca thay đổi điều kiện ngoài miền hiệu chuẩn: hệ số 0,75/1,25 với tốc độ 0,14/0,18. Không chèn hỏng cảm biến; báo ở đây là dấu hiệu mô hình không khớp, không được gọi là xác định linh kiện hỏng.
- Các ca dùng cùng quan sát cho miền hẹp cũ, miền profile cũ, miền đã fit và timeout một sự kiện (+0,2 s). Không gắn các bộ này vào quyền điều khiển, nên không kết luận năng suất/khả năng hồi phục.
- Sau khi xem pilot, bổ sung đối chiếu giữ gain profile 0,8–1,2 nhưng dùng cùng drift 0,005 m/s. Đây là **phân tích bổ sung sau pilot**, công bố rõ; không dùng kết quả này để sửa tham số đã niêm phong.

## Kết quả trên dữ liệu kiểm tra

| Phương án | Báo trên 8 ca bình thường | Báo trên 16 ca lỗi | Báo trên 4 ca ngoài miền | Độ rộng trung bình khoảng trên ca bình thường |
|---|---:|---:|---:|---:|
| Fit từ mốc quang | 0/8 | 16/16 | 2/4 | 76.8 mm |
| Miền hẹp giả định cũ | 0/8 | 16/16 | 4/4 | 35.2 mm |
| Miền profile cũ | 0/8 | 0/16 | 0/4 | 109.8 mm |
| Gain profile, cùng drift (bổ sung) | 0/8 | 16/16 | 0/4 | 80.9 mm |
| Timeout một sự kiện | 0/8 | 16/16 | 2/4 | Không có khoảng |

Cả bốn bộ có khoảng đều bao phủ 766/766 mẫu có mốc trong tám ca bình thường. Các mẫu gần nhau trên một quỹ đạo có tương quan; không đổi số này thành xác suất 100% hoặc cam kết bao phủ 95% trên máy thật.

Bộ fit báo lỗi sau 1,48–1,90 s kể từ chèn. Nó **chậm hơn timeout đơn giản 0,16–0,26 s** ở các ca lỗi này. Miền hẹp giả định cũng báo đủ 16 ca, sớm hơn hoặc bằng timeout. Không có bằng chứng bộ fit thắng các đối chứng đó về thời gian phát hiện.

Trên bốn ca ngoài miền, mức bao phủ mẫu của bộ fit là 230/377, miền hẹp 33/377, profile cũ 377/377, đối chiếu cùng drift 298/377. Profile rộng giữ được bao phủ nhưng không chỉ ra thay đổi; khoảng hẹp phát hiện nhiều thay đổi hơn nhưng không còn bao phủ quỹ đạo. Đây là đánh đổi cần kiểm tra, không phải một phương án luôn thắng.

## Phân biệt hiệu ứng tham số học được với giả định đặt trước

So cả gói mới với profile cũ, độ rộng trung bình giảm khoảng 30,1%. Tuy nhiên hai gói khác cả gain lẫn drift; không được quy toàn bộ mức giảm này cho học từ dữ liệu. Khi giữ cùng drift, gain fit chỉ giảm độ rộng khoảng **5,1%** (80,9 → 76,8 mm). Phần còn lại chủ yếu do chọn drift nhỏ hơn; drift đó vẫn cần hiệu chuẩn độc lập.

Khoảng rộng trung bình 76,8 mm chưa đủ cơ sở để gắp chính xác; không dùng việc phát hiện đủ 16 ca để cho phép bỏ PS3 và tiếp tục gắp. Hai lỗi cùng quan sát vẫn cho cùng dấu hiệu, chưa xác định được cảm biến hay băng tải hỏng.

## Kết luận và bước tiếp theo

Đã có đường hiệu chuẩn từ tín hiệu quang, có tập giữ riêng và cơ chế niêm phong trước đánh giá. Kết quả tốt trong phạm vi hẹp: không báo nhầm trong tám ca kiểm tra, báo đủ 16 ca lỗi; đồng thời đã xác định rõ độ trễ và thất bại bao phủ ngoài miền.

Tiếp theo nên thử suy tốc độ theo từng chu kỳ từ độ rộng xung PS2, dùng kích thước phôi đã biết, thay vì một miền gain chung cho tất cả điều kiện. Phải tính sai số lấy mẫu, góc phôi và kích thước, rồi kiểm tra riêng trước khi nối vào chính sách. Đây là công việc tiếp theo, chưa triển khai trong phiên bản này. Sau đó mới thử kín chọn tốc độ/chế độ và bổ sung suy giảm mạng; vẫn phải so với quy tắc thích nghi dùng cùng thông tin.

Chưa có bộ phân loại ML được huấn luyện, dữ liệu camera, ghi PLC, chạy kín khôi phục hoặc kiểm chứng vật lý. Không thêm các phần đó chỉ để có tên công nghệ.

## Mã, dữ liệu và cách chạy

- Kế hoạch nhập sửa được: mujoco/experiments/interval_calibration_20261105.json.
- Bộ thử/fit: mujoco/calibrate_residual.py; từ chối trùng điều kiện train/test, số không hợp lệ, trên 100 ca hoặc trên 10 s mô phỏng/ca.
- Bộ tính lại độc lập: mujoco/analyze_calibration.py; khôi phục đúng 10.164 kết quả mẫu–bộ quan sát từ tín hiệu và lệnh; vị trí thật chỉ dùng chấm mức bao phủ.
- Bản cuối: output/docker/interval_calibration_20261105_final và output/docker/interval_calibration_20261105_analysis.json; pilot giữ riêng.
- Docker candidate-20261105-interval-calibration: 149 kiểm tra lõi, 10 web đạt; kết quả 37 ca và phân tích khớp chính xác bản WSL pilot. 117 tệp MuJoCo trước đó giữ nguyên; bản accepted không đổi.

```bash
# Trong WSL có môi trường MuJoCo, chọn thư mục đầu ra mới
python mujoco/calibrate_residual.py --output output/calibration_new
python mujoco/analyze_calibration.py --source output/calibration_new --output output/calibration_new_analysis.json
```

Bộ thử không ghi đè thư mục đã có. Kết quả chưa được người dùng nghiệm thu; chỉ có candidate.
