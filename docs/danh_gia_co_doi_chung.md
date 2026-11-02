# Đánh giá thời gian dự báo và phản ứng khi có lỗi

Bộ mới làm ba việc: đo thời gian dự báo, chạy các tình huống có đối chứng,
và xuất báo cáo dễ đọc. Không đổi bộ điều khiển mặc định hay ngưỡng theo kết quả.

## Cách chạy

Trong môi trường MuJoCo đã cài:

```text
python mujoco/qualify.py --output output/docker/qualification-check_local
```

Hoặc Docker thử nghiệm:

```text
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode build
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode qualification-check
```

Dùng --config để chọn hồ sơ máy và --plan để chọn kế hoạch JSON. Tệp mặc định:
`mujoco/experiments/qualification_20261102.json`. Đầu ra phải chưa tồn tại.
Cả kế hoạch và mọi hồ sơ thử đều được kiểm tra trước khi bắt đầu.

## Đọc bảng thời gian

Hai nhánh nhận cùng vị trí/tốc độ/bất định giả lập: nhánh tính 1 chiều và nhánh
MuJoCo băng/phôi. Chúng có mức chi tiết khác nhau nên thời gian tính không phải
thước đo độ chính xác vật lý. Mỗi trường hợp có 1 lượt làm nóng, 5 lượt đo;
có 3 trường hợp. Hồ sơ hiện tại có hạn 20 ms; một nhóm riêng dùng hạn chức năng
1 giây để xem có chạy đủ 54 trường hợp hay không. Hạn rộng không được tự đưa vào
điều khiển. Cấu hình thực tế khác sẽ có hạn tương ứng trong bảng dữ liệu gốc.

Thời gian ngoài hàm gồm phần gọi hàm và tạo kết quả; phần khởi tạo mô hình,
nhập thư viện và làm nóng không trộn vào bảng lượt đo. Kết quả từng lượt vẫn
được lưu. p95 là giá trị theo thứ hạng chứa 95% số mẫu quan sát, không phải
thời gian lớn nhất bảo đảm. Đo chạy tuần tự trên máy hiện tại, chưa thử tải đồng
thời hoặc thời gian thực. Gói MuJoCo không được coi là tính kịp chỉ vì ra lệnh HOLD.

## Đọc phần đối chứng

6 tình huống: bình thường, mất tín hiệu quang ở điểm gắp, trễ 20 ms, mất 5% bản tin,
băng thật trong mô phỏng chậm/nhanh hơn lệnh 15%. Mỗi tình huống dùng 2 seed
(mã tạo nhiễu) và bật/tắt giới hạn tốc độ tái cấu hình cố định: tổng 24 lượt.
Các seed không làm tình huống tất định trở thành những thí nghiệm độc lập.
Các độ lệch là mức thử do thiết kế, không phải số đã đo trên máy thật.

Đây không phải so sánh DT với PLC tuần tự. Cả hai chính sách vẫn dùng cùng
bộ ước lượng và giám sát dự báo. Hạn tính phần này là 1 giây để đánh giá chức
năng, không phải chứng minh điều khiển đáp ứng 20 ms. Mặc định chạy một phôi,
cho phép giả định trục/chân không để đi hết chu trình; máy thật chưa được kiểm chứng.

DONE là hoàn tất; HOLD là dừng chờ. Dừng khi không có lỗi cảm biến chưa có nghĩa
là báo nhầm: mạng hoặc bất định vẫn có thể cần dừng. Không tính tăng tốc bằng
cách so một lượt hoàn tất với một lượt dừng. Lượt vi phạm tiêu chí vẫn giữ nguyên.

## Tệp kết quả

- report.md: báo cáo tiếng Việt, phần dễ đọc trước tiên.
- qualification.json: tổng hợp để trang web đọc, không phải giấy nghiệm thu.
- benchmark.json, timing.jsonl và timing.csv: số đo từng lượt; lượt làm nóng có nhãn riêng.
- manifest.json: phiên bản môi trường và dấu kiểm tra nguồn; plan.json/base_config.json giữ đầu vào.
- study/: hồ sơ, dấu vết từng lượt và so sánh chính sách đã có sẵn.

Mở trang /tong_quan.html bằng web/server.py để xem số mới dưới output/docker,
hoặc chọn qualification.json ngay trong trình duyệt. Trang chỉ đọc, không gửi lệnh máy.
Nếu bị ngắt giữa chừng, timing.jsonl và thư mục từng lượt vẫn còn; thiếu qualification.json
thì không được gọi là bản đánh giá hoàn tất. Chưa có độ chính xác phát hiện lỗi máy thật,
không khẳng định tốc độ hay an toàn ngoài các tình huống đã thử.
