# Nghiên cứu giới hạn của dự báo 1D

## Câu hỏi

Trong các đầu vào giả định gần cuối băng, hai mô hình có cùng khuyên chạy/dừng
hay không? Nếu khác, đó có thể là do mô hình dừng dọc băng hay do MuJoCo xét thêm
ngang/cao? Đây là nghiên cứu thăm dò bằng mô phỏng, không phải đo độ chính xác máy thật.

## Kế hoạch cố định trước khi chạy

Kế hoạch model_boundary_20261103.json ghép toàn bộ các giá trị:

- Khoảng cách tâm ước lượng tới giới hạn tâm cho phép: −5, 0, 5, 10, 15, 20, 40, 80 mm.
- Tốc độ ước lượng: 0,08; 0,16; 0,24 m/s.
- Tuổi dữ liệu: 0 hoặc 60 ms.
- Hệ số nhân ma sát trượt của cả băng và phôi: 0,25; 1; 2.

Tổng 144 đầu vào. Sai lệch ước lượng chọn 2 mm như một giả định thử, chưa hiệu chuẩn.
Mỗi đầu vào chạy ba cách tính: 1D; tiếp xúc MuJoCo chỉ chấm giới hạn dọc; tiếp xúc
MuJoCo chấm cả dọc/ngang/cao. Hai bản tiếp xúc dùng cùng động lực học và chỉ khác
hàm chấm biên. Mỗi dự báo giữ bộ 54 kịch bản, chân trời 0,5 s của hồ sơ.

Kế hoạch dùng hạn chức năng 5 s để đọc kết quả đầy đủ, một luồng native. Không đổi
hạn 20 ms hoặc tham số máy trong hồ sơ điều khiển. Không gán thời gian mỗi dự báo
ở đây thành tốc độ sản xuất. Tệp kế hoạch nhập sửa được cho các đợt nghiên cứu sau;
không ghi đè đợt cũ. Mọi kết quả tính thiếu/lỗi vẫn được giữ và loại khỏi phép so.

## Cách chạy

Trong môi trường Python đã cài MuJoCo của dự án:

```text
python mujoco/study_model_boundary.py --output output/nghien_cuu_bien_moi
```

Kết quả: report.md dễ đọc; cases.csv để lọc; cases.jsonl chứa đủ ba dự báo mỗi đầu
vào; boundary.json tổng hợp; plan.json, base_config.json và manifest.json để truy nguồn.
Thư mục xuất phải chưa tồn tại. Đầu vào âm vẫn được giữ để tìm giới hạn, không được
coi là phôi đang vận hành bình thường trong miền hỗ trợ của băng.

Docker candidate có sẵn chế độ:

```powershell
./scripts/docker_dt.ps1 -Mode boundary-study
```

Đổi kế hoạch bằng -Plan với tên tệp JSON trong mujoco/experiments; đổi hồ sơ bằng
-Config với tên tệp trong mujoco/configs. Kết quả mỗi lần nằm trong thư mục riêng.

## Giới hạn diễn giải

Khác nhau chưa xác định mô hình nào đúng. MuJoCo không phải đáp án vật lý đã hiệu
chuẩn. Chỉ hiệu giữa hai biên cùng xét dọc được ghi như chênh lệch mô hình; không
lấy biên tổng hợp dọc/ngang/cao trừ biên 1D để gọi là sai số. Lưới cố định không phải
mẫu ngẫu nhiên, không cho xác suất lỗi, ý nghĩa thống kê hay độ chính xác chẩn đoán.
Chưa tự sửa hệ số dừng dựa trên kết quả này. Cần dữ liệu kiểm tra riêng và cuối cùng
phải đối chiếu với máy thật trước khi đổi vai trò điều khiển.

Tham khảo kỹ thuật nội bộ: mục Contact parameters trong tài liệu chính thức MuJoCo,
https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters (đã đọc 03/11/2026).
Đây là hướng dẫn triển khai, không thêm lại vào danh mục trích dẫn bài báo.
