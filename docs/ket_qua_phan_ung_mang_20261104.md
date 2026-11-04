# Phản ứng của lõi trước dữ liệu mạng bất thường

Thời gian dưới đây là thời gian mô phỏng tính từ nhịp đầu áp dụng tình huống. Không phải độ trễ PLC hoặc thời gian xử lý trên máy thật.

| Tình huống | Lệnh giảm tốc sau mốc (ms) | Dừng chờ sau mốc (ms) | Lý do dừng |
|---|---:|---:|---|
| Bình thường | Không có | 1620.0–1620.0 | Chưa có xác nhận trục XY/đầu hút |
| Trễ 40 ms | 20.0–20.0 | 2200.0–2200.0 | Bất định vị trí gắp vượt giới hạn |
| Trễ 120 ms | 20.0–20.0 | 80.0–80.0 | Quá hạn im lặng dữ liệu |
| Mất gói 300 ms | 20.0–20.0 | 80.0–80.0 | Quá hạn im lặng dữ liệu |
| Một gói lặp | 20.0–20.0 | 2160.0–2160.0 | Chưa có xác nhận trục XY/đầu hút |
| Một gói sai phiên | 20.0–20.0 | 2160.0–2160.0 | Chưa có xác nhận trục XY/đầu hút |

Mốc của ca bình thường chỉ dùng so sánh, không có lỗi được chèn. Dừng do thiếu xác nhận XY/giác hút là giới hạn phản hồi hiện tại, không phải phát hiện lỗi mạng.

Có 3/3 cặp trễ dài/mất gói có cùng đầu vào và quyết định tới lúc dừng. Vì vậy các phiên này chưa cho phép tách hai nguyên nhân trước lúc dừng.

Gói lặp và sai phiên được ghi nhận trong timing.csv ở cột packet_rejection_after_epoch_ms. Giá trị 0 nghĩa là cùng nhịp xử lý, không phải xử lý mất 0 giây trên máy thật. Dừng là phản ứng bảo thủ trước thiếu dữ liệu. Dữ liệu trở lại không tự xóa dừng chờ. Ba lần lặp dùng cùng mô hình và lịch thử; không phải ba máy độc lập hoặc căn cứ tính độ chính xác chẩn đoán. Không thay tham số để làm kết quả đạt.

## Đối chiếu trước và sau sửa

Với trễ dài/mất gói trong bộ thử này, thời gian từ nhịp áp dụng tình huống tới HOLD
đổi từ 100 ms thành 80 ms. Tính từ gói hợp lệ cuối trước mốc, khoảng im lặng đổi
120 ms thành 100 ms. Hai cách tính dùng hai mốc khác nhau, không mâu thuẫn.
Ngưỡng cấu hình vẫn là 100 ms; bước lấy mẫu 20 ms; dung sai số học 1 ns.

Cả 18 phiên mới và 36 lần phát lại đều đạt đối chiếu logic; đối chứng cố tình ép
quá hạn tính toán vẫn bị phát hiện. Chín nhóm hồi quy đạt, gồm 141 kiểm tra lõi và
8 kiểm tra web. Hai kiểm tra đóng gói nguồn đạt. Không chỉnh profile hoặc hình học;
mã băm mô hình plant giữa các cặp trước/sau giống nhau.

Ba cặp trễ dài/mất gói đều có cùng quan sát và quyết định tới lúc dừng. Kết luận
đúng là phát hiện thiếu dữ liệu và dừng chờ; chưa khẳng định đã xác định được mạng
rớt gói, nguồn ngừng gửi hay gói đến muộn. Các nguyên nhân cảm biến/ma sát/áp suất
không được kiểm chứng bởi bộ thử mạng này.

Đây là kết quả trên đồng hồ mô phỏng, không chứng minh phản ứng 80 ms trên PLC,
khả năng thời gian thực hoặc độ chính xác chẩn đoán. Nghiên cứu mang tính hồi cứu
với các tình huống cố định; ba lần lặp không phải ba máy độc lập. Vòng điều khiển
đầy đủ vẫn cần các xác nhận phần cứng chưa có. MuJoCo và CAD V5 chưa được tuyên bố
đồng bộ hoàn toàn.

## Mở tệp kết quả

- `output/docker/time_boundary_verification_20261104/response_before_fix/`
- `output/docker/time_boundary_verification_20261104/response_after_fix/`
- `docker/evidence/candidate-20261104-time-boundary.json`

Ảnh mới: `production-twin-dt:candidate-20261104-time-boundary`; chờ người dùng
kiểm nghiệm. Bản accepted cũ được giữ nguyên. Không có ảnh được đẩy ra registry.
