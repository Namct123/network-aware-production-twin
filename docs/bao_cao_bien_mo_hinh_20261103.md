# Kết quả nghiên cứu giới hạn mô hình — 03/11/2026

## Điều mới tìm được

Mô hình 1D và MuJoCo không phải lúc nào cũng khuyên giống nhau. Lưới 144 đầu vào
giả định có 138 cặp cùng khuyến nghị, 3 cặp 1D khuyên chạy/MuJoCo khuyên dừng,
và 3 cặp ngược lại. Đây là số trường hợp trên một lưới cố định, **không phải độ
chính xác 95,8%, tỷ lệ lỗi máy hoặc xác suất an toàn**.

Kết quả này hữu ích hơn việc chỉ chạy các đầu vào ở xa cuối băng rồi thấy hai
mô hình luôn đồng ý. Nó chỉ ra vùng cần nghiên cứu kỹ trước khi cho dự báo nền
tham gia điều khiển. MuJoCo cũng chưa được hiệu chuẩn nên chưa được coi là đáp án.

## Đã thử như thế nào?

Kế hoạch được lưu trước lần chạy: 8 khoảng cách tâm phôi tới giới hạn tâm cho phép,
3 tốc độ, 2 mức tuổi dữ liệu và 3 hệ số nhân ma sát trượt; tổng 144 đầu vào.
Sai lệch ước lượng giả định 2 mm. Mỗi dự báo xét 54 kịch bản trong 0,5 s.
Đây là đánh giá một trạng thái đầu vào, không phải 144 chu trình gắp–thả.

Ba cách tính dùng cùng đầu vào:

1. 1D: công thức vận chuyển dọc băng và khoảng đi thêm khi dừng.
2. MuJoCo chỉ chấm dọc: vẫn tính tiếp xúc trong không gian, nhưng chỉ kiểm tra
   phôi có vượt giới hạn dọc băng hay không.
3. MuJoCo chấm đầy đủ: cùng động lực học với cách 2, thêm giới hạn ngang và cao.

Hai bản tiếp xúc có cùng khuyến nghị trong toàn bộ lưới này. Vì vậy, sáu bất đồng
quan sát ở đây đã tồn tại khi chỉ so cùng điều kiện dọc băng; chưa cần giải thích
bằng việc MuJoCo xét thêm ngang/cao. Điều này không chứng minh có thể bỏ các
điều kiện ngang/cao trong trường hợp khác.

Hệ số nhân ma sát chỉ tác động lên thành phần trượt của cả băng và phôi; không
đổi các thành phần xoắn/lăn. Hạn tính chức năng là 5 s để xem đủ kết quả, không
thay hạn điều khiển 20 ms. Hồ sơ máy đang dùng không bị sửa hoặc tự khớp tham số.

## Các trường hợp bất đồng ở bước 2 ms

Biên dương nghĩa là mô hình còn dư khoảng tới giới hạn; biên âm nghĩa là ít nhất
một kịch bản của mô hình vượt giới hạn. Cả hai cột biên dưới đây chỉ xét dọc băng.

| Cách giới hạn (mm) | Tốc độ (m/s) | Tuổi dữ liệu (ms) | Ma sát nhân | Biên 1D (mm) | Biên tiếp xúc dọc (mm) | Khuyến nghị 1D / tiếp xúc |
|---:|---:|---:|---:|---:|---:|---|
| 15 | 0,08 | 60 | 0,25 | −0,200 | +0,373 | Dừng / chạy |
| 15 | 0,08 | 60 | 1 | −0,200 | +0,962 | Dừng / chạy |
| 15 | 0,08 | 60 | 2 | −0,200 | +0,698 | Dừng / chạy |
| 15 | 0,24 | 0 | 0,25 | +0,600 | −7,231 | Chạy / dừng |
| 15 | 0,24 | 0 | 2 | +0,600 | −0,502 | Chạy / dừng |
| 20 | 0,24 | 0 | 0,25 | +5,600 | −2,244 | Chạy / dừng |

Đây là khác biệt giữa hai mô hình đã triển khai, không phải sai số so với máy thật.
Không suy từ một hàng rằng tăng ma sát luôn làm kết quả tốt hơn; toàn bộ đáp ứng
tiếp xúc và cách chia thời gian vẫn ảnh hưởng kết quả.

## Vì sao 1D cho ra các số này?

Với đúng bộ kịch bản và chân trời hiện tại, khoảng dư để chạy tiếp của 1D có thể
đọc thành: khoảng cách còn lại, trừ sai lệch vị trí, trừ quãng đi trong tuổi dữ
liệu/chờ phản ứng/chạy thêm một chu kỳ, rồi trừ khoảng đi thêm khi dừng giả định.

Ví dụ tốc độ 0,24 m/s, dữ liệu mới, khoảng cách còn 15 mm:

- Dùng tốc độ lớn nhất của bộ kịch bản: 0,24 + 0,02 = 0,26 m/s.
- Thời gian phản ứng lớn nhất 20 ms và cho chạy thêm 20 ms: đi thêm 10,4 mm.
- Trừ sai lệch vị trí 2 mm và khoảng đi thêm khi dừng giả định 2 mm.
- Khoảng dư: 15 − 10,4 − 2 − 2 = **0,6 mm**; 1D khuyên chạy.

Con số 2 mm đi thêm khi dừng hiện là giả định trong hồ sơ, chưa phải quãng dừng
đã đo cho mọi tốc độ và ma sát. Chính vì vậy, một công thức tính nhanh có thể
cho kết luận khác mô hình tiếp xúc khi đến sát giới hạn.

## Bước tính nhỏ hơn có làm kết luận thay đổi không?

Sau khi thấy kết quả trên, đã ghi kế hoạch kiểm tra riêng: lưới con 24 đầu vào
ở khoảng cách 15/20 mm và tốc độ 0,08/0,24 m/s, giữ các tuổi dữ liệu và ma sát.
Mỗi đầu vào chạy lại với bước vật lý 1, 2, 4 ms, giữ chu kỳ điều khiển 20 ms.
Đây là phân tích bổ sung sau khi xem kết quả, **không phải bộ xác nhận độc lập**.

| Bước vật lý | Đầu vào tính đủ | 1D chạy / tiếp xúc dừng | 1D dừng / tiếp xúc chạy |
|---:|---:|---:|---:|
| 1 ms | 24/24 | 4 | 3 |
| 2 ms | 24/24 | 3 | 3 |
| 4 ms | 24/24 | 3 | 3 |

Sáu bất đồng ban đầu vẫn tồn tại ở cả ba mức bước. Có thêm một đầu vào đổi dấu
khi thay bước: cách giới hạn 15 mm, tốc độ 0,24 m/s, dữ liệu mới và ma sát nhân 1.

| Bước vật lý | Biên tiếp xúc dọc (mm) | Khuyến nghị tiếp xúc |
|---:|---:|---|
| 1 ms | −0,140 | Dừng |
| 2 ms | +0,035 | Chạy |
| 4 ms | +0,422 | Chạy |

Do đó một biên dương rất nhỏ chưa đủ để tin rằng kết luận ổn định theo cách tính.
Thay bước cũng đổi cách lượng tử hóa thời điểm phản ứng; thử này chưa tách hai
ảnh hưởng đó và chưa chứng minh mô hình đã hội tụ. Không coi kết quả 1 ms là đáp
án vật lý đúng. Chưa thêm một ngưỡng mới chỉ để buộc các kết quả giống nhau.

## Kiểm tra phần mềm và bàn giao

- Đạt 119 kiểm tra lõi, 2 kiểm tra đóng gói, bộ tích hợp và lưới 144 đầu vào trong Docker.
- Tất cả đầu vào của lưới chính và lưới con đều tính đủ, không lỗi bất biến biên.
- Đối chiếu lần WSL và Docker trên 144 đầu vào: khuyến nghị trùng nhau; chênh lệch
  biên lớn nhất quan sát bằng 0 trong dung sai kiểm tra 10⁻⁹ m. Đây chỉ là khả năng
  tái lập giữa hai môi trường phần mềm này, không phải độ chính xác vật lý.
- Các đầu vào ban đầu vượt giới hạn vẫn được giữ. Chênh lệch biên lớn ở những
  đầu vào mất vùng hỗ trợ không được dùng để suy ra một quãng dừng bình thường.
- Docker candidate-20261103-boundary-study chờ người dùng kiểm nghiệm; các ảnh cũ giữ nguyên.

Đọc [kế hoạch/cách chạy](nghien_cuu_gioi_han_mo_hinh.md) và
[hồ sơ bằng chứng, mã ảnh, mã băm](../docker/evidence/candidate-20261103-boundary-study.json).
Các tệp gốc ở output/docker/ có từng đầu vào, cấu hình, kế hoạch và kết quả đầy đủ.

## Hướng nghiên cứu tiếp theo

Ưu tiên xây cách đánh giá độ tin cậy số học khi biên quá nhỏ, rồi khảo sát mô hình
quãng dừng phụ thuộc tốc độ và tham số chưa biết. Cần tách dữ liệu xây mô hình và
dữ liệu kiểm tra; cuối cùng phải đo máy thật. Chưa có căn cứ thay nhánh điều khiển
1D bằng MuJoCo hoặc cho kết quả nền tự cấp lệnh chạy tiếp.
