# Network-aware predictive monitoring for production systems

**Phạm vi hiện tại: phương pháp giám sát sự kiện có xét chất lượng và độ mới
của dữ liệu.** Dây chuyền MuJoCo là một bệ kiểm thử của phương pháp; kết quả
chưa chứng minh khả năng áp dụng đã được kiểm chứng trên các máy khác.

## Đọc và chạy

1. [Bản bàn giao ngắn để tiếp tục/chat gọn](docs/TOM_TAT_DU_AN.md).
2. [Phạm vi, lý do lựa chọn và lộ trình](docs/pham_vi_bai_bao_20261106.md).
3. [Chạy gói Docker nghiên cứu đã thu gọn](docs/chay_goi_giam_sat.md).
4. [Bài báo hiện hành](paper/README.md), [PDF](reports/dt_cppps_manuscript_virtual.pdf).
5. [Nhật ký từng hạng mục](docs/nhat_ky_cong_viec.md).

## Phần triển khai chính

- `mujoco/event_window.py`: lõi so sự kiện với miền dự đoán, không biết thiết bị.
- `mujoco/eta_monitor.py`: bộ nối cảm biến quang, kiểm tra dữ liệu, dự phòng.
- `mujoco/eta_ml.py`: ML tùy chọn để so với công thức xung và bù sai lệch đơn giản.
- `research_scope.json`: 35 tệp nguồn trong runtime Docker tập trung.
- `mujoco/study_eta_monitor.py`: phép so trên bệ thử MuJoCo, giữ dữ liệu chấm ngoài lõi.

Lõi phân biệt tiến độ không khớp với dữ liệu chưa đủ để kết luận. Mất lịch sử
không được tự xem là một cảm biến hỏng hoặc một tín hiệu khỏe mạnh.

## Bằng chứng và giới hạn

ML dự báo thời điểm tốt hơn rất ít trên chín ca nhưng không báo lỗi sớm hơn bù
hằng số. 465 lượt phát lại chỉ từ 31 bản ghi; chín cặp mất cảm biến/băng đứng có
cùng quan sát. Chưa có kiểm chứng vật lý, phân loại nguyên nhân lỗi, tự phục hồi
hoặc ghi lệnh PLC từ mô đun mới. Bài báo giữ nguyên các kết quả bất lợi.

Gói tập trung tái lập 61 đoạn học và 465 quyết định cũ. Bộ thử mới có 36 bản ghi/
720 lượt so đồng hồ/tuổi; ngưỡng cũ báo nhầm 2 trong 6 ca bình thường đủ đầu vào.
Xem [kết quả và giới hạn](docs/doi_chung_thoi_gian_20261106.md). 16 kiểm tra ETA
trong Docker và 171 kiểm tra lõi kho đầy đủ trong WSL đã đạt. Kiểm tra phần mềm
không thay cho nghiệm thu của người dùng hay kiểm chứng khoa học.

## Phần giữ làm nền

Lõi DT đầy đủ, profile tham số hóa, CAD V5, mô hình MuJoCo chức năng, bộ điều
khiển toàn chu trình và các bằng chứng lịch sử vẫn được giữ để truy vết; chúng
không cùng phạm vi với gói nghiên cứu 35 tệp. CAD V5 và baseline MuJoCo chưa
đồng bộ hình học đầy đủ. Không dùng Unity hoặc Factory I/O.

Bản đã nghiệm thu vẫn là `accepted-20261103-software-v2`. Gói thu gọn
`candidate-20261106-network-clock` đang chờ người dùng kiểm tra, không tự
nâng thành accepted/stable/latest. Xem [lịch sử Docker](docker/RELEASES.md).

Mục tiêu dài hạn tự chọn cấu hình PLC vẫn được giữ, nhưng không phải tuyên bố
đã đạt của bài này. Quy tắc nhóm: [CONTRIBUTING.md](CONTRIBUTING.md).
