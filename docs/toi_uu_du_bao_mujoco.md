# Tối ưu phần dự báo MuJoCo

Mục tiêu: giảm thời gian gọi Python lặp lại, giữ mô hình và các giá trị thiết kế.
Bản gốc vẫn nằm trong physics_predictor.py với tên ReferenceMuJoCoBeltPredictor.
Bản MuJoCoBeltPredictor mới gom kịch bản có cùng chỉ số bước dừng rồi dùng bộ
rollout đã có trong MuJoCo. Một nhóm tính phần chạy trước dừng và phần băng dừng,
giữ nguyên cách đặt lại bộ giải lúc chuyển mô hình. Không dùng GPU. native_threads cho chọn 1–16 luồng, mặc định 1; thử nghiệm ghi riêng 1/4/8 luồng.

Vẫn có 54 kịch bản, bước vật lý 2 ms và chân trời 0,5 giây trong hồ sơ đang dùng.
Số bước tính thực sự được kiểm tra. Biên được kiểm tra trên cả điểm đầu và mọi
bước được trả về, không chỉ điểm cuối. Dữ liệu không hữu hạn hoặc thời gian ngừng
bước bị từ chối. Nhánh điều khiển mặc định vẫn là dự báo một chiều.

## Chạy đối chiếu

```text
python mujoco/check_physics_optimization.py --output output/docker/physics-check_local
```

Hoặc sau khi dựng ảnh thử nghiệm:

```text
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode build
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode physics-check
```

Đầu ra phải chưa tồn tại. --config chọn hồ sơ khác. Bộ kiểm tra so 12 trường hợp cho từng biến thể 1/4/8 luồng,
gồm vận tốc bằng không, gần/cuối băng, dữ liệu cũ và thời điểm dừng không trùng
lưới. Biến thể lưới 3 ms chỉ dùng đối chiếu tính tổng quát, không ghi vào hồ sơ điều khiển.
Đối chiếu dùng hạn chức năng 5 giây để xem đủ kết quả của cả hai bản; không áp hạn
này cho máy. Yêu cầu cùng hành động, cùng số bước/kịch bản và biên lệch không quá
một phần tỷ mét. Đây là so hai cách tính cùng mô hình, không phải độ chính xác vật lý.

Sau đó đo cả bản gốc và bản mới trên ba đầu vào như đợt 02/11: mỗi trường hợp có
một lượt làm nóng, năm lượt đo, với hạn cấu hình 20 ms và hạn chức năng 1 giây
được tách riêng. Đo lần lượt trên cùng máy, chưa kiểm soát tải để chứng minh
thời gian lớn nhất. Nếu số đẹp chỉ xuất hiện khi tăng hạn thì không tính là đạt 20 ms.

report.md dễ đọc trước; optimization.json, equivalence.json, timing.csv và
benchmark.json giữ kết quả chi tiết. Lượt không đạt không bị xóa hoặc đổi nhãn.
Mã máy không thể bị ngắt tức thì giữa một nhóm; phát hiện quá hạn vẫn trả HOLD
(dừng chờ), chưa có bảo đảm thời gian thực cứng. Mô hình vẫn chỉ gồm băng/phôi,
chưa có robot và khí nén/giác hút được hiệu chuẩn.

Nguồn API: https://mujoco.readthedocs.io/en/stable/python.html#rollout . Đã đọc
API thực tế của bản MuJoCo 3.16.0 đang cài trước khi triển khai; không dựa vào
việc một bài báo dùng MuJoCo để tự suy tốc độ hoặc độ chính xác của trạm này.

Hồ sơ tùy chọn: mujoco/configs/native_physics_cell_20261103.json. Đặt prediction.native_threads theo tài nguyên máy; không tự suy máy khác có cùng tốc độ. Bộ thử dùng cùng các mô hình để so công bằng và ghi số CPU nhìn thấy trong manifest.json.
