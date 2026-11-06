# Mở và chạy gói nghiên cứu giám sát đã thu gọn

Gói này tập trung vào phương pháp giám sát sự kiện. MuJoCo chỉ là bệ thử ảo.
Không có điều khiển PLC thật, CAD authoring hoặc mô phỏng toàn chu trình trong
gói chạy. Chưa phải bản được người dùng nghiệm thu.

## Chuẩn bị

Giải nén, mở terminal Linux/WSL ở thư mục chứa research_scope.json. Cần Docker
engine đang hoạt động và Python3 để tạo gói build. Máy hiện tại dùng WSL
Ubuntu-24.04, dự án đầy đủ ở /mnt/d/Projects/network-aware-production-twin.

```bash
python3 docker/build_image.py --scope monitoring --tag candidate-20261106-pulse-model-audit
```

## Kiểm tra mô đun và tạo lại bản ghi

```bash
IMG=production-twin-dt:candidate-20261106-pulse-model-audit
docker run --rm --network none --read-only "$IMG"
mkdir -p output/docker
# Cho user10001 trong container ghi được; chỉ cấp quyền cho thư mục đầu ra này.
chmod a+rwx output/docker
docker run --rm --network none --read-only -v "$PWD/output/docker:/app/output" "$IMG" mujoco/study_eta_ml.py --output /app/output/fresh_ml
docker run --rm --network none --read-only -v "$PWD/output/docker:/app/output" "$IMG" mujoco/study_eta_monitor.py --source /app/output/fresh_ml --output /app/output/fresh_monitor
```

Tên thư mục phải chưa tồn tại; chương trình từ chối ghi đè thí nghiệm cũ. Bước
đầu tạo61 đoạn bình thường và trọng số riêng để tái lập; bước sau dùng trọng
số/miền đã đóng gói, thêm18 đoạn lỗi và chạy465 lượt phát lại. Xem results.json
và từng tệp jsonl trong output/docker/fresh_monitor. Đây vẫn cùng bộ điều kiện
đã xem, không phải xác nhận trên tập mới.

## Đọc mã từ đâu?

- event_window.py: lõi không phụ thuộc thiết bị, nhận miền sự kiện và tín hiệu.
- eta_monitor.py: bộ nối xung quang, điều kiện dữ liệu và lựa chọn dự phòng.
- eta_ml.py: Ridge học phần dư; không mặc định tốt hơn bù hằng số.
- models/eta_monitor_v1.json: miền sai số và bối cảnh hiệu chuẩn; profile trong
  configs/ thay đổi được, nhưng thay profile có thể khiến miền cũ bị từ chối.

Tách lõi chỉ cho phép viết bộ nối khác. Cần mô hình, ánh xạ, hiệu chuẩn và kiểm
chứng mới trước khi dùng với xi lanh hoặc robot khác. Không coi kiểm tra phần
mềm với tên sự kiện khác nhau là đã thử nhiều loại máy.

Đọc docs/pham_vi_bai_bao_20261106.md trước khi mở rộng. Bản paper hiện hành và
PDF đi cùng gói; thông tin tác giả/đơn vị và phần vật lý cần người phụ trách điền.


## Phép so mới đã khóa trước chạy

Trong cùng image, chạy study_network_clock.py --output /app/output/clock_review
với volume đầu ra như trên. Tạo36 bản ghi và720 lượt so, không cần tạo dữ liệu
học cũ trước. Đọc docs/doi_chung_thoi_gian_20261106.md để thấy cả kết quả báo
nhầm và thiếu đầu vào. Bộ này đã được xem; chạy lại không làm nó thành tập mới.

Hậu kiểm mô hình: audit_pulse_model.py --source /app/output/clock_review --output /app/output/pulse_audit_review. Mã đọc vị trí chấm để rà giả thiết, không cấp dữ liệu đó cho bộ dự báo online.
