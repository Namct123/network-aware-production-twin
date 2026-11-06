# Nối mô hình ML vào giám sát bất thường

## Mục này làm gì?

Trước đây ML chỉ dự báo một thời điểm phôi tới PS3. Bây giờ đã có mô đun nhận
liên tục tín hiệu cảm biến và lệnh tốc độ, chốt thời điểm dự kiến từ xung PS2,
rồi so với cạnh PS3 thật sự nhận được. Nó trả về:

- Cạnh đến sớm hoặc muộn hơn miền dự kiến.
- Chưa thấy cạnh dù đã quá hạn ở hai mẫu hợp lệ liên tiếp.
- Chưa đủ dữ liệu để đánh giá, kèm lý do: gói quá cũ, mất gói/lịch sử hoặc chất
  lượng tín hiệu không dùng được. Đây không phải kết luận máy đang khỏe.

Đó là API (hàm để chương trình khác gọi) observe/issued trong eta_monitor.py,
tái sử dụng PulseObserver. Nó chỉ đưa cảnh báo tư vấn, chưa được gắn vào chính
sách RuntimeCore, chưa phát lệnh PLC và chưa làm robot tiếp tục khi mất PS3.

## Học gì và giữ nguyên gì?

Không huấn luyện lại Ridge hoặc chọn lại tham số sau khi thấy lỗi. Từ tám bản
ghi hiệu chuẩn bình thường cũ (chỉ bốn cặp bản ghi khác nhau), lấy sai số lớn
nhất cho từng phương án: xung 140,0 ms; bù hằng số 42,9 ms; ML 65,0 ms. Đây
là nửa độ rộng cửa sổ thời gian thực nghiệm, không phải độ tin cậy 95%.

Ba phương án cùng kiểm tra miền đặc trưng, độ mới và lịch sử. Ngoài miền học,
đổi lệnh tốc độ hoặc đổi chiều dài phôi/khoảng cảm biến/chu kỳ lấy mẫu thì
chuyển sang mô hình xung với các biên kỹ thuật đã có. Không tiếp tục áp miền
sai số cũ cho hình học mới. Đứt lịch sử hoặc mất chất lượng thì không có quyền
kết luận từ mô hình. Cần tạo mô đun mới cho chu kỳ/phôi mới.

Các giá trị nằm trong mujoco/models/eta_monitor_v1.json và profile, thay đổi
được. Thay một giá trị không đồng nghĩa đã hiệu chuẩn hoặc kiểm chứng nó.

## Kết quả trên dữ liệu ảo

Dùng lại chín ca bình thường và bốn ca ngoài miền của bước trước; tạo thêm
18 đoạn lỗi (chín mất tín hiệu PS3 và chín băng đứng). Tổng 31 bản ghi, chạy
ba phương án với năm cách truyền dữ liệu = 465 lượt phát lại. Không coi đây
là 465 phép đo độc lập hay thử nghiệm máy thật. Các bản ghi bình thường đã
được xem ở bước trước nên nghiên cứu này là thăm dò, không phải kiểm định mới.

| Phương án | Báo nhầm bình thường, không trễ | Báo bất thường, không trễ | Báo bất thường, trễ 40 ms |
|---|---:|---:|---:|
| Công thức xung | 0/9 | 18/18 | 16/18 |
| Bù hằng số từ train | 0/9 | 18/18 | 18/18 |
| Ridge ML | 0/9 | 18/18 | 18/18 |

Hai ca xung chưa báo khi trễ 40 ms kết thúc bản ghi trước cửa sổ xác nhận;
chưa đủ quan sát để gọi là bỏ sót. Trễ 120 ms: toàn bộ bị từ chối. Mất một
đoạn gói sau xung hoặc mất chất lượng PS3: có dự báo lúc đầu, sau đó ngừng
đánh giá; không tính sự từ chối này thành phát hiện lỗi của ML. Bốn ca ngoài
miền chuyển sang mô hình biên kỹ thuật, không ghi công cho ML.

So trực tiếp 18 ca lỗi không trễ: ML bằng lúc ở 2 lượt và muộn hơn 20–40 ms ở
16 lượt, không sớm hơn lượt nào. Với trễ 40 ms, thứ tự này giữ nguyên. Lý do:
sai số trung bình ML có nhỏ hơn, nhưng miền sai số hiệu chuẩn rộng hơn bù hằng
số. **Dự báo thời điểm tốt hơn chưa chắc báo lỗi nhanh hơn.** Các mẫu cách 20 ms,
không diễn giải chênh lệch thành tốc độ phát hiện vật lý ở mức dưới một mẫu.

Cả chín cặp mất PS3/băng đứng cho đúng cùng tín hiệu đầu vào. Bộ giám sát nhận
ra tiến độ không khớp, chưa chỉ được nguyên nhân. Không công bố độ chính xác
chẩn đoán 100%, tăng năng suất hoặc phục hồi hoàn chỉnh từ các số trên.

## Chạy lại trong Docker ở thư mục dự án

Cần engine Docker hoạt động; với máy hiện tại chạy các lệnh này trong WSL.
Các thư mục đầu ra phải là tên mới, không ghi đè kết quả đã có.

```bash
export DT_IMAGE_TAG=candidate-20261106-eta-monitor-v2
# Tạo bản ghi bình thường, không thay trọng số đã đóng gói.
docker compose run --rm --entrypoint python dt mujoco/study_eta_ml.py --output /app/output/eta_ml_review
# Nạp trọng số/miền đã đóng gói; tạo lỗi, chạy giám sát và lưu từng quyết định.
docker compose run --rm --entrypoint python dt mujoco/study_eta_monitor.py --source /app/output/eta_ml_review --output /app/output/eta_monitor_review
```

Kết quả ở output/docker/eta_monitor_review/results.json và các tệp jsonl từng
mẫu. Chạy lại study_eta_ml tạo mô hình riêng trong output để tái lập, không
ghi đè trọng số đã đóng gói trong mujoco/models.

## Việc tiếp theo có ý nghĩa

Nối cảnh báo tư vấn vào nhật ký của RuntimeCore và đánh giá ngân sách tính
trước khi cho tham gia chọn cấu hình. Với dữ liệu hiện có, ML chưa thắng bù
hằng số về thời gian báo; không chọn ML làm lý do bỏ phản hồi/liên động. Cần
điều kiện động học có sai lệch thay đổi hoặc quan sát độc lập hữu ích, rồi so
lại trên tập mới; không tăng số lần lặp giống nhau để làm đẹp độ chính xác.
