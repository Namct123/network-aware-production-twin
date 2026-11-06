# Vì sao cần kiểm tra tiếp xúc trước khi học lại bộ dự báo?

## Đã tìm được gì?

Một phần sai lệch dự báo xuất phát từ điều kiện tiếp xúc của phôi trong mô hình
hiện tại. Lúc bắt đầu, phôi còn nằm một phần trên cầu nối đứng yên và một phần
trên băng đang chạy. Lấy vận tốc trung bình trong giai đoạn này để dự báo cả đoạn
sau có thể sai. Đây là kết luận về bệ thử MuJoCo, chưa phải kết luận về máy thật.

Đã thực hiện 48 bản ghi: 12 điều kiện cũ × 4 cách mô phỏng. Chỉ 6/12 điều kiện
ở mỗi cách có đủ đầu và cuối xung để đánh giá. Sáu điều kiện còn lại đã che cảm
biến khi bắt đầu; được giữ lại và báo thiếu quan sát, không âm thầm loại bỏ.
48 bản ghi không phải 48 mẫu độc lập hoặc một tập kiểm chứng mới chưa từng xem.

| Cách mô phỏng chẩn đoán | Sai số xung trung bình | Sai số sau bù hằng cũ | Nằm trong chặn lấy mẫu lý tưởng | Nằm trong miền bù hằng cũ |
|---|---:|---:|---:|---:|
| Giữ nguyên | 95,6 ms | 37,8 ms | 2/6 | 4/6 |
| Để phôi ổn định 0,4 giây trước chạy | 95,6 ms | 24,4 ms | 2/6 | 5/6 |
| Cầu nối chuyển động cùng băng, chỉ trong phép chẩn đoán | 32,2 ms | 87,1 ms | 6/6 | 0/6 |
| Vừa ổn định vừa cho cầu nối chuyển động | 28,9 ms | 108,2 ms | 6/6 | 0/6 |

Sai số là độ lệch tuyệt đối trung bình của thời điểm cạnh quang được lấy mẫu,
không phải độ chính xác định vị hoặc độ chính xác phát hiện lỗi. Các số trong
bảng đều tính trên sáu ca đủ xung của từng cách; định danh ca tương ứng giữ nguyên.

## Thay đổi nào là để nghiên cứu, thay đổi nào đã đưa vào hệ thống?

Đã thêm chương trình `mujoco/study_contact_startup.py` và kế hoạch JSON. Chương
trình lấy thông số từ profile, dựng bản sao riêng cho từng phép đối chiếu. Không
đổi hình học, profile gốc, trọng số ML, miền cảnh báo hoặc bộ điều khiển đang dùng.

Trong hai nhánh chẩn đoán, gán vận tốc bề mặt cầu nối bằng băng để tách ảnh hưởng
của bề mặt đứng yên. Đây là can thiệp nhân tạo trong bộ giải tiếp xúc, không phải
đề xuất thay cầu nối hay sửa phần cứng. Nhánh ổn định cho mô phỏng chạy tĩnh 0,4
giây rồi đặt lại gốc thời gian; giữ nguyên tư thế/vận tốc đã hình thành.

Vị trí, tư thế và lực tiếp xúc chỉ nằm trong nhật ký chấm riêng. Bộ dự báo vẫn
không được đọc chúng. Có lực tiếp xúc với cầu nối trong giai đoạn xung ở cả sáu
ca đủ dữ liệu; trường này dùng để rà mô hình, không giả làm cảm biến máy thật.
Trong nhánh cầu nối chuyển động, chênh vận tốc trung bình sau/trong xung còn
khoảng −0,03% đến +0,09%, so với +5,9% đến +7,9% ở nhánh gốc.

Dùng trường tiếp xúc và hàm đọc lực theo [tài liệu API MuJoCo](https://mujoco.readthedocs.io/en/stable/APIreference/APItypes.html)
và [hàm mj_contactForce](https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html#mj-contactforce).
Nhật ký là giá trị tại giai đoạn bộ giải được lấy mẫu, không phải đo lực trên máy.

## Ý nghĩa với lõi Digital Twin

Bộ dự báo phải phản ánh đúng giai đoạn vận hành. Học một giá trị bù có thể vô tình
học luôn ảnh hưởng của cầu nối trong mô hình, nên khi điều kiện tiếp xúc
thay đổi, giá trị bù đó không còn phù hợp. Kết quả 0/6 trong miền bù cũ ở nhánh
cầu nối chuyển động minh họa sự phụ thuộc này; không phải sáu lỗi máy thật.

Cho phôi nằm ổn định trước chạy không tự sửa được mọi sai lệch. Do đó chưa đủ
căn cứ để kết luận chỉ cần thêm một hằng số thời gian tăng tốc hoặc huấn luyện
mạng học sâu là khắc phục được vấn đề. Cũng không thể dùng phép can thiệp vào
bệ thử để tuyên bố bộ giám sát hiện tại đã được cải thiện.

## Bước tiếp theo đã thu hẹp

1. Giữ mô hình gốc làm đối chứng và giữ các ca báo nhầm. Xác định rõ giai đoạn
   đưa phôi qua cầu nối và giai đoạn phôi đã đi ổn định trên băng trong giả thiết
   của bộ dự báo; không cho mô hình đọc vị trí chấm để quyết định giai đoạn online.
2. Tạo dữ liệu hiệu chỉnh riêng có lịch sử lệnh bắt đầu, điều kiện tiếp xúc và
   chu kỳ lấy mẫu được ghi rõ. Ưu tiên mô hình ít tham số trước; chỉ thêm ML nếu
   nó mang lại lợi ích so với công thức và bù đơn giản với cùng đầu vào.
3. Khóa mô hình, điều kiện được dùng và miền sai số trước khi tạo bộ đánh giá
   chưa xem. Báo riêng số ca đủ dữ liệu, báo nhầm và thời điểm phát hiện.
4. Thêm bộ nối sự kiện xi lanh thực sự sau khi chốt mô hình/miền của nó; không
   lấy việc đổi tên một nhãn sự kiện làm bằng chứng áp dụng cho máy khác.

## Tái lập và bàn giao

Kế hoạch/mã đã được lưu Git `1d3fc5c` trước chạy. 12 bản ghi nhánh gốc tái tạo
đúng từng byte cả quan sát, lệnh và vị trí chấm của phép thử trước. Có kiểm tra
36 hash đầu vào và 192 hash đầu ra; kết quả WSL và Docker giống nhau.

Lệnh trong Docker candidate:

```powershell
wsl.exe -d Ubuntu-24.04 -u root --cd /mnt/d/Projects/network-aware-production-twin -- docker run --rm --network none --read-only -v /mnt/d/Projects/network-aware-production-twin/output/docker:/app/output production-twin-dt:candidate-20261106-contact-startup-v2 mujoco/study_contact_startup.py --source /app/output/network_clock_20261106_final --output /app/output/contact_startup_review_new
```

Cần có dữ liệu tham chiếu `network_clock_20261106_final` (tạo bởi
`study_network_clock.py`); thư mục kết quả mới phải chưa tồn tại. Đường dẫn trên
là vị trí dự án trên máy hiện tại, đổi lại nếu chuyển máy. Candidate chờ người
nghiệm thu; ảnh accepted giữ nguyên. CAD V5 và MuJoCo chưa đồng bộ hình học.

Đã sửa quy ước hash kế hoạch tham chiếu sang UTF-8/LF sau phép hậu kiểm để
chạy được từ Git trên cả Windows và Linux. Các nhánh và điều kiện không đổi;
manifest vẫn giữ hash byte thực tế. Lần kiểm tra tệp tạm trong container chỉ
đọc không đạt được giữ nhật ký; kiểm tra hiện dùng dữ liệu byte trong bộ nhớ.
176 kiểm tra lõi WSL, 21 Docker và 3 ranh giới đóng gói đạt trên bản v2 cuối.
